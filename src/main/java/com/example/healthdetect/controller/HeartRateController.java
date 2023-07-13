package com.example.healthdetect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.grpc.HelloReply;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.HeartRate;
import com.example.healthdetect.entity.Indicator;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.grpclient.GRPCClient;
import com.example.healthdetect.service.ExamineService;
import com.example.healthdetect.service.HeartRateService;
import org.apache.ibatis.annotations.Param;
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
import java.util.Base64;
import java.util.Date;
import java.util.List;

@RestController
@RequestMapping("/heart_rate")
public class HeartRateController {

    @Autowired
    private HeartRateService heartRateService;

    @PostMapping("/insert")
    public RespBean insert(@RequestBody HeartRate  heartRate) {
        boolean save = heartRateService.save(heartRate);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<HeartRate> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(HeartRate::getDetectTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(HeartRate::getDetectTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<HeartRate> resultList = heartRateService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    private InputStream getImgInputStream(String path) throws FileNotFoundException {
        return new FileInputStream(new File(path));
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

    /*
     * 调用算法服务，得到图片的base64编码
     * 直接向前端返回base64编码
     * */
//    @GetMapping("/base64")
//    public RespBean getGraphBase64(HttpServletResponse resp) {
//        //调用算法端，获取base64编码
//        String base64 = null;
//        return RespBean.success(base64);
//    }

    @GetMapping("/base64")
    public RespBean getGraphBase64(HttpServletResponse resp) {
        //调用算法端，获取base64编码
        GRPCClient client = new GRPCClient("localhost", 50001);
        HelloReply response = null;
        try {
            String user = "hjt";
            response = client.greet(user);

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

    @GetMapping("/start_examine")
    public void startExamine() {
        // 发送消息，算法端开始接受视频流...

        // 消息回调，得到指标
    }

}
