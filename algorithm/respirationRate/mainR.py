"""
呼吸频率检测
respiration
"""
import datetime
import json
import math
import queue
import threading
from collections import deque

import numpy as np
import cv2
import sys
import matplotlib.pyplot as plt
import os
import base64
import io
import time

realWidth = 320
realHeight = 240
videoWidth = 160
videoHeight = 120
videoChannels = 3
videoFrameRate = 15

GRPC_MODE = False
inter = 100
# 画图变量
rrBufferSize = 20
rrBufferIndex = 0
rrBuffer = np.zeros((rrBufferSize))

# 绘图/村图片相关
pic_num = 20
record_interval = 5
pic_interval = 10
record_len = int(pic_interval / record_interval)
record_num_max = 500

rr=-100
temp_arr=[] # 用于计算1s内的平均值
window_size = 15
data_queue = deque(maxlen=window_size)


def pic(x, y, queue):
    plt.plot(x, y)  # 绘制图片
    plt.xlabel("time")
    plt.ylabel("SpO2")
    plt.show()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    # 或者直接读取二进制，转换base64
    base64_png = base64.b64encode(buffer.getvalue())
    queue.put(base64_png)


def loacalPic(x, y):
    plt.plot(x, y)  # 绘制图片
    plt.xlabel("time")
    plt.ylabel("BPM")
    t = time.strftime('%Y-%m-%d %H_%M_%S', time.localtime())
    plt.show()

    pic_path = "./pic_results/"
    if not os.path.exists(pic_path):
        os.makedirs(pic_path)
    plt.savefig(pic_path + t + ".png")


# Helper Methods
def buildGauss(frame, levels):
    pyramid = [frame]
    for level in range(levels):
        frame = cv2.pyrDown(frame)
        pyramid.append(frame)
    return pyramid


def reconstructFrame(pyramid, index, levels):
    filteredFrame = pyramid[index]
    for level in range(levels):
        filteredFrame = cv2.pyrUp(filteredFrame)
    filteredFrame = filteredFrame[:videoHeight, :videoWidth]
    return filteredFrame


def applyFFT(frames, fps):
    n = frames.shape[0]
    t = np.linspace(0, float(n) / fps, n)
    disp = frames.mean(axis=0)
    y = frames - disp

    k = np.arange(n)
    T = n / fps
    frq = k / T  # two sides frequency range
    freqs = frq[range(n // 2)]  # one side frequency range

    Y = np.fft.fft(y, axis=0) / n  # fft computing and normalization
    signals = Y[range(n // 2), :, :]

    return freqs, signals


def bandPass(freqs, signals, freqRange):
    signals[freqs < freqRange[0]] *= 0
    signals[freqs > freqRange[1]] *= 0

    return signals


def find(condition):
    res, = np.nonzero(np.ravel(condition))
    return res


def freq_from_crossings(sig, fs):
    """Estimate frequency by counting zero crossings

    """
    # print(sig)
    # Find all indices right before a rising-edge zero crossing
    indices = find((sig[1:] >= 0) & (sig[:-1] < 0))
    x = sig[1:]
    x = np.mean(x)

    return x


# from PIL import Image
# from io import BytesIO
# import base64
#
# def pil_image_to_base64(pil_image):
#    buf = BytesIO()
#    pil_image.save(buf, format="JPEG")
#    return base64.b64encode(buf.getvalue())
#
# def base64_to_pil_image(base64_img):
#    return Image.open(BytesIO(base64.b64decode(base64_img)))

def searchFreq(freqs, signals, frames, fs):
    curMax = 0
    freMax = 0
    Mi = 0
    Mj = 0
    for i in range(10, signals.shape[1]):
        for j in range(signals.shape[2]):

            idxMax = abs(signals[:, i, j])
            idxMax = np.argmax(idxMax)
            freqMax = freqs[idxMax]
            ampMax = signals[idxMax, i, j]
            c, a = abs(curMax), abs(ampMax)
            if (c < a).any():
                curMax = ampMax
                freMax = freqMax
                Mi = i
                Mj = j
    # print "(%d,%d) -> Freq:%f Amp:%f"%(i,j,freqMax*60, abs(ampMax))
    y = frames[:, Mi, Mj]
    y = y - y.mean()
    fq = freq_from_crossings(y, fs)
    rate_fft = freMax * 60

    rate_count = round(20 + (fq * 10))

    if np.isnan(rate_count):
        rate = rate_fft
    elif abs(rate_fft - rate_count) > 20:
        rate = rate_fft
    else:
        rate = rate_count

    return rate

def gen_pic(queue):
    x_data = []
    y_data = []

    # 从 deque 中提取数据
    data = list(data_queue)
    if len(data) > window_size:
        data = data[0 - window_size:]

    print(data)
    for item in data:
        x_data.append(item['detectTime'])
        y_data.append(item['rate'])
    plt.plot(x_data, y_data)
    plt.xlabel("detect time")
    plt.ylabel("respiration rate")
    # plt.legend()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    base64_png = base64.b64encode(buffer.getvalue())


    dict = {"rrList": data, "base64": str(base64_png, encoding='utf-8')}
    json_map = json.dumps(dict)
    queue.put(json_map)
    plt.close()


def send_result_to_backend(queue):
    global temp_arr
    # count += 1
    #
    # 将新数据塞入窗口，窗口有最近的5个体温，计算平均值，发送给springboot
    if len(temp_arr)>0:
        new_data = np.mean(temp_arr)
        temp_arr=[]
        cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_queue.append({"rate": new_data, "detectTime": cur_time})
        # print(list(data_queue))

        if not math.isnan(new_data) :
            # pic
            gen_pic(queue)
            # print({temperature, tim})
        # repeat this task after 5s

    threading.Timer(1, send_result_to_backend, [queue]).run()


def rr_main(queue):
    global rr
    global temp_arr
    # Webcam Parameters
    # if len(sys.argv) == 2:
    #     webcam = cv2.VideoCapture(sys.argv[1])
    # else:
    #     webcam = cv2.VideoCapture(0)
    # webcam.set(3, realWidth)
    # webcam.set(4, realHeight)

    # 利用rtmp拉流的，需要现在手机端推流
    # webcam = cv2.VideoCapture('rtmp://119.3.221.223:1935/stream/pupils_trace')

    webcam = cv2.VideoCapture(0)
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')

    # Output Videos
    if len(sys.argv) != 2:
        originalVideoFilename = "original.mov"
        originalVideoWriter = cv2.VideoWriter()
        originalVideoWriter.open(originalVideoFilename, cv2.VideoWriter_fourcc('j', 'p', 'e', 'g'), videoFrameRate,
                                 (realWidth, realHeight), True)

    outputVideoFilename = "output.mov"
    outputVideoWriter = cv2.VideoWriter()
    outputVideoWriter.open(outputVideoFilename, cv2.VideoWriter_fourcc('j', 'p', 'e', 'g'), videoFrameRate,
                           (realWidth, realHeight), True)

    # Color Magnification Parameters
    levels = 3
    alpha = 170
    minFrequency = 1.0
    maxFrequency = 2.0
    bufferSize = 150
    bufferIndex = 0

    # Output Display Parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    loadingTextLocation = (20, 30)
    bpmTextLocation = (videoWidth // 2 + 5, 30)
    fontScale = 1
    fontColor = (255, 255, 255)
    lineType = 2
    boxColor = (0, 255, 0)
    boxWeight = 3

    # Initial Gaussian Pyramid
    sampleLen = 10
    firstFrame = np.zeros((videoHeight, videoWidth, videoChannels))
    firstGauss = buildGauss(firstFrame, levels + 1)[levels]
    sample = np.zeros((sampleLen, firstGauss.shape[0], firstGauss.shape[1], videoChannels))

    idx = 0

    respRate = []

    # pipeline = PipeLine(videoFrameRate)
    # face_flag = 0
    # for i in range(len(videoStrings)):
    # input_img = base64_to_pil_image(videoStrings[i])

    # input_img = input_img.resize((320, 240))
    # gray = cv2.cvtColor(np.array(input_img), cv2.COLOR_BGR2GRAY)

    # faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    # print(faces)
    # faces = [1,2,3]
    # print(len(faces))
    # if len(faces) > 0:
    # print("FACE FOUND _ RR")

    # face_flag = 1

    # frame = cv2.cvtColor(np.array(input_img), cv2.COLOR_BGR2RGB)
    i = 0
    time0 = time.time()
    record_x = []
    record_y = []
    record_index = 0

    threading.Timer(1, send_result_to_backend, [queue]).start()
    temp_arr=[]
    while (True):
        ret, frame = webcam.read()
        if ret == False:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Detect faces
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        # Select face region as ROI
        for (x, y, w, h) in faces:
            # Select face region as ROI
            detectionFrame = frame[y:y + h, x:x + w, :]
            detectionFrame = cv2.resize(detectionFrame,
                                        (videoWidth, videoHeight))  #
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, boxWeight)

        if len(sys.argv) != 2:
            originalFrame = frame.copy()
            originalVideoWriter.write(originalFrame)

        # detectionFrame = frame[videoHeight//2:realHeight-videoHeight//2, videoWidth//2:realWidth-videoWidth//2, :]

        detectionFrame = frame[int(videoHeight / 2):int(realHeight - videoHeight / 2),
                         int(videoWidth / 2):int(realWidth - int(videoWidth / 2)), :]

        sample[idx] = buildGauss(detectionFrame, levels + 1)[levels]

        freqs, signals = applyFFT(sample, videoFrameRate)
        signals = bandPass(freqs, signals, (0.2, 0.8))
        respiratoryRate = searchFreq(freqs, signals, sample, videoFrameRate)

        # frame[int(videoHeight/2):int(realHeight-videoHeight/2), int(videoWidth/2):(realWidth-int(videoWidth/2)), :] = outputFrame

        idx = (idx + 1) % 10

        respRate.append(respiratoryRate)

        # else:
        # print("Face not found")

        # if face_flag == 1:
        l = []
        a = max(respRate)
        b = np.mean(respRate)
        if b < 0:
            b = 5
        l.append(a)
        l.append(b)

        rr = np.mean(l)
        rr = round(rr, 2)
        # else:
        #   rr = "Face not recognised!"

        # print(rr)
        '''
        if bufferIndex % bpmCalculationFrequency == 0:
            i = i + 1
            for buf in range(bufferSize):
                fourierTransformAvg[buf] = np.real(fourierTransform[buf]).mean()
            hz = frequencies[np.argmax(fourierTransformAvg)]
            bpm = 60.0 * hz
            bpmBuffer[bpmBufferIndex] = bpm
            bpmBufferIndex = (bpmBufferIndex + 1) % bpmBufferSize
        '''
        # Amplify
        # filtered = np.real(np.fft.ifft(fourierTransform, axis=0))
        # filtered = filtered * alpha

        # Reconstruct Resulting Frame
        # filteredFrame = reconstructFrame(filtered, bufferIndex, levels)
        # outputFrame = detectionFrame + filteredFrame
        # outputFrame = cv2.convertScaleAbs(outputFrame)

        # bufferIndex = (bufferIndex + 1) % bufferSize
        if len(faces) != 0:
            i = i + 1
            # if i % inter == 0:
            #     db.insertRR(round(rr, 1))
            #     print('insert dataBase!!')
        cv2.putText(frame, "Respiration: %.1f" % rr, bpmTextLocation, font, fontScale, fontColor, lineType)
        temp_arr.append(rr)
        print("temp_arr ---->", temp_arr)


        # 使用 send_result_to_backend 替代 *********************************
        # if (int(time1 - time0)) % record_interval == 0:
        #     # print("记录数据："+str(time1))
        #     t = time.strftime('%H:%M:%S', time.localtime())
        #     record_x.append(t)
        #     record_y.append(round(rr, 1))
        #     record_index += 1
        #     if record_index == record_num_max:
        #         record_x = record_x[:-record_len]
        #         record_y = record_y[:-record_len]
        #         record_index = record_len

        # 每过pic_interval秒分钟画一次图
        # if (int(time1 - time0)) % pic_interval == 0:
        #     # print("开始绘图:"+str(time1))
        #     if record_index < record_len:
        #         pass
        #     else:
        #         if GRPC_MODE:
        #             pic(record_x[:-record_len], record_y[:-record_len], queue)
        #         else:
        #             loacalPic(record_x[:-record_len], record_y[:-record_len])

        cv2.imshow("Webcam Respiration Rate Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()
    outputVideoWriter.release()
    if len(sys.argv) != 2:
        originalVideoWriter.release()


if __name__ == "__main__":
    rr_main()
