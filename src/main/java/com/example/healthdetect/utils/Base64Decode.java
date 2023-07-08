package com.example.healthdetect.utils;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Base64;
import java.util.UUID;

public class Base64Decode {

    public static String generateImage(String base64, String path) {
        // 解密
        try {
            // 图片分类路径+图片名+图片后缀
            String imgClassPath = path.concat(UUID.randomUUID().toString()).concat(".jpg");

            // 去掉base64前缀 data:image/jpeg;base64,
            base64 = base64.substring(base64.indexOf(",", 1) + 1);
            // 解密，解密的结果是一个byte数组
            Base64.Decoder decoder = Base64.getDecoder();
            byte[] img_bytes = decoder.decode(base64);
            for (int i = 0; i < img_bytes.length; ++i) {
                if (img_bytes[i] < 0) {
                    img_bytes[i] += 256;
                }
            }

            // 保存图片
            OutputStream out = new FileOutputStream(imgClassPath);
            out.write(img_bytes);
            out.flush();
            out.close();
            // 返回图片的相对路径 = 图片分类路径+图片名+图片后缀
            return imgClassPath;
        } catch (IOException e) {
            return null;
        }
    }
}
