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
    # ERC-20 transfer方法的标准方法ID，使用keccak
    method_id = w3.keccak(text="transfer(address,uint256)").hex()[:10]
    # 转账接收地址，转换为32字节hex
    to_address_hex = to_address.lower().replace('0x', '').rjust(64, '0')
    # 转账金额，考虑代币的小数位数
    amount_hex = hex(amount * (10 ** decimals))[2:].rjust(64, '0')
    return method_id + to_address_hex + amount_hex


# Excel文件路径
file_path = ''  # 更新为您的文件路径

# 加载账户信息
df_accounts = load_accounts_from_excel(file_path)

# 指定接收代币的地址
recipient_address = ''  # 更新为实际接收地址
# 代币合约地址
token_contract_address = ''  # 更新为代币合约地址
# 转账金额
amount = 10  # 更新为实际转账金额
# 代币的小数位数
decimals = 18  # 根据代币实际情况更新



# 过滤掉Address列为空的行
df_accounts.dropna(subset=['Address'], inplace=True)

# 填充'yes'列中的NaN值为0
df_accounts['transfer'] = df_accounts['transfer'].fillna(0)

# 对每个账户进行操作
for index, account in df_accounts.iterrows():
    # 现在可以安全地将'yes'列的值转换为整数，因为我们已经填充了所有的NaN值
    processed_flag = int(account['transfer'])
    address = str(account['Address']).strip()  # 移除可能的空格

    # 检查账户是否已经运行
    if processed_flag == 1:
        print(f"Account {address} is already processed. Skipping...")
        continue

    # 检查地址是否为有效的以太坊地址
    if not Web3.is_address(address):
        print(f"Invalid address {address}. Skipping...")
        continue

    # 生成ERC-20代币转账的data字段
    data = generate_transfer_data(recipient_address, amount, decimals)

    # 获取当前的平均Gas价格
    current_gas_price = web3.eth.gas_price
    print(f"当前的平均Gas价格: {current_gas_price}")

    # 构建交易信息
    tx = {
        'chainId': 97,
        'gas': 21000,
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
