package com.example.healthdetect.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.RespirationRate;
import com.example.healthdetect.entity.Temperature;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import com.example.healthdetect.service.RespirationRateService;
import org.apache.tomcat.util.http.fileupload.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@RestController
@RequestMapping("/rr")
public class RespirationController {

    @Autowired
    private RespirationRateService respirationRateService;


    @PostMapping("/insert")
    @ResponseBody
    public RespBean insert(@RequestBody RespirationRate respirationRate) {
        boolean save = respirationRateService.save(respirationRate);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    @ResponseBody
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<RespirationRate> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(RespirationRate::getDetectTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(RespirationRate::getDetectTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<RespirationRate> resultList = respirationRateService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    @GetMapping("/latest_one")
    public RespBean getLatestOne() {
        return RespBean.success(respirationRateService.getLatestOne());
    }

    @GetMapping("/latest_queue")
    public RespBean getLatestData() {
        return RespBean.success(respirationRateService.getLatestQueue());
    }

//    @GetMapping("/base64")
//    public RespBean getGraphBase64() {
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
//        String mapStr = response.getBase64Url();
//        JSONObject resObj = JSONObject.parseObject(mapStr);
//        Temperature tempObj = new Temperature(resObj.getString("temperature"), resObj.getString("time"));
//        respirationRateService.save(tempObj);
//        HashMap<String, String> data = new HashMap<>();
//        data.put("temperatureObj", JSON.toJSONString(tempObj));
//        data.put("base64", resObj.getString("base64"));
//        return RespBean.success(data);
//    }




}
