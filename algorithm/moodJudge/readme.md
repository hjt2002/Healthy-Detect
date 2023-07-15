
### 1. 首先安装：
>pip install cmake
### 2. 然后，安装dlib库
>pip install dlib
### 3. （不用按了！！！！）然后, 安装face_recognition模块
>pip install face_recognition

##### 3.1 如果不成功，可能要手动安装，
###### 参照：https://blog.csdn.net/qq_65656809/article/details/127237586
### 两个文件夹我直接放在bao文件夹里了，直接复制到python的sit-package里，我不知道能不能直接引用
#### 参考路径 D:\pycharmPro\py3.8\py3.8\Lib\site-packages，就是安装python的包


### 4. （也不用下了！！！！！）还需要下载face_recognition（已经下了，不用下）
##### 下载地址：https://github.com/ageitgey/face_recognition_models
### 在face-recognition-models-master里要python setup.py install 一下

### （这个看情况）会提示gpu没有安装，因此要安装一下pip install tenserflow-cpu(已解决)
##### 但是会有一大堆依赖冲突。。。目前还不清楚会不会影响

#### 可能需要某个训练包？（找到了，不用再下）
>https://github.com/priya-dwivedi/face_and_emotion_detection
