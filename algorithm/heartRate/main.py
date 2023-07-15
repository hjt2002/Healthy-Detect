import datetime
import json
import threading
import time
import io
from collections import deque

import numpy as np
import cv2
import sys
from hrvanalysis import extract_features
import matplotlib.pyplot as plt
import base64
import os

# 控制
GRPC_MODE = True

# Webcam Parameters
realWidth = 320
realHeight = 240
videoWidth = 160
videoHeight = 120
videoChannels = 3
videoFrameRate = 15

# Color Magnification Parameters
levels = 3
alpha = 170
minFrequency = 1.0
maxFrequency = 2.0
bufferSize = 150

# Output Display Parameters
font = cv2.FONT_HERSHEY_SIMPLEX
loadingTextLocation = (20, 30)
bpmTextLocation = (videoWidth // 2 + 5, 30)
fontScale = 1
fontColor = (255, 255, 255)
lineType = 2
boxColor = (0, 255, 0)
boxWeight = 3

# Heart Rate Calculation Variables
bpmCalculationFrequency = 15
bpmBufferSize = 10
hrvBufferSize = 10  # 建议大于100，这个似乎是时间越长越准确

# 绘图/村图片相关
pic_num = 20
record_interval = 5
pic_interval = 10
record_len = int(pic_interval / record_interval)
record_num_max = 500

window_size = 15
feature_queue = deque(maxlen=window_size)


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


def pic(x, y, queue):
    plt.plot(x, y)  # 绘制图片
    plt.xlabel("time")
    plt.ylabel("BPM")
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

    pic_path = "./pic_results/"
    if not os.path.exists(pic_path):
        os.makedirs(pic_path)
    plt.savefig(pic_path + t + ".png")


def gen_pic(queue):
    x_data = []
    y_data = []

    # 从 deque 中提取数据
    data = list(feature_queue)
    if len(data) > window_size:
        data = data[0 - window_size:]

    print(data)
    for item in data:
        x_data.append(item['detectTime'])
        y_data.append(item['heartRate'])
    plt.plot(x_data, y_data)
    plt.xlabel("detect time")
    plt.ylabel("heart rate")
    # plt.legend()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    base64_png = base64.b64encode(buffer.getvalue())

    dict = {"hrList": data, "base64": str(base64_png, encoding='utf-8')}
    json_map = json.dumps(dict)
    queue.put(json_map)
    plt.close()


def send_result_to_backend(queue):
    global features
    global feature_queue
    # count += 1
    #
    # 将新数据塞入窗口，窗口有最近的5个体温，计算平均值，
    print(features)
    if features:
        cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {}
        data["heartRate"] = float(features["bpm"])
        data["detectTime"] = cur_time
        data["meanNni"] = float(features["mean_nni"])
        data["sdnn"] = float(features["sdnn"])
        data["sdsd"] = float(features["sdsd"])
        data["nni50"] = float(features["nni_50"])
        data["pnni50"] = float(features["pnni_50"])
        data["nni20"] = float(features["nni_20"])
        data["pnni20"] = float(features["pnni_20"])
        data["rmssd"] = float(features["rmssd"])
        data["medianNni"] = float(features["median_nni"])
        data["rangeNni"] = float(features["range_nni"])
        data["cvsd"] = float(features["cvsd"])
        data["cvnni"] = float(features["cvnni"])
        data["meanHr"] = float(features["mean_hr"])
        data["maxHr"] =float(features["max_hr"])
        data["minHr"] = float(features["min_hr"])
        data["stdHr"] = float(features["std_hr"])

        feature_queue.append(data)
        # print(list(data_queue))

        # if not math.isnan(new_data) :
        #     # pic
        #     gen_pic(queue)
        #     # print({temperature, tim})
        # # repeat this task after 5s
    # print(feature_queue)
    # print(len(feature_queue))

    gen_pic(queue)
    threading.Timer(1, send_result_to_backend, [queue]).run()


record_x = []
record_y = []
features = {}


def hr_main(queue=None):
    global record_x
    global record_y
    global features

    # Load Haar cascade for face detection
    p = os.path.dirname(os.getcwd())
    p = p + '\\algorithm\\heartRate\\haarcascade_frontalface.xml'
    print("获取的xml目录为：")
    print(p)
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')

    webcam = None

    # 利用rtmp拉流的，需要现在手机端推流
    # webcam = cv2.VideoCapture('rtmp://119.3.221.223:1935/stream/pupils_trace')
    webcam = cv2.VideoCapture(0)
    webcam.set(3, realWidth)
    webcam.set(4, realHeight)

    if len(sys.argv) != 2:
        originalVideoFilename = "original.mov"
        originalVideoWriter = cv2.VideoWriter()
        originalVideoWriter.open(originalVideoFilename, cv2.VideoWriter_fourcc('j', 'p', 'e', 'g'), videoFrameRate,
                                 (realWidth, realHeight), True)

    outputVideoFilename = "output.mov"
    outputVideoWriter = cv2.VideoWriter()
    outputVideoWriter.open(outputVideoFilename, cv2.VideoWriter_fourcc('j', 'p', 'e', 'g'), videoFrameRate,
                           (realWidth, realHeight), True)

    bufferIndex = 0

    # Initialize Gaussian Pyramid
    firstFrame = np.zeros((videoHeight, videoWidth, videoChannels))
    firstGauss = buildGauss(firstFrame, levels + 1)[levels]
    videoGauss = np.zeros((bufferSize, firstGauss.shape[0], firstGauss.shape[1], videoChannels))
    fourierTransformAvg = np.zeros((bufferSize))

    # Bandpass Filter for Specified Frequencies
    frequencies = (1.0 * videoFrameRate) * np.arange(bufferSize) / (1.0 * bufferSize)
    mask = (frequencies >= minFrequency) & (frequencies <= maxFrequency)

    # Heart Rate Calculation Variables
    bpmBufferIndex = 0
    bpmBuffer = np.zeros((bpmBufferSize))

    hrvBuffer = np.zeros(hrvBufferSize)  # 尝试存储RR间距
    hrvBuffer.fill(555.5555555555555)
    hrvBufferIndex = 0

    i = 0
    time0 = time.time()
    record_index = 0
    # print("time0:"+str(time0))

    threading.Timer(1, send_result_to_backend, [queue]).start()

    while True:
        ret, frame = webcam.read()
        if not ret:
            break

        if len(sys.argv) != 2:
            originalFrame = frame.copy()
            originalVideoWriter.write(originalFrame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            # Select face region as ROI
            detectionFrame = frame[y:y + h, x:x + w, :]
            detectionFrame = cv2.resize(detectionFrame,
                                        (videoWidth, videoHeight))  # Resize ROI to match video dimensions

            videoGauss[bufferIndex] = buildGauss(detectionFrame, levels + 1)[levels]

            fourierTransform = np.fft.fft(videoGauss, axis=0)
            fourierTransform[mask == False] = 0

            if bufferIndex % bpmCalculationFrequency == 0:
                i = i + 1

                for buf in range(bufferSize):
                    fourierTransformAvg[buf] = np.real(fourierTransform[buf]).mean()
                hz = frequencies[np.argmax(fourierTransformAvg)]
                bpm = 60.0 * hz
                if bpm != 0:
                    ii = 60000 / bpm
                    # print(ii)
                    hrvBuffer[hrvBufferIndex % hrvBufferSize] = int(ii)
                    hrvBufferIndex = hrvBufferIndex + 1
                    # if hrvBufferIndex == hrvBufferSize:
                    # print(hrvBuffer)
                    features = extract_features.get_time_domain_features(hrvBuffer)
                    features['bpm'] = bpm
                    # print("尝试调用hrv-analysis函数")
                    # print(features)

                    #      db.insertHRV(bpm, features)

                bpmBuffer[bpmBufferIndex] = bpm
                bpmBufferIndex = (bpmBufferIndex + 1) % bpmBufferSize

            bufferIndex = (bufferIndex + 1) % bufferSize

            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, boxWeight)

        if i > bpmBufferSize:
            bpm = bpmBuffer.mean()
            cv2.putText(frame, "BPM: %d" % bpm, bpmTextLocation, font, fontScale, fontColor, lineType)

            # pic
            # 每隔record_interval秒记录一次数据
            time1 = time.time()
            # print("time1:"+str(time1))
            if (int(time1 - time0)) % record_interval == 0:
                # print("记录数据："+str(time1))
                t = time.strftime('%H:%M:%S', time.localtime())
                record_x.append(t)
                record_y.append(bpm)
                record_index += 1
                if record_index == record_num_max:
                    record_x = record_x[:-record_len]
                    record_y = record_y[:-record_len]
                    record_index = record_len
            # 每过pic_interval秒分钟画一次图
            if (int(time1 - time0)) % pic_interval == 0:
                # print("开始绘图:"+str(time1))
                if record_index < record_len:
                    pass
                else:
                    if not GRPC_MODE:
                        # pic(record_x[:-record_len], record_y[:-record_len], queue)
                        # feature_queue.append(features)
                        # gen_pic(features,record_x[:-record_len], record_y[:-record_len], queue)
                        # else:
                        loacalPic(record_x[:-record_len], record_y[:-record_len])

        else:
            cv2.putText(frame, "Calculating BPM...", loadingTextLocation, font, fontScale, fontColor, lineType)

        outputVideoWriter.write(frame)

        if len(sys.argv) != 2:
            cv2.imshow("Webcam Heart Rate Monitor", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    webcam.release()
    cv2.destroyAllWindows()
    outputVideoWriter.release()
    if len(sys.argv) != 2:
        originalVideoWriter.release()


if __name__ == "__main__":
    hr_main()
