package com.example.healthdetect.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.healthdetect.entity.HeartRate;
import com.example.healthdetect.entity.Indicator;
import org.springframework.stereotype.Repository;

@Repository
public interface HeartRateMapper extends BaseMapper<HeartRate> {
}
