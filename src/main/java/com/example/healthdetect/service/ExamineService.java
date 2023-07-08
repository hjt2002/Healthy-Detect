package com.example.healthdetect.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.IndicatorMapper;
import com.example.healthdetect.entity.Indicator;
import org.springframework.stereotype.Service;

@Service
public class ExamineService extends ServiceImpl<IndicatorMapper,Indicator> {

}
