package com.example.healthdetect.exception;

import com.example.healthdetect.common.RespBeanEnum;

/**
 * 全局异常
 *
 * @author: LC
 * @date 2022/3/2 5:32 下午
 * @ClassName: GlobalException
 */
public class GlobalException extends RuntimeException {

    private RespBeanEnum respBeanEnum;

    public RespBeanEnum getRespBeanEnum() {
        return respBeanEnum;
    }

    public void setRespBeanEnum(RespBeanEnum respBeanEnum) {
        this.respBeanEnum = respBeanEnum;
    }

    public GlobalException(RespBeanEnum respBeanEnum) {
        this.respBeanEnum = respBeanEnum;
    }
}
