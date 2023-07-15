package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.BloodOxygenMapper;
import com.example.healthdetect.entity.BloodOxygen;
import com.example.healthdetect.entity.HeartRate;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

@Service
public class BloodOxygenService extends ServiceImpl<BloodOxygenMapper, BloodOxygen> {

    private long timeInterval = 1000;

    private String base64;
    private List<BloodOxygen> dataArr = new ArrayList<>();

    private void getDataFromPy() throws GlobalException {
        //调用算法端，获取base64编码
        GRPCClient client = null;
        client = new GRPCClient("localhost", 50001);

        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "oxygen";
            response = client.greet(queueName);
            if (response == null || "null".equals(response.getType())) {
                System.out.println("blood oxygen 算法端暂时无数据--->" + response);
            } else {
                String mapStr = response.getBase64Url();
                JSONObject resObj = JSONObject.parseObject(mapStr);
                String oxygenArr = resObj.getString("oxygenArr");
                this.dataArr = JSONObject.parseArray(oxygenArr, BloodOxygen.class);
                this.base64 = resObj.getString("base64");
                this.save(dataArr.get(dataArr.size() - 1));
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

    public BloodOxygen getLatestOne() {
        LambdaQueryWrapper<BloodOxygen> lambdaQuery = Wrappers.lambdaQuery();
        lambdaQuery.orderByDesc(BloodOxygen::getDetectTime).last(" LIMIT 1");
        // 执行查询操作
        List<BloodOxygen> resultList = this.list(lambdaQuery);
        if (resultList.size() == 0) {
            return null;
        }
        return resultList.get(0);
    }

    public HashMap<String, String> getLatestQueue() {
        if (this.dataArr.size() == 0) {
            HashMap<String, String> data = new HashMap<>();
            ArrayList<BloodOxygen> bloodOxygenList = new ArrayList<>();
            for (int i = 0; i < 15; i++) {
                BloodOxygen bloodOxygen = new BloodOxygen(String.valueOf((new Random().nextInt(100)) * -1), new Date().toString());
                bloodOxygenList.add(bloodOxygen);
            }
            data.put("bloodOxygenList", JSON.toJSONString(bloodOxygenList));
            data.put("base64", this.base64);
            return data;
        }
        HashMap<String, String> data = new HashMap<>();
        data.put("bloodOxygenList", JSON.toJSONString(this.dataArr));
        data.put("base64", this.base64);
        return data;
    }
}