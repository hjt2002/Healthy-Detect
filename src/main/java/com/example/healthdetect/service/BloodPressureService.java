package com.example.healthdetect.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.healthdetect.dao.BloodPressureMapper;
import com.example.healthdetect.dao.HeartRateMapper;
import com.example.healthdetect.entity.BloodPressure;
import com.example.healthdetect.entity.HeartRate;
import org.springframework.stereotype.Service;

@Service
public class BloodPressureService extends ServiceImpl<BloodPressureMapper, BloodPressure> {

}
