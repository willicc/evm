# evmEVM通用交互程序
说明：适用于大部分EVM网络批量刷tx。可以自行在cnofig.json添加不同链的rpc和链id。

比如，在monad上开发一个faucet合约，然后通过程序批量领取。或者任意其他合约的交互，需要取得合约的地址和data。

## 免责声明：本程序为明文代码，运行前请先审核代码安全性。确定使用后，运行时产生任何损失均与本代码无关

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
<img width="1200" height="1056" alt="image" src="https://github.com/user-attachments/assets/b3c14b95-52c1-47e0-ad84-ee0bc1b78ad6" />


