# evmEVM通用交互程序

## 1 安装支持环境
安装 Python，tkinter（GUI 库）， web3（区块链交互库）

    sudo apt update && sudo apt install python3 python3-pip
    sudo apt install python3-tk
    pip3 install web3

## 2 准备私匙文件和配置文件
程序读取私匙文件address.txt内容，一行一个。类似如下：

0x123456...

config.json如果不包括需要的网络，请自行在config.json中添加所需网络。


## 3 运行脚本
    python3 evm.py

在弹出的窗口中设置参数，选择链和交互目标的合约地址。发送的data。如下图是刷monad运行
    
## 4 运行截图如下
<img width="1200" height="1056" alt="image" src="https://github.com/user-attachments/assets/b9401950-b9a4-4625-bdb4-215e767979e6" />

