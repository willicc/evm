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
        self.root.title("EVM General Interaction Program")
        self.root.geometry("600x500")
        
        # Input frame for parameters
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Configure column weight so labels and inputs align compactly
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Fix for readonly Combobox click issue on mac - enhance style
        style = ttk.Style()
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", "white"), ("!focus", "SystemWindow")],
                  selectforeground=[("readonly", "black")],
                  background=[("readonly", "white")],
                  foreground=[("readonly", "black")])
        
        # Chain selection combobox
        tk.Label(input_frame, text="Chain:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.chain_var = tk.StringVar()
        self.chain_combo = ttk.Combobox(input_frame, textvariable=self.chain_var, state="readonly", width=10)
        self.chain_combo.grid(row=0, column=1, pady=2, padx=(0,5), sticky=tk.W)
        self.chain_var.set("eth")  # default eth
        
        # Bind click to force dropdown open (fix for macOS unresponsive click)
        self.chain_combo.bind('<Button-1>', lambda e: self.chain_combo.event_generate('<Down>'))
        
        self.private_keys = []  # store loaded private keys
        self.stop_flag = False  # stop flag
        self.execution_thread = None  # execution thread
        
        # Target contract address
        tk.Label(input_frame, text="Contract address:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.contract_addr_entry = tk.Entry(input_frame, width=50)
        self.contract_addr_entry.grid(row=1, column=1, pady=2, padx=(0,5), sticky=tk.W)
        
        # Data (calldata) - 4 lines
        tk.Label(input_frame, text="Data:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.data_entry = tk.Text(input_frame, height=4, width=65)
        self.data_entry.grid(row=2, column=1, pady=2, padx=(0,5), sticky=tk.W)
        
        # Interaction count, Gas, Delay on same row - use subframe for compact layout
        params_subframe = tk.Frame(input_frame)
        params_subframe.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Interaction count group
        times_frame = tk.Frame(params_subframe)
        times_frame.pack(side=tk.LEFT, padx=(0,5))
        tk.Label(times_frame, text="Interactions:").pack(side=tk.LEFT)
        self.times_entry = tk.Entry(times_frame, width=4)
        self.times_entry.pack(side=tk.LEFT, padx=(2,0))
        self.times_entry.insert(0, "1")
        
        # Gas group
        gas_frame = tk.Frame(params_subframe)
        gas_frame.pack(side=tk.LEFT, padx=(10,5))
        tk.Label(gas_frame, text="Gas (leave blank for dynamic):").pack(side=tk.LEFT)
        self.gas_entry = tk.Entry(gas_frame, width=8)
        self.gas_entry.pack(side=tk.LEFT, padx=(2,0))
        
        # Delay group
        delay_frame = tk.Frame(params_subframe)
        delay_frame.pack(side=tk.LEFT, padx=(10,0))
        tk.Label(delay_frame, text="Random delay (s):").pack(side=tk.LEFT)
        self.delay_entry = tk.Entry(delay_frame, width=6)
        self.delay_entry.pack(side=tk.LEFT, padx=(2,0))
        self.delay_entry.insert(0, "1-5")
        
        # Button frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        
        # Execute button
        self.execute_btn = tk.Button(button_frame, text="Start Interactions", command=self.start_execution)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button (initially disabled)
        self.stop_btn = tk.Button(button_frame, text="Stop", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Output log
        self.log_text = scrolledtext.ScrolledText(root, width=70, height=20)
        self.log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Initialize config.json and dynamically set combobox options
        self.load_config()
        
        # Auto-load address.txt now (after log_text is created)
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
                self.log(f"Default config.json file created")
            except Exception as e:
                self.log(f"Failed to create config.json: {str(e)}")
        # Read and set combobox values regardless of whether file existed
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            chain_options = list(config.keys())
            self.chain_combo['values'] = chain_options
            if "eth" not in chain_options:
                self.chain_var.set(chain_options[0] if chain_options else "eth")
            else:
                self.chain_var.set("eth")
            self.log(f"Loaded config.json successfully, options: {chain_options}")
        except Exception as e:
            self.log(f"Failed to load config.json: {str(e)}")
            self.chain_combo['values'] = ["eth", "base", "op", "bsc", "arbitrum"]
    
    def auto_load_private_keys(self):
        filename = "address.txt"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    self.private_keys = [line.strip() for line in lines if line.strip()]
                    # Ensure 0x prefix if missing
                    self.private_keys = ["0x" + pk if not pk.startswith("0x") else pk for pk in self.private_keys]
                self.log(f"Successfully auto-loaded private keys from: {filename}, total {len(self.private_keys)} keys")
            except Exception as e:
                self.log(f"Auto-load failed: {str(e)}")
        else:
            self.log("address.txt not found. Make sure the file exists in the current directory")
    
    def start_execution(self):
        if self.execution_thread and self.execution_thread.is_alive():
            self.log("Execution already running. Please wait or stop the current job")
            return
        self.stop_flag = False
        self.execution_thread = threading.Thread(target=self.execute_interaction, daemon=True)
        self.execution_thread.start()
        self.execute_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("Interaction execution started...")
    
    def stop_execution(self):
        self.stop_flag = True
        self.execute_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Stop signal sent, waiting for current operation to finish...")
    
    def execute_interaction(self):
        try:
            if not self.private_keys:
                raise ValueError("Please ensure address.txt exists and private keys are loaded")
            
            # Read RPC and chain_id from config.json
            config_file = "config.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
            selected_chain = self.chain_var.get()
            if selected_chain not in config:
                raise ValueError(f"Invalid chain selection: {selected_chain}. Please check config.json")
            rpc = config[selected_chain]["rpc"]
            chain_id = config[selected_chain]["chain_id"]
            self.log(f"Using chain {selected_chain}: RPC={rpc}, Chain ID={chain_id}")
            
            contract_addr = self.contract_addr_entry.get().strip()
            if not contract_addr:
                raise ValueError("Contract address cannot be empty")
            contract_addr = Web3.to_checksum_address(contract_addr)
            
            data_text = self.data_entry.get("1.0", tk.END).strip()
            data = data_text if data_text and data_text.startswith("0x") else ("0x" + data_text if data_text else "")
            
            times = int(self.times_entry.get().strip() or "1")
            gas_str = self.gas_entry.get().strip()
            gas = int(gas_str) if gas_str else None
            
            # Parse delay range
            delay_str = self.delay_entry.get().strip() or "1-5"
            if '-' not in delay_str:
                raise ValueError("Delay range format should be min-max")
            min_delay, max_delay = map(float, delay_str.split('-'))
            if min_delay < 0 or max_delay < min_delay:
                raise ValueError("Invalid delay range")
            
            # Connect to Web3
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                raise ValueError("Unable to connect to RPC")
            
            total_interactions = len(self.private_keys) * times
            self.log(f"Start execution, total interactions: {total_interactions} (each key {times} times, delay {min_delay}-{max_delay}s)")
            
            for pk_idx, private_key in enumerate(self.private_keys):
                if self.stop_flag:
                    self.log("Execution stopped")
                    break
                try:
                    account = w3.eth.account.from_key(private_key)
                    self.log(f"Private key {pk_idx+1}/{len(self.private_keys)}: account {account.address}")
                    
                    # Get initial nonce for each private key
                    base_nonce = w3.eth.get_transaction_count(account.address)
                    
                    for i in range(times):
                        if self.stop_flag:
                            self.log("Execution stopped")
                            break
                        # Before each tx, re-fetch latest nonce to ensure accuracy
                        current_nonce = w3.eth.get_transaction_count(account.address)
                        self.log(f"  Interaction {i+1}/{times} (latest nonce: {current_nonce})...")
                        
                        # Build transaction
                        data_bytes = bytes.fromhex(data[2:]) if data and data.startswith("0x") else b''
                        intrinsic_estimate = 21000 + len(data_bytes) * 16  # rough intrinsic gas estimate
                        self.log(f"    Data length: {len(data_bytes)} bytes, rough intrinsic gas: ~{intrinsic_estimate}")
                        
                        tx = {
                            'to': contract_addr,
                            'value': 0,
                            'gas': 0,  # will estimate later
                            'gasPrice': w3.eth.gas_price,
                            'nonce': current_nonce,  # use latest nonce
                            'data': data_bytes,  # handle data as bytes
                            'chainId': chain_id
                        }
                        
                        try:
                            estimated_gas = w3.eth.estimate_gas(tx)
                            self.log(f"    Estimated gas: {estimated_gas}")
                        except Exception as est_e:
                            self.log(f"    Gas estimation failed ({est_e}), using fallback value")
                            estimated_gas = 250000  # fallback estimate
                        
                        if gas is None:
                            # Add buffer up to 200%, min 500000 to cover intrinsic needs on some chains like Monad
                            gas_to_use = max(int(estimated_gas * 2.0), 500000)
                        else:
                            gas_to_use = gas
                        
                        tx['gas'] = gas_to_use
                        self.log(f"    Using gas: {gas_to_use}")
                        
                        # Sign and send
                        signed_tx = account.sign_transaction(tx)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        self.log(f"    Tx hash: {tx_hash.hex()}")
                        
                        # Wait for confirmation (optional, timeout 120s) - note: blocking call
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                        status = "Success" if receipt.status == 1 else "Failed (on-chain but execution failed)"
                        self.log(f"    Tx confirmed: {status}")
                        
                        # If execution failed (status == 0), skip further processing but continue next interaction
                        if receipt.status != 1:
                            self.log(f"    Skipping any post-processing, continuing to next interaction")
                        
                        # Add random delay after each interaction (including last), can be interrupted
                        delay = random.uniform(min_delay, max_delay)
                        self.log(f"    Waiting {delay:.2f} seconds...")
                        start_time = time.time()
                        while time.time() - start_time < delay:
                            if self.stop_flag:
                                self.log("Interrupting delay wait")
                                break
                            time.sleep(0.1)
                    
                    if self.stop_flag:
                        break
                    self.log(f"All interactions for private key {pk_idx+1} completed")
                    
                    # Add random delay between addresses (except after last)
                    if pk_idx < len(self.private_keys) - 1:
                        delay = random.uniform(min_delay, max_delay)
                        self.log(f"    Waiting {delay:.2f} seconds between addresses...")
                        start_time = time.time()
                        while time.time() - start_time < delay:
                            if self.stop_flag:
                                self.log("Interrupting between-address delay wait")
                                break
                            time.sleep(0.1)
                    
                except Exception as e:
                    self.log(f"Private key {pk_idx+1} execution error, skipping: {str(e)}")
                    continue
            
            if not self.stop_flag:
                self.log("All private key interactions completed!")
            else:
                self.log("Interactions stopped")
            
            # Reset button states (on main thread)
            self.root.after(0, self.reset_buttons)
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.root.after(0, self.reset_buttons)
    
    def reset_buttons(self):
        self.execute_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.stop_flag = False

if __name__ == "__main__":
    root = tk.Tk()
    app = EVMInteractor(root)
    root.mainloop()
