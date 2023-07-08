package com.example.healthdetect.entity;

import lombok.Data;

@Data
public class Indicator {
    private Integer heartRate;
    private Integer bloodPressure;
    private Integer bloodOxygen;
    private String mood;
    private String  examineTime;
}
