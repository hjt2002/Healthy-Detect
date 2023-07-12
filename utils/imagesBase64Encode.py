import base64


# 编码图像格式
def imageToBase64(image_str):
    picture = open(image_str, "rb")
    picture_base64 = base64.b64encode(picture.read())
    # 输出base64编码
    # print(picture_base64)

    return picture_base64


def base64Decode(picture_base64):
    en_picture = base64.b64decode(picture_base64)
    pic = open("re.png", "wb")
    pic.write(en_picture)

    pic.close()
    # print(en_picture)
