#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

path = os.path.dirname(sys.path[0])
if path not in sys.path:
    sys.path.append(path)

import queue
import time
from concurrent import futures
from datetime import datetime
from threading import Thread

import grpc

from example import helloworld_pb2, helloworld_pb2_grpc



_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# 定义全局队列
global BASE64_QUEUE_HEART_RATE
global BASE64_QUEUE_BLOOD_PRESSURE
global BASE64_QUEUE_TEMPERATURE
global BASE64_QUEUE_OX
global BASE64_QUEUE_RESPIRATION_RATE
global QUEUE_MOOD

BASE64_QUEUE_HEART_RATE = queue.Queue()
BASE64_QUEUE_BLOOD_PRESSURE = queue.Queue()
BASE64_QUEUE_TEMPERATURE = queue.Queue()
BASE64_QUEUE_OX=queue.Queue()
BASE64_QUEUE_RESPIRATION_RATE=queue.Queue()
QUEUE_MOOD=queue.Queue()

class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        # 定义返回内容 message : (request->请求参数)
        print("from client: ", request.name)
        # 根据不同的name返回不同的队列数据
        response = None
        if request.name == "heart_rate":
            # 心率服务
            if BASE64_QUEUE_HEART_RATE.qsize() != 0:
                # 队列存在str
                # 定义返回数据
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "heart rate"
                my_base64url = BASE64_QUEUE_HEART_RATE.get()
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_base64url)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")

        elif request.name == "temperature":
            # 体温服务
            if BASE64_QUEUE_TEMPERATURE.qsize() != 0:
                # 队列存在str
                # 定义返回数据
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "temperature"
                my_temperature = BASE64_QUEUE_TEMPERATURE.get()
                print('temperature in queue', my_temperature)
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_temperature)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")

        elif request.name == "oxygen":
            # 血氧服务
            if BASE64_QUEUE_OX.qsize() != 0:
                # 队列存在str
                # 定义返回数据
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "oxygen"
                my_oxygen = BASE64_QUEUE_OX.get()
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_oxygen)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")


        elif request.name == "respiration_rate":
            # 呼吸频率服务
            if BASE64_QUEUE_RESPIRATION_RATE.qsize() != 0:
                # 队列存在str
                # 定义返回数据
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "respiration"
                my_rr = BASE64_QUEUE_RESPIRATION_RATE.get()
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_rr)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")

        elif request.name == "mood":
            # 心情服务
            if QUEUE_MOOD.qsize() != 0:
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "mood"
                my_mood = QUEUE_MOOD.get()
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_mood)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")

        elif request.name == "blood_pressure":
            # 血压服务
            if BASE64_QUEUE_BLOOD_PRESSURE.qsize() != 0:
                # 队列存在str
                # 定义返回数据
                my_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                my_type = "blood pressure"
                my_base64url = BASE64_QUEUE_BLOOD_PRESSURE.get()
                response = helloworld_pb2.HelloReply(date=my_date, type=my_type, base64url=my_base64url)
                print('response', response)
            else:
                # 队列为空
                response = helloworld_pb2.HelloReply(type="null")

        print('response', response)
        return response


def serve():
    print("server start...")
    # 定义server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    # 监听端口 本机:localhost  port:8181
    server.add_insecure_port('[::]:50001')
    # 启动服务
    server.start()

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


# def temp():
#     while True:
#         time.sleep(1)
#         print(BASE64_QUEUE.qsize())


def my_main():
    from algorithm.heartRate.main import hr_main
    # BASE64_QUEUE_HEART_RATE 心率监测服务
    thread_algorithm_heart_rate = Thread(target=hr_main, args=(BASE64_QUEUE_HEART_RATE,))
    # thread_algorithm_heart_rate.start()

    from algorithm.temperature.thermal_screening import main as temperature_main
    thread_algorithm_temperature = Thread(target=temperature_main, args=(BASE64_QUEUE_TEMPERATURE,))
    # thread_algorithm_temperature.start()

    from algorithm.bloodOxygen.mainO import ox_main
    thread_algorithm_oxygen = Thread(target=ox_main, args=(BASE64_QUEUE_OX,))
    # thread_algorithm_oxygen.start()

    from algorithm.respirationRate.mainR import rr_main
    thread_algorithm_rr = Thread(target=rr_main, args=(BASE64_QUEUE_RESPIRATION_RATE,))
    # thread_algorithm_rr.start()

    from algorithm.moodJudge.moodJudge import start
    thread_algorithm_mood = Thread(target=start, args=(QUEUE_MOOD,))
    thread_algorithm_mood.start()


    # BASE64_QUEUE_BLOOD_PRESSURE 血压监测服务
    # thread_algorithm_blood_pressure = Thread(target=,args=(BASE64_QUEUE_BLOOD_PRESSURE,))
    # thread_algorithm_blood_pressure.start()

    print("algorithm start...")
    # 服务端
    thread_serve = Thread(target=serve)
    thread_serve.start()

    # 测试
    # thread_count = Thread(target=temp)
    # thread_count.start()

    thread_serve.join()


if __name__ == '__main__':
    # 启动
    my_main()
