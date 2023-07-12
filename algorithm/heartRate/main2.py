# 添加了人脸跟踪
import base64
import time
import io

import numpy as np
import cv2
import sys
import matplotlib.pyplot as plt
import datetime

from utils.imagesBase64Encode import imageToBase64

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
    tim = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    plt.plot(x, y)
    plt.xlabel("time")
    plt.ylabel("BPM")
    # plt.legend()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    # 或者直接读取二进制，转换base64
    base64_png = base64.b64encode(buffer.getvalue())
    queue.put(base64_png)
    # plt.savefig("pic-results/" + tim + ".png")


def main(queue):
    # Load Haar cascade for face detection
    faceCascade = cv2.CascadeClassifier('E:\\workspace\\pythonworkspace\\pythonProject\\algorithm\\heartRate\\haarcascade_frontalface.xml')
    # faceCascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')
    # Webcam Parameters
    webcam = None
    if len(sys.argv) == 2:
        webcam = cv2.VideoCapture(sys.argv[1])
    else:
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


    # Initialize Gaussian Pyramid
    bufferIndex = 0
    firstFrame = np.zeros((videoHeight, videoWidth, videoChannels))
    firstGauss = buildGauss(firstFrame, levels + 1)[levels]
    videoGauss = np.zeros((bufferSize, firstGauss.shape[0], firstGauss.shape[1], videoChannels))
    fourierTransformAvg = np.zeros((bufferSize))

    # Bandpass Filter for Specified Frequencies
    frequencies = (1.0 * videoFrameRate) * np.arange(bufferSize) / (1.0 * bufferSize)
    mask = (frequencies >= minFrequency) & (frequencies <= maxFrequency)

    # Heart Rate Calculation Variables
    bpmCalculationFrequency = 15
    bpmBufferIndex = 0
    bpmBufferSize = 10
    bpmBuffer = np.zeros((bpmBufferSize))

    # pic
    pic_num = 10
    pic_list_len = 20
    bpm_x_list = []
    bpm_y_list = []
    bpm_index = 0
    t0 = time.time()

    i = 0
    while (True):
        ret, frame = webcam.read()
        if ret == False:
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
                bpmBuffer[bpmBufferIndex] = bpm
                bpmBufferIndex = (bpmBufferIndex + 1) % bpmBufferSize

            filtered = np.real(np.fft.ifft(fourierTransform, axis=0))
            filtered = filtered * alpha

            filteredFrame = reconstructFrame(filtered, bufferIndex, levels)
            outputFrame = detectionFrame + filteredFrame
            outputFrame = cv2.convertScaleAbs(outputFrame)

            bufferIndex = (bufferIndex + 1) % bufferSize

            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, boxWeight)

        if i > bpmBufferSize:
            bpm = bpmBuffer.mean()
            cv2.putText(frame, "BPM: %d" % bpm, bpmTextLocation, font, fontScale, fontColor, lineType)
            # pic
            tim = datetime.datetime.now().strftime('%H:%M:%S')
            bpm_x_list.append(tim)
            bpm_y_list.append(bpm)
            bpm_index += 1

            # pic
            if pic_num > 0:
                t1 = time.time()
                t = int(t1-t0)
                # 每间隔两秒绘制一次图像
                if t % 2 == 0:
                    if bpm_index < pic_list_len:
                        pass
                    else:
                        x = bpm_x_list[:-pic_list_len]
                        y = bpm_y_list[:-pic_list_len]
                        # 传入主线程定义的队列
                        pic(x, y, queue)
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


# if __name__ == "__main__":
#     main()
