# EVM General Interaction Program

Description: Suitable for batch transactions on most EVM networks. You can add RPC endpoints and chain IDs for different chains in `config.json`.

For example, develop a faucet contract on Monad and then use this program to batch-claim it. Or interact with any other contract — you only need the contract address and the `data` payload.

## Disclaimer

This program is provided as plain-text source code. Please review the code for safety before running. Any losses or damages that occur while using this program are not the responsibility of this code.

## 1 Install required environment

Install Python, `tkinter` (GUI library), and `web3` (blockchain interaction library):

```bash
sudo apt update && sudo apt install python3 python3-pip
sudo apt install python3-tk
pip3 install web3
```

## 2 Prepare private key file and configuration

The program reads private keys from `address.txt`, one per line. Example:

```
0x123456...
```

If `config.json` does not include the network you need, add the required network entries (RPC and chainId) to `config.json` yourself.

## 3 Run the script

```bash
python3 evm.py
```

In the popup window set the parameters, choose the chain and the target contract address for interaction, and provide the `data` to send. The example below shows running batch claims on Monad.

## 4 Screenshot of running

<img width="1200" height="1056" alt="image" src="https://github.com/user-attachments/assets/b3c14b95-52c1-47e0-ad84-ee0bc1b78ad6" />
