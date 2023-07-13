package com.example.healthdetect.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.healthdetect.entity.BloodPressure;
import com.example.healthdetect.entity.Indicator;
import org.springframework.stereotype.Repository;

@Repository
public interface BloodPressureMapper extends BaseMapper<BloodPressure> {
}
