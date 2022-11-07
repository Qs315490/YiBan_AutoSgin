FROM python:alpine

# 创建工作文件夹
RUN mkdir /works
WORKDIR /works
# 安装依赖
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories \
	&& apk --update add --no-cache tzdata alpine-sdk autoconf automake libtool\
	&& cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
	&& apk del tzdata \
	&& mkdir -p /usr/share/zoneinfo/Asia/ \
	&& ln -s /etc/localtime /usr/share/zoneinfo/Asia/Shanghai \
	&& pip3 install requests pycrypto \
	&& apk del alpine-sdk autoconf automake libtool
# 复制程序文件
COPY src/*.py /works/

ENTRYPOINT [ "python3", "/works/yibanAutoSing.py" ]