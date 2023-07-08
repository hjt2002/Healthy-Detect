package com.example.healthdetect.common;

import lombok.Data;

@Data
public class RespBean {

    private long code;
    private String message;
    private Object object;

    public static RespBean success() {
        return new RespBean(RespBeanEnum.SUCCESS.getCode(), RespBeanEnum.SUCCESS.getMessage(), null);
    }

    public static RespBean success(Object object) {
        return new RespBean(RespBeanEnum.SUCCESS.getCode(), RespBeanEnum.SUCCESS.getMessage(), object);
    }

    public static RespBean error(RespBeanEnum respBeanEnum) {
        return new RespBean(respBeanEnum.getCode(), respBeanEnum.getMessage(), null);
    }

    public static RespBean error(RespBeanEnum respBeanEnum, Object object) {
        return new RespBean(respBeanEnum.getCode(), respBeanEnum.getMessage(), object);
    }

    public RespBean(){

    }

    public RespBean(long code, String message, Object object) {
        this.code = code;
        this.message = message;
        this.object = object;
    }



}
