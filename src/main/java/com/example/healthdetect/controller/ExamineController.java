package com.example.healthdetect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.Indicator;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.service.ExamineService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

@RestController
public class ExamineController {

    @Autowired
    private ExamineService examineService;

    @PostMapping("/insert")
    public RespBean insert(@RequestBody Indicator indicator) {
        boolean save = examineService.save(indicator);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<Indicator> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(Indicator::getExamineTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(Indicator::getExamineTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<Indicator> resultList = examineService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    @GetMapping("/start_examine")
    public void startExamine() {
        // 发送消息，算法端开始接受视频流...

        // 消息回调，得到指标
    }


}
