package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.HeartRateMapper;
import com.example.healthdetect.dao.IndicatorMapper;
import com.example.healthdetect.entity.HeartRate;
import com.example.healthdetect.entity.Indicator;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

@Service
public class HeartRateService extends ServiceImpl<HeartRateMapper, HeartRate> {


    private long timeInterval=1000;

    private String base64;
    private List<HeartRate> dataArr = new ArrayList<>();

    private void getDataFromPy() {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "heart_rate";
            response = client.greet(queueName);
            if ("null".equals(response.getType())){
                System.out.println("算法端暂时无数据--->"+response);
            }else {
                String mapStr = response.getBase64Url();
                JSONObject resObj = JSONObject.parseObject(mapStr);
                String arr = resObj.getString("heartRateList");
                this.dataArr = JSONObject.parseArray(arr, HeartRate.class);
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
        HashMap<String, String> data = new HashMap<>();
        data.put("heartRateList", JSON.toJSONString(this.dataArr) );
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
        System.out.println("开始获取心率数据");

    }

}
