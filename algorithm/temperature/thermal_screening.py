import datetime
import io
import json
import os
import queue
import threading
import time
from collections import deque

import numpy as np
import cv2

base_dir = 'Computer Vision Projects/Thermal Screening Project/'
threshold = 200
area_of_box = 700  # 3000 for img input
min_temp = 102  # in fahrenheit
font_scale_caution = 1  # 2 for img input
font_scale_temp = 0.7  # 1 for img input

temperature = -1000
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface.xml')

window_size = 15
data_queue = deque(maxlen=window_size)


def convert_to_temperature(pixel_avg):
    """
    Converts pixel value (mean) to temperature (fahrenheit) depending upon the camera hardware
    """
    return pixel_avg / 1.040723 - 74
    # return pixel_avg - 74


def process_frame(frame):
    global temperature
    global faceCascade
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    heatmap_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    heatmap = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_HOT)  # Apply color map (hot) to the grayscale image

    # Binary threshold
    _, binary_thresh = cv2.threshold(heatmap_gray, threshold, 255, cv2.THRESH_BINARY)

    # Image opening: Erosion followed by dilation 先腐蚀再膨胀
    kernel = np.ones((3, 3), np.uint8)
    image_erosion = cv2.erode(binary_thresh, kernel, iterations=1)  # Erosion operation
    image_opening = cv2.dilate(image_erosion, kernel, iterations=1)  # Dilation operation

    frame, faces = detect_face(frame)
    # Get contours from the image obtained by opening operation
    # contours, _ = cv2.findContours(image_opening, 1, 2)

    image_with_rectangles = np.copy(heatmap)

    for x, y, w, h in faces:
        # rectangle over each contour
        # x, y, w, h = cv2.boundingRect(contour)

        # Pass if the area of rectangle is not large enough
        if (w) * (h) < area_of_box:
            continue

        # Mask is boolean type of matrix.
        mask = np.zeros_like(heatmap_gray)
        # cv2.drawContours(mask, contour, -1, 255, -1)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        # 只计算 块内部而不是整个矩形的像素均值
        # print("mean", cv2.mean(heatmap_gray, mask=mask)[0])
        mean = convert_to_temperature(cv2.mean(heatmap_gray, mask=mask)[0])

        # Colors for rectangles and textmin_area
        temperature = round(mean, 2)

        color = (0, 255, 0) if temperature < min_temp else (
            255, 255, 127)

        # 如果满足以下条件，则回调函数
        if temperature >= min_temp:
            # 在此处执行回调函数
            cv2.putText(image_with_rectangles, "High temperature detected !!!", (35, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale_caution, color, 2, cv2.LINE_AA)

        # 绘制矩形以可视化
        image_with_rectangles = cv2.rectangle(
            image_with_rectangles, (x, y), (x + w, y + h), color, 2)

        # 为每个矩形写入温度
        cv2.putText(image_with_rectangles, "{} F".format(temperature), (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale_temp, color, 2, cv2.LINE_AA)

    return image_with_rectangles


def detect_face(frame):
    global faceCascade
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Detect faces
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        # Select face region as ROI
        detectionFrame = frame[y:y + h, x:x + w, :]
        detectionFrame = cv2.resize(detectionFrame,
                                    (frame.shape[0], frame.shape[1]))  # Resize ROI to match video dimensions
        boxColor = (0, 255, 0)
        boxWeight = 3
        cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, boxWeight)

    return frame, faces


from pyecharts.charts import Line
from pyecharts import options as opts
import base64


def convert_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_data


import matplotlib.pyplot as plt


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
        y_data.append(item['temperature'])
    plt.plot(x_data, y_data)
    plt.xlabel("detectTime")
    plt.ylabel("temperature")
    # plt.legend()

    # 申请缓冲地址
    buffer = io.BytesIO()  # using buffer,great way!
    # 把plt的内容保存在内存中
    plt.savefig(buffer, format='png')
    base64_png = base64.b64encode(buffer.getvalue())

    dict = {"temperatureArr": data, "base64": str(base64_png, encoding='utf-8')}
    json_map = json.dumps(dict)
    queue.put(json_map)
    plt.close()


def send_result_to_backend(queue):
    # count += 1
    #
    new_data = temperature
    cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_queue.append({"temperature": temperature, "detectTime": cur_time})
    print(list(data_queue))

    if temperature > 0 :
        # pic
        gen_pic(queue)
        # print({temperature, tim})
    # repeat this task after 5s

    threading.Timer(1, send_result_to_backend, [queue]).run()


def main(queue):
    """
    Main driver function
    """

    url = "http://192.168.43.1:8081/video"
    video = cv2.VideoCapture(url)
    ## For Video Input
    # video = cv2.VideoCapture(str(base_dir+'video_input.mp4'))
    video_frames = []

    height = 0
    width = 0

    threading.Timer(1, send_result_to_backend, [queue]).start()

    while True:
        ret, frame = video.read()

        if not ret:
            break

        # Process each frame
        # 此处得到的 temperature 需要定时写入数据库 并发送给前端
        frame = process_frame(frame)
        height, width, _ = frame.shape
        video_frames.append(frame)

        # Show the video as it is being processed in a window
        cv2.imshow('frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

    # Save video to output
    size = (height, width)
    out = cv2.VideoWriter(str(base_dir + 'output.avi'), cv2.VideoWriter_fourcc(*'MJPG'), 100, size)

    for i in range(len(video_frames)):
        out.write(video_frames[i])
    out.release()

    # img = cv2.imread(str(base_dir + 'input_image.jpg'))
    #
    # # Process the image
    # processed_img = process_frame(img)
    # height, width, _ = processed_img.shape
    # dim = (int(width * 0.5),int(height * 0.5))
    #
    # resized_img = cv2.resize(processed_img, dim, interpolation=cv2.INTER_AREA)
    # cv2.imwrite(str(base_dir + 'output_image.jpg'), resized_img)
    #
    # saved_img = cv2.imread(str(base_dir + 'output_image.jpg'))
    # cv2.imshow('output', saved_img)
    #
    # cv2.waitKey(0)


if __name__ == "__main__":
    main(queue.Queue())
