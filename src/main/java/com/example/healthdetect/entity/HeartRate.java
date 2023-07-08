package com.example.healthdetect.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import lombok.Data;

@Data
public class HeartRate {
    private Integer heartRate;
    private String detectTime;
    private Float meanNni;
    private Float sdnn;
    private Float sdsd;
    @TableField("nni_50")
    private Integer nni50;
    @TableField("pnni_50")
    private Float pnni50;
    @TableField("nni_20")
    private Integer nni20;
    @TableField("pnni_20")
    private Float pnni20;
    private Float rmssd;
    private Float medianNni;
    private Float rangeNni;
    private Float cvsd;
    private Float cvnni;
    private Float meanHr;
    private Float maxHr;
    private Float minHr;
    private Float stdHr;

}
