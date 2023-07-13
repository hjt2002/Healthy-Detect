package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.IndicatorMapper;
import com.example.healthdetect.dao.TemperatureMapper;
import com.example.healthdetect.entity.Indicator;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

@Service
public class TemperatureService extends ServiceImpl<TemperatureMapper,Temperature> {

    private long timeInterval=1000;

    private String base64;
    private List<Temperature> dataArr = new ArrayList<>();

    private void getDataFromPy() {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "temperature";
            response = client.greet(queueName);
            if (response==null||"null".equals(response.getType())){
                System.out.println("算法端暂时无数据--->"+response);
            }else {
                String mapStr = response.getBase64Url();
                JSONObject resObj = JSONObject.parseObject(mapStr);
                String temperatureArr = resObj.getString("temperatureArr");
                this.dataArr = JSONObject.parseArray(temperatureArr, Temperature.class);
//                data.put("temperatureArr", JSON.toJSONString(tempObj));
                this.base64 = resObj.getString("base64");
            }

        } finally {
            try {
                client.shutdown();
            } catch (InterruptedException e) {
                System.out.println(e.getLocalizedMessage());
                throw new RuntimeException(e);
            }
        }

    }

    public HashMap<String ,String > getLatest() {
        if (this.dataArr.size() == 0) {
            HashMap<String, String> data = new HashMap<>();
            ArrayList<Temperature> temperatures = new ArrayList<>();
            for (int i = 0; i < 15; i++) {
                Temperature temperature = new Temperature(String.valueOf((new Random().nextInt(100))*-1), new Date().toString());
                temperatures.add(temperature);
            }
            data.put("temperatureList", JSON.toJSONString(temperatures) );
            data.put("base64", this.base64);
            return data;
        }
        HashMap<String, String> data = new HashMap<>();
        data.put("temperatureList", JSON.toJSONString(this.dataArr) );
        data.put("base64", this.base64);
        return data;
    }

    @PostConstruct
    private void startPullingDataFromAlgorithm() {
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                while (true) {
                    getDataFromPy();
                    try {
                        Thread.sleep(timeInterval);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
        };
        Thread thread = new Thread(runnable);
        thread.start();

    }

}
