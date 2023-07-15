package com.example.healthdetect.common;

/**
 * 公共返回对象枚举
 *
 * @author: LC
 * @date 2022/3/2 1:44 下午
 * @ClassName: RespBean
 */

public enum RespBeanEnum {

    //通用
    SUCCESS(200, "响应成功"),
    ERROR(500, "服务端异常"),
    PIC_ERROR(508, "图片资源异常"),

    GRPC_ERROR(600, "GRPC连接异常"),

    ;

    private final Integer code;
    private final String message;

    public Integer getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    RespBeanEnum(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
