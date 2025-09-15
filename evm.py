import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from web3 import Web3
import json
import random
import time
import os
import threading

class EVMInteractor:
    def __init__(self, root):
        self.root = root
        self.root.title("EVM 通用交互程序")
        self.root.geometry("600x500")
        
        # 参数输入框架
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # 配置列权重，使标签和输入更紧凑
        input_frame.grid_columnconfigure(1, weight=1)
        
        # 修复 Mac 上 readonly Combobox 鼠标点击问题 - 增强 style
        style = ttk.Style()
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", "white"), ("!focus", "SystemWindow")],
                  selectforeground=[("readonly", "black")],
                  background=[("readonly", "white")],
                  foreground=[("readonly", "black")])
        
        # 链选择下拉
        tk.Label(input_frame, text="链选择:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.chain_var = tk.StringVar()
        self.chain_combo = ttk.Combobox(input_frame, textvariable=self.chain_var, state="readonly", width=10)
        self.chain_combo.grid(row=0, column=1, pady=2, padx=(0,5), sticky=tk.W)
        self.chain_var.set("eth")  # 默认 eth
        
        # 绑定点击事件：强制下拉菜单打开，修复 macOS 点击无响应
        self.chain_combo.bind('<Button-1>', lambda e: self.chain_combo.event_generate('<Down>'))
        
        self.private_keys = []  # 存储加载的私钥列表
        self.stop_flag = False  # 停止标志
        self.execution_thread = None  # 执行线程
        
        # 目标合约地址
        tk.Label(input_frame, text="交互地址:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.contract_addr_entry = tk.Entry(input_frame, width=50)
        self.contract_addr_entry.grid(row=1, column=1, pady=2, padx=(0,5), sticky=tk.W)  # 左边距0，更贴近标签
        
        # Data (calldata) - 设置为4行
        tk.Label(input_frame, text="Data:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.data_entry = tk.Text(input_frame, height=4, width=65)
        self.data_entry.grid(row=2, column=1, pady=2, padx=(0,5), sticky=tk.W)  # 左边距0，更贴近标签
        
        # 交互次数、Gas、延迟 并列同一行 - 使用子Frame以pack布局实现紧凑
        params_subframe = tk.Frame(input_frame)
        params_subframe.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 交互次数组
        times_frame = tk.Frame(params_subframe)
        times_frame.pack(side=tk.LEFT, padx=(0,5))
        tk.Label(times_frame, text="交互次数:").pack(side=tk.LEFT)
        self.times_entry = tk.Entry(times_frame, width=4)
        self.times_entry.pack(side=tk.LEFT, padx=(2,0))
        self.times_entry.insert(0, "1")
        
        # Gas组
        gas_frame = tk.Frame(params_subframe)
        gas_frame.pack(side=tk.LEFT, padx=(10,5))
        tk.Label(gas_frame, text="Gas (可留空默认动态):").pack(side=tk.LEFT)
        self.gas_entry = tk.Entry(gas_frame, width=8)
        self.gas_entry.pack(side=tk.LEFT, padx=(2,0))
        
        # 延迟组
        delay_frame = tk.Frame(params_subframe)
        delay_frame.pack(side=tk.LEFT, padx=(10,0))
        tk.Label(delay_frame, text="随机延迟时间:").pack(side=tk.LEFT)
        self.delay_entry = tk.Entry(delay_frame, width=6)
        self.delay_entry.pack(side=tk.LEFT, padx=(2,0))
        self.delay_entry.insert(0, "1-5")
        
        # 按钮框架
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        
        # 执行按钮
        self.execute_btn = tk.Button(button_frame, text="执行交互", command=self.start_execution)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮（初始禁用）
        self.stop_btn = tk.Button(button_frame, text="停止交互", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出日志
        self.log_text = scrolledtext.ScrolledText(root, width=70, height=20)
        self.log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # 初始化 config.json 并动态设置下拉选项
        self.load_config()
        
        # 现在自动加载 address.txt（在 log_text 创建后）
        self.auto_load_private_keys()
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def load_config(self):
        config_file = "config.json"
        default_config = {
            "eth": {
                "rpc": "https://mainnet.infura.io",
                "chain_id": 1
            },
            "base": {
                "rpc": "https://mainnet.base.org",
                "chain_id": 8453
            },
            "op": {
                "rpc": "https://mainnet.optimism.io",
                "chain_id": 10
            },
            "bsc": {
                "rpc": "https://bsc-dataseed.binance.org/",
                "chain_id": 56
            },
            "arbitrum": {
                "rpc": "https://arb1.arbitrum.io/rpc",
                "chain_id": 42161
            }
        }
        if not os.path.exists(config_file):
            try:
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.log(f"已创建默认 config.json 文件")
            except Exception as e:
                self.log(f"创建 config.json 失败: {str(e)}")
        # 无论是否存在，都读取并设置下拉选项
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            chain_options = list(config.keys())
            self.chain_combo['values'] = chain_options
            if "eth" not in chain_options:
                self.chain_var.set(chain_options[0] if chain_options else "eth")
            else:
                self.chain_var.set("eth")
            self.log(f"加载 config.json 成功，下拉选项: {chain_options}")
        except Exception as e:
            self.log(f"加载 config.json 失败: {str(e)}")
            self.chain_combo['values'] = ["eth", "base", "op", "bsc", "arbitrum"]
    
    def auto_load_private_keys(self):
        filename = "address.txt"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    self.private_keys = [line.strip() for line in lines if line.strip()]
                    # 确保添加 0x 前缀如果缺少
                    self.private_keys = ["0x" + pk if not pk.startswith("0x") else pk for pk in self.private_keys]
                self.log(f"成功自动加载私钥文件: {filename}, 共 {len(self.private_keys)} 个私钥")
            except Exception as e:
                self.log(f"自动加载文件失败: {str(e)}")
        else:
            self.log("未找到 address.txt 文件，请确保文件存在于当前目录")
    
    def start_execution(self):
        if self.execution_thread and self.execution_thread.is_alive():
            self.log("执行中，请等待或停止当前任务")
            return
        self.stop_flag = False
        self.execution_thread = threading.Thread(target=self.execute_interaction, daemon=True)
        self.execution_thread.start()
        self.execute_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("执行交互已启动...")
    
    def stop_execution(self):
        self.stop_flag = True
        self.execute_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("停止信号已发送，等待当前操作完成...")
    
    def execute_interaction(self):
        try:
            if not self.private_keys:
                raise ValueError("请确保 address.txt 文件存在并加载私钥")
            
            # 从 config.json 获取 RPC 和 chain_id
            config_file = "config.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
            selected_chain = self.chain_var.get()
            if selected_chain not in config:
                raise ValueError(f"无效链选择: {selected_chain}，请检查 config.json")
            rpc = config[selected_chain]["rpc"]
            chain_id = config[selected_chain]["chain_id"]
            self.log(f"使用链 {selected_chain}: RPC={rpc}, Chain ID={chain_id}")
            
            contract_addr = self.contract_addr_entry.get().strip()
            if not contract_addr:
                raise ValueError("合约地址不能为空")
            contract_addr = Web3.to_checksum_address(contract_addr)
            
            data_text = self.data_entry.get("1.0", tk.END).strip()
            data = data_text if data_text and data_text.startswith("0x") else ("0x" + data_text if data_text else "")
            
            times = int(self.times_entry.get().strip() or "1")
            gas_str = self.gas_entry.get().strip()
            gas = int(gas_str) if gas_str else None
            
            # 解析延迟范围
            delay_str = self.delay_entry.get().strip() or "1-5"
            if '-' not in delay_str:
                raise ValueError("延迟范围格式应为 min-max")
            min_delay, max_delay = map(float, delay_str.split('-'))
            if min_delay < 0 or max_delay < min_delay:
                raise ValueError("无效的延迟范围")
            
            # 连接 Web3
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                raise ValueError("无法连接到 RPC")
            
            total_interactions = len(self.private_keys) * times
            self.log(f"开始执行，总交互次数: {total_interactions} (每个私钥 {times} 次, 延迟 {min_delay}-{max_delay}秒)")
            
            for pk_idx, private_key in enumerate(self.private_keys):
                if self.stop_flag:
                    self.log("停止执行")
                    break
                try:
                    account = w3.eth.account.from_key(private_key)
                    self.log(f"私钥 {pk_idx+1}/{len(self.private_keys)}: 账户 {account.address}")
                    
                    # 为每个私钥获取初始 nonce
                    base_nonce = w3.eth.get_transaction_count(account.address)
                    
                    for i in range(times):
                        if self.stop_flag:
                            self.log("停止执行")
                            break
                        # 在每个交易发送前，重新获取最新 nonce 以确保准确
                        current_nonce = w3.eth.get_transaction_count(account.address)
                        self.log(f"  第 {i+1}/{times} 次交互 (最新 nonce: {current_nonce})...")
                        
                        # 构建交易
                        data_bytes = bytes.fromhex(data[2:]) if data and data.startswith("0x") else b''
                        intrinsic_estimate = 21000 + len(data_bytes) * 16  # 粗略内在 gas 估算
                        self.log(f"    Data 长度: {len(data_bytes)} 字节, 粗略内在 gas: ~{intrinsic_estimate}")
                        
                        tx = {
                            'to': contract_addr,
                            'value': 0,
                            'gas': 0,  # 稍后估算
                            'gasPrice': w3.eth.gas_price,
                            'nonce': current_nonce,  # 使用最新 nonce
                            'data': data_bytes,  # 正确处理 data 为 bytes
                            'chainId': chain_id
                        }
                        
                        try:
                            estimated_gas = w3.eth.estimate_gas(tx)
                            self.log(f"    估算 Gas: {estimated_gas}")
                        except Exception as est_e:
                            self.log(f"    估算 Gas 失败 ({est_e}), 使用 fallback 值")
                            estimated_gas = 250000  # fallback 估算
                        
                        if gas is None:
                            # 修复：增加 buffer 到 200%，min 500000 以覆盖 Monad 等链的 intrinsic 需求
                            gas_to_use = max(int(estimated_gas * 2.0), 500000)
                        else:
                            gas_to_use = gas
                        
                        tx['gas'] = gas_to_use
                        self.log(f"    使用 Gas: {gas_to_use}")
                        
                        # 签名并发送
                        signed_tx = account.sign_transaction(tx)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        self.log(f"    交易哈希: {tx_hash.hex()}")
                        
                        # 等待确认 (可选，超时120秒) - 注意：此为阻塞调用，停止后需等待完成
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        status = "成功" if receipt.status == 1 else "失败 (上链成功但执行失败)"
                        self.log(f"    交易确认: {status}")
                        
                        # 如果执行失败 (status == 0)，跳过后续处理但继续下一个交互
                        if receipt.status != 1:
                            self.log(f"    跳过后续处理，继续下一个交互")
                        
                        # 在每次交互后添加随机延迟（包括最后一次），可中断
                        delay = random.uniform(min_delay, max_delay)
                        self.log(f"    等待 {delay:.2f} 秒...")
                        start_time = time.time()
                        while time.time() - start_time < delay:
                            if self.stop_flag:
                                self.log("中断延迟等待")
                                break
                            time.sleep(0.1)
                    
                    if self.stop_flag:
                        break
                    self.log(f"私钥 {pk_idx+1} 所有交互完成")
                    
                    # 在地址（私钥）之间添加随机延迟（除了最后一个）
                    if pk_idx < len(self.private_keys) - 1:
                        delay = random.uniform(min_delay, max_delay)
                        self.log(f"    地址间等待 {delay:.2f} 秒...")
                        start_time = time.time()
                        while time.time() - start_time < delay:
                            if self.stop_flag:
                                self.log("中断地址间延迟等待")
                                break
                            time.sleep(0.1)
                    
                except Exception as e:
                    self.log(f"私钥 {pk_idx+1} 执行异常，跳过: {str(e)}")
                    continue
            
            if not self.stop_flag:
                self.log("所有私钥交互完成！")
            else:
                self.log("交互已停止")
            
            # 重置按钮状态（在主线程中）
            self.root.after(0, self.reset_buttons)
            
        except Exception as e:
            self.log(f"错误: {str(e)}")
            self.root.after(0, self.reset_buttons)
    
    def reset_buttons(self):
        self.execute_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.stop_flag = False

if __name__ == "__main__":
    root = tk.Tk()
    app = EVMInteractor(root)
    root.mainloop()
