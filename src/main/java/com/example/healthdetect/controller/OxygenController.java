package com.example.healthdetect.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.healthdetect.common.RespBean;
import com.example.healthdetect.common.RespBeanEnum;
import com.example.healthdetect.entity.BloodOxygen;
import com.example.healthdetect.exception.GlobalException;
import com.example.healthdetect.service.BloodOxygenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@RestController
@RequestMapping("/oxygen")
public class OxygenController {

    @Autowired
    private BloodOxygenService bloodOxygenService;


    @PostMapping("/insert")
    @ResponseBody
    public RespBean insert(@RequestBody BloodOxygen bloodOxygen) {
        boolean save = bloodOxygenService.save(bloodOxygen);
        if (!save) {
            throw new GlobalException(RespBeanEnum.ERROR);
        }
        return RespBean.success();
    }

    @GetMapping("/list")
    @ResponseBody
    public RespBean getList(@RequestParam(required = false) String examTimeMin, @RequestParam(required = false) String examTimeMax) {
        LambdaQueryWrapper<BloodOxygen> lambdaQuery = Wrappers.lambdaQuery();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (examTimeMin != null) {
            try {
                Date minDate = dateFormat.parse(examTimeMin);
                lambdaQuery.ge(BloodOxygen::getDetectTime, minDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        if (examTimeMax != null) {
            try {
                Date maxDate = dateFormat.parse(examTimeMax);
                lambdaQuery.le(BloodOxygen::getDetectTime, maxDate);
            } catch (ParseException e) {
                e.printStackTrace();
                // 处理日期解析异常...
            }
        }
        // 执行查询操作
        List<BloodOxygen> resultList = bloodOxygenService.list(lambdaQuery);
        return RespBean.success(resultList);
    }

    @GetMapping("/new_one")
    public RespBean getLatestData() {
        return RespBean.success(bloodOxygenService.getLatest());
    }


}
