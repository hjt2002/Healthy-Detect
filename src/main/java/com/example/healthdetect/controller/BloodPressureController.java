package com.example.healthdetect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.grpc.HelloReply;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.BloodPressure;
import com.example.healthdetect.entity.HeartRate;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import com.example.healthdetect.service.BloodPressureService;
import com.example.healthdetect.service.HeartRateService;
import org.apache.tomcat.util.http.fileupload.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Base64;
import java.util.Date;
import java.util.List;

@RestController
@RequestMapping("/blood_pressure")
public class BloodPressureController {

    @Autowired
    private BloodPressureService bloodPressureService;

    @PostMapping("/insert")
    public RespBean insert(@RequestBody BloodPressure bloodPressure) {
        boolean save = bloodPressureService.save(bloodPressure);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<BloodPressure> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(BloodPressure::getDetectTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(BloodPressure::getDetectTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<BloodPressure> resultList = bloodPressureService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    /*
    * 调用算法服务，得到图片的base64编码
    * 将base64编码转成 图片格式返回前端
    * */
    @GetMapping("/graph")
    public void getGraph(HttpServletResponse resp)  {
        //调用算法端，获取base64编码
        String base64 = null;
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

    @GetMapping("/latest")
    public RespBean getLatest() {
        LambdaQueryWrapper<BloodPressure> lambdaQuery = Wrappers.lambdaQuery();
        lambdaQuery.orderByDesc(BloodPressure::getDetectTime).last(" LIMIT 1");
        // 执行查询操作
        List<BloodPressure> resultList = bloodPressureService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    /*
     * 调用算法服务，得到图片的base64编码
     * 直接向前端返回base64编码
     * */
    @GetMapping("/base64")
    public RespBean getGraphBase64(HttpServletResponse resp) {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        HelloReply response = null;
        try {
            String queueName = "blood_pressure";
            response = client.greet(queueName);

        } finally {
            try {
                client.shutdown();
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }
        String base64 = response.getBase64Url();
        return RespBean.success(base64);
    }
}
