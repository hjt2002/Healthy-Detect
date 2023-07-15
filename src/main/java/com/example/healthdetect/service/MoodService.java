package com.example.healthdetect.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.dao.MoodMapper;
import com.example.healthdetect.entity.Mood;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

@Service
public class MoodService extends ServiceImpl<MoodMapper, Mood> {

    private long timeInterval=1000;

    private String base64;
    private Mood mood ;

    private void getDataFromPy() throws GlobalException{
        //调用算法端，获取base64编码
        GRPCClient client = null;
        com.example.grpc.HelloReply response = null;
        System.out.println("GET IN HERE");
        try {
            client = new GRPCClient("localhost", 50001);
            String queueName = "mood";
            response = client.greet(queueName);
            if (response==null||"null".equals(response.getType())){
                System.out.println("mood 算法端暂时无数据--->"+response);
            }else {
                String mapStr = response.getBase64Url();
                this.mood = JSONObject.parseObject(mapStr, Mood.class);
                this.save(this.mood);
//                data.put("temperatureArr", JSON.toJSONString(tempObj));
            }

        } finally {
            try {
                client.shutdown();
            } catch (Exception e) {
                throw new GlobalException(RespBeanEnum.GRPC_ERROR);
            }
        }

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

    public Mood getLatestOne() {
        LambdaQueryWrapper<Mood> lambdaQuery = Wrappers.lambdaQuery();
        lambdaQuery.orderByDesc(Mood::getEndTime).last(" LIMIT 1");
        // 执行查询操作
        List<Mood> resultList = this.list(lambdaQuery);
        if (resultList.size() == 0) {
            return null;
        }
        return resultList.get(0);
    }
}
