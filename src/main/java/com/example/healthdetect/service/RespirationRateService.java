package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.BloodOxygenMapper;
import com.example.healthdetect.dao.RespirationRateMapper;
import com.example.healthdetect.entity.BloodOxygen;
import com.example.healthdetect.entity.RespirationRate;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

@Service
public class RespirationRateService extends ServiceImpl<RespirationRateMapper, RespirationRate> {

    private long timeInterval=1000;

    private String base64;
    private List<RespirationRate> dataArr = new ArrayList<>();

    private void getDataFromPy() throws GlobalException {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "respiration_rate";
            response = client.greet(queueName);
            if (response==null||"null".equals(response.getType())){
                System.out.println("respiration_rate 算法端暂时无数据--->"+response);
            }else {
                String mapStr = response.getBase64Url();
                JSONObject resObj = JSONObject.parseObject(mapStr);
                String rrList = resObj.getString("rrList");
                this.dataArr = JSONObject.parseArray(rrList, RespirationRate.class);
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

    public RespirationRate getLatestOne() {
        LambdaQueryWrapper<RespirationRate> lambdaQuery = Wrappers.lambdaQuery();
        lambdaQuery.orderByDesc(RespirationRate::getDetectTime).last(" LIMIT 1");
        // 执行查询操作
        List<RespirationRate> resultList = this.list(lambdaQuery);
        if (resultList.size() == 0) {
            return null;
        }
        return resultList.get(0);
    }

    public HashMap<String ,String > getLatestQueue() {
        if (this.dataArr.size() == 0) {
            HashMap<String, String> data = new HashMap<>();
            ArrayList<RespirationRate> rrList = new ArrayList<>();
            for (int i = 0; i < 15; i++) {
                RespirationRate respirationRate = new RespirationRate(String.valueOf((new Random().nextInt(100)) * -1), new Date().toString());
                rrList.add(respirationRate);
            }
            data.put("rrList", JSON.toJSONString(rrList));
            data.put("base64", this.base64);
            return data;
        }
        HashMap<String, String> data = new HashMap<>();
        data.put("rrList", JSON.toJSONString(this.dataArr));
        data.put("base64", this.base64);
        return data;
    }
}
