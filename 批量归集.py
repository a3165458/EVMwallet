import pandas as pd
from web3 import Web3
import time
import random

# 初始化Web3接口和连接到Binance Smart Chain测试网
w3 = Web3(Web3.HTTPProvider('https://data-seed-prebsc-1-s1.binance.org:8545/'))

# 函数：从Excel文件中加载账户
def load_accounts_from_excel(file_path):
    return pd.read_excel(file_path, engine='openpyxl')

# 函数：将更新后的账户信息保存回Excel文件
def save_accounts_to_excel(df, file_path):
    df.to_excel(file_path, index=False, engine='openpyxl')

# 函数：生成ERC-20代币转账的data字段
def generate_transfer_data(to_address, amount, decimals=18):
    method_id = w3.keccak(text="transfer(address,uint256)").hex()[:10]
    to_address_hex = to_address.lower().replace('0x', '').rjust(64, '0')
    amount_hex = hex(amount * (10 ** decimals))[2:].rjust(64, '0')
    return method_id + to_address_hex + amount_hex

# 函数：获取ERC-20代币余额
def get_token_balance(token_address, wallet_address):
    method_id = w3.keccak(text="balanceOf(address)").hex()[:10]
    wallet_address_hex = wallet_address.lower().replace('0x', '').rjust(64, '0')
    data = method_id + wallet_address_hex
    balance = w3.eth.call({'to': token_address, 'data': data})
    return int(balance.hex(), 16)

# 加载账户信息
file_path = ''  # 更新为您的文件路径
df_accounts = load_accounts_from_excel(file_path)

# 指定接收代币的地址和代币合约地址
recipient_address = ''  # 更新为实际接收地址
token_contract_address = ''  # 更新为代币合约地址
amount = 5  # 更新为实际转账金额
decimals = 18  # 根据代币实际情况更新

# 过滤和准备
df_accounts.dropna(subset=['Address'], inplace=True)
df_accounts['transfer'] = df_accounts['transfer'].fillna(0)

for index, account in df_accounts.iterrows():
    processed_flag = int(account['transfer'])
    address = str(account['Address']).strip()

    if processed_flag == 1:
        print(f"Account {address} is already processed. Skipping...")
        continue

    if not Web3.is_address(address):
        print(f"Invalid address {address}. Skipping...")
        continue

    balance = get_token_balance(token_contract_address, address)
    if balance < amount * (10 ** decimals):
        print(f"Insufficient balance in account {address}. Skipping...")
        continue
    
    try:
        current_gas_price = w3.eth.gas_price
    except:
        print("Error fetching current gas price. Using default.")
        current_gas_price = w3.to_wei(5, 'gwei') 

    # 生成ERC-20代币转账的data字段
    data = generate_transfer_data(recipient_address, amount, decimals)

    # 构建交易字典
    tx = {
        'chainId': 97,
        'gas': 50000,
        'gasPrice': current_gas_price,
        'nonce': w3.eth.get_transaction_count(account['Address']),
        'to': token_contract_address,
        'value': 0,
        'data': data
    }

    # 签名交易
    signed_tx = w3.eth.account.sign_transaction(tx, account['PrivateKey'])

    # 发送交易
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent with hash: {tx_hash.hex()}")

    # 更新DataFrame中的'transfer'列为1，表示已处理
    df_accounts.at[index, 'transfer'] = 1


    # 保存更新后的Excel文件
    save_accounts_to_excel(df_accounts, file_path)

    # 随机等待时间以模拟人类操作，防止被节点限制
    sleep_time = random.randint(30, 80)
    print(f"Waiting for {sleep_time} seconds...")
    time.sleep(sleep_time)
