# tcp-proxy-by-python  [![Build Status](https://travis-ci.org/daoiqi/python-proxy-forward.png)](https://travis-ci.org/daoiqi/python-proxy-forward)
tcp proxy using python code

download code ,and run it.

# Require
require [`PySocks`](https://github.com/Anorov/PySocks)

`pip install PySocks`

# Config
modify `proxy.ini`, such as:

```
[mysql_section]
listen=12000                  # listen 0.0.0.0:12000
remote=127.0.0.1:3306         # want to access remote host:port
socks5=127.0.0.1:7700         # the socks5 proxy

[ftp_section]
listen=127.0.0.1:12001        # listen 127.0.0.1:12001
remote=123.123.123.123:21     # remote host:port
#socks5=127.0.0.1:7700        # not proxy
```

# Run
```
cd ./src
python proxy.py
```

# socks5 proxy
```bash
ssh -2 -D 7700 -l username host -p 22 -Nf  -o ServerAliveInterval=300 -o ServerAliveCountMax=3
```

```
-2 使用ssh2协议
-D 7700 在本机开启7700端口，流量巾帼       经过7700端口就可以走代理了。
-l  usernmae 输入用户名
host   ssh服务器
-p 22 服务器的ssh端口
-o ServerAliveInterval=300   如果没有操作，那么客户端会向ssh server发送保持连接的信号
-o ServerAliveCountMax=3  如果server没响应，那么最大请求3次都没响应就断开了。
```
