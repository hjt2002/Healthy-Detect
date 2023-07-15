package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.dao.TemperatureMapper;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

@Service
public class TemperatureService extends ServiceImpl<TemperatureMapper,Temperature> {

    private long timeInterval=1000;

    private String base64;
    private List<Temperature> dataArr = new ArrayList<>();

    private void getDataFromPy() throws GlobalException{
        //调用算法端，获取base64编码
        GRPCClient client = null;
        com.example.grpc.HelloReply response = null;
        try {
            client = new GRPCClient("localhost", 50001);
            String queueName = "temperature";
            response = client.greet(queueName);
            if (response==null||"null".equals(response.getType())){
                System.out.println("temperature 算法端暂时无数据--->"+response);
            }else {
                String mapStr = response.getBase64Url();
                JSONObject resObj = JSONObject.parseObject(mapStr);
                String temperatureArr = resObj.getString("temperatureArr");
                this.dataArr = JSONObject.parseArray(temperatureArr, Temperature.class);
//                data.put("temperatureArr", JSON.toJSONString(tempObj));
                this.base64 = resObj.getString("base64");
                this.save(dataArr.get(dataArr.size() - 1));
            }

        } finally {
            try {
                client.shutdown();
            } catch (Exception e) {
                throw new GlobalException(RespBeanEnum.GRPC_ERROR);
            }
        }

    }

    public HashMap<String ,String > getLatestQueue() {
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
                    try {
                        getDataFromPy();
                        Thread.sleep(timeInterval);
                    } catch (Exception e) {
                        throw new GlobalException(RespBeanEnum.GRPC_ERROR);
                    }
                }
            }
        };
        try {
            Thread thread = new Thread(runnable);
            thread.start();
        } catch (Exception e) {
            throw new GlobalException(RespBeanEnum.GRPC_ERROR);
        }

    }

    public Temperature getLatestOne() {
        LambdaQueryWrapper<Temperature> lambdaQuery = Wrappers.lambdaQuery();
        lambdaQuery.orderByDesc(Temperature::getDetectTime).last(" LIMIT 1");
        // 执行查询操作
        List<Temperature> resultList = this.list(lambdaQuery);
        if (resultList.size() == 0) {
            return null;
        }
        return resultList.get(0);
    }
}