import datetime
import json
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



GRPC_MODE = False
inter = 100
# 画图变量
oxBufferSize = 20
oxBufferIndex = 0
oxBuffer = np.zeros((oxBufferSize))

# 绘图/村图片相关
pic_num = 20
record_interval = 5
pic_interval = 10
record_len = int(pic_interval / record_interval)
record_num_max = 500


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

ox_level=-1000
window_size = 15
data_queue = deque(maxlen=window_size)
def gen_pic(queue):
    x_data = []
    y_data = []

    # 从 deque 中提取数据
    data = list(data_queue)
    if len(data) > window_size:
        data = data[0 - window_size:]

    # print(data)
    for item in data:
        x_data.append(item['detectTime'])
        y_data.append(item['oxLevel'])
    plt.plot(x_data, y_data)
    plt.xlabel("detect_time")
    plt.ylabel("blood_oxygen_level")
    # plt.legend()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    base64_png = base64.b64encode(buffer.getvalue())


    dict = {"dataList": data, "base64": str(base64_png, encoding='utf-8')}
    json_map = json.dumps(dict)
    queue.put(json_map)
    plt.close()


def send_result_to_backend(queue):
    # count += 1
    #
    # 将新数据塞入窗口，窗口有最近的5个体温，计算平均值，发送给springboot
    new_data = ox_level

    if ox_level > 0:
        cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 要传到 springboot，key名要和 那边的实体属性 同名
        data_queue.append({"oxLevel": new_data, "detectTime": cur_time})
        print(list(data_queue))
        gen_pic(queue)
        # print({temperature, tim})
    # repeat this task after 5s

    threading.Timer(1, send_result_to_backend, [queue]).run()

def ox_main(queue):
    # 测试可以用本机，更方便
    url = "http://192.168.43.1:8081/video"
    webcam = cv2.VideoCapture(url)
    # webcam = cv2.VideoCapture('rtmp://119.3.221.223:1935/stream/pupils_trace')
    # p = os.path.dirname(os.getcwd())
    # p = p + '/algorithm/bloodOxygen/haarcascade_frontalface.xml'
    # print("获取的xml目录为：")
    # print(p)
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')
    realWidth = 320
    realHeight = 240
    videoWidth = 160
    videoHeight = 120
    videoChannels = 3
    videoFrameRate = 15
    count = 0
    A = 100
    B = 5
    bo = 0.0

    # Output Display Parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    loadingTextLocation = (20, 30)
    bpmTextLocation = (videoWidth // 2 + 5, 30)
    fontScale = 1
    fontColor = (255, 255, 255)
    lineType = 2
    boxColor = (0, 255, 0)
    boxWeight = 3
    webcam.set(3, realWidth)
    webcam.set(4, realHeight)

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
    spcount = 0
    spresult = 0
    result = 0
    i = 0

    time0 = time.time()
    record_x = []
    record_y = []
    record_index = 0

    threading.Timer(1, send_result_to_backend, [queue]).start()
    while (True):
        ret, frame = webcam.read()
        # print(frame)
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

        # Red channel operations
        red_channel = frame[:, :, 2]
        mean_red = np.mean(red_channel)
        std_red = np.std(red_channel)
        red_final = std_red / mean_red

        # Blue channel operations
        blue_channel = frame[:, :, 0]
        mean_blue = np.mean(blue_channel)
        std_blue = np.std(red_channel)
        blue_final = std_blue / mean_blue

        sp = A - (B * (red_final / blue_final))
        sp = round(sp, 2)
        spresult = spresult + sp + 3  # (correction factor)
        spcount += 1

        spmean = float(spresult) / float(spcount)
        if len(faces) != 0:
            i = i + 1
            # if i % inter == 0:
            #     db.insertOx(round(spmean, 3))
            #     print('insert dataBase!!')
            # print(spmean)
            cv2.putText(frame, "SpO2: %.3f" % spmean, bpmTextLocation, font, fontScale, fontColor, lineType)
            global ox_level
            ox_level=spmean

        # time1 = time.time()
        # # print("time1:"+str(time1))
        # if (int(time1 - time0)) % record_interval == 0:
        #     # print("记录数据："+str(time1))
        #     t = time.strftime('%H:%M:%S', time.localtime())
        #     record_x.append(t)
        #     record_y.append(round(spmean,3))
        #     record_index += 1
        #     if record_index == record_num_max:
        #         record_x = record_x[:-record_len]
        #         record_y = record_y[:-record_len]
        #         record_index = record_len
        # # 每过pic_interval秒分钟画一次图
        # if (int(time1 - time0)) % pic_interval == 0:
        #     # print("开始绘图:"+str(time1))
        #     if record_index < record_len:
        #         pass
        #     else:
        #         if GRPC_MODE:
        #             pic(record_x[:-record_len], record_y[:-record_len], queue)
        #         else:
        #             loacalPic(record_x[:-record_len], record_y[:-record_len])

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

    res = 1
    result = result + res
    # print(sp)
    length = len(frame[1:])
    print("length" + str(length))
    # result = result/length
    result = spresult / spcount
    print("final res value: " + str(result))

    if result > 0.25:
        spresult = spresult / spcount
        spresult = round(spresult, 2)
    else:
        spresult = "Finger not recognised"


if __name__ == "__main__":
    ox_main()
