package com.example.healthdetect;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan(value = "com.example.healthdetect.dao")
public class HealthDetectApplication {

    public static void main(String[] args) {
        SpringApplication.run(HealthDetectApplication.class, args);
    }

}
