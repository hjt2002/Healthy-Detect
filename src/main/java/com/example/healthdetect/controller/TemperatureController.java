package com.example.healthdetect.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.Indicator;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import com.example.healthdetect.service.ExamineService;
import com.example.healthdetect.service.TemperatureService;
import org.apache.tomcat.util.http.fileupload.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@RestController
@RequestMapping("/temperature")
public class TemperatureController {

    @Autowired
    private TemperatureService temperatureService;

    @PostMapping("/test")
    @ResponseBody
    public RespBean test(@RequestBody Temperature temperature) {
        System.out.println("test");
        return RespBean.success();
    }


    @PostMapping("/insert")
    @ResponseBody
    public RespBean insert(@RequestBody Temperature temperature) {
        boolean save = temperatureService.save(temperature);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    @ResponseBody
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<Temperature> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(Temperature::getDetectTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(Temperature::getDetectTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<Temperature> resultList = temperatureService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    @GetMapping("/arr")
    public RespBean getTemperatureArr() {
//        //调用算法端，获取base64编码
//        GRPCClient client = new GRPCClient("localhost", 50001);
//        com.example.grpc.HelloReply response = null;
//        try {
//            String queueName = "temperature";
//            response = client.greet(queueName);
//
//        } finally {
//            try {
//                client.shutdown();
//            } catch (InterruptedException e) {
//                throw new RuntimeException(e);
//            }
//        }
//        String temperature = response.getBase64Url();
        System.out.println("get temperature");
        String temperature = String.valueOf(new Random().nextInt(40));
        Temperature obj = new Temperature(temperature, new Date().toString());
        return RespBean.success(obj);
    }

    @GetMapping("/new_one")
    public RespBean getLatestData() {
        return RespBean.success(temperatureService.getLatest());
    }

    @GetMapping("/base64")
    public RespBean getGraphBase64() {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "temperature";
            response = client.greet(queueName);

        } finally {
            try {
                client.shutdown();
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }
        String mapStr = response.getBase64Url();
        JSONObject resObj = JSONObject.parseObject(mapStr);
        Temperature tempObj = new Temperature(resObj.getString("temperature"), resObj.getString("time"));
        temperatureService.save(tempObj);
        HashMap<String, String> data = new HashMap<>();
        data.put("temperatureObj", JSON.toJSONString(tempObj));
        data.put("base64", resObj.getString("base64"));
        return RespBean.success(data);
    }

    @GetMapping("/graph")
    public void getGraph(HttpServletResponse resp)  {
        //调用算法端，获取base64编码
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        com.example.grpc.HelloReply response = null;
        try {
            String queueName = "temperature";
            response = client.greet(queueName);

        } finally {
            try {
                client.shutdown();
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }
        String base64 = response.getBase64Url();
        try {
            // 去掉base64前缀 data:image/jpeg;base64,
            base64 = base64.substring(base64.indexOf(",", 1) + 1);
            // 解密，解密的结果是一个byte数组
            Base64.Decoder decoder = Base64.getDecoder();
            byte[] imgbytes = decoder.decode(base64);
            for (int i = 0; i < imgbytes.length; ++i) {
                if (imgbytes[i] < 0) {
                    imgbytes[i] += 256;
                }
            }
            InputStream in =new ByteArrayInputStream(imgbytes);
            resp.setContentType(MediaType.IMAGE_PNG_VALUE);
            IOUtils.copy(in, resp.getOutputStream());
        } catch (IOException e) {
            throw new GlobalException(RespBeanEnum.PIC_ERROR);
        }

    }


}
