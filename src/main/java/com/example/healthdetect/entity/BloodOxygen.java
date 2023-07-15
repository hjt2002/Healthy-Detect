package com.example.healthdetect.entity;

import lombok.Data;

@Data
public class BloodOxygen {
    String oxLevel;
    String detectTime;

    public BloodOxygen() {
    }

    public BloodOxygen(String oxLevel, String detectTime) {
        this.oxLevel = oxLevel;
        this.detectTime = detectTime;
    }
}
