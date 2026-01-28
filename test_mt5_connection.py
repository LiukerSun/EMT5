import MetaTrader5 as mt5
import time
import subprocess

print("正在启动MT5终端...")
subprocess.Popen([r'C:\Program Files\MetaTrader 5\terminal64.exe'])
time.sleep(8)

print("尝试连接...")
result = mt5.initialize(
    path=r'C:\Program Files\MetaTrader 5\terminal64.exe',
    login=316154676,
    password='mniLiuker0520..',
    server='XMGlobal-MT5 7',
    timeout=60000
)

print(f'连接结果: {result}')
error = mt5.last_error()
print(f'错误信息: {error}')

if result:
    info = mt5.account_info()
    print(f'账户信息:')
    print(f'  账号: {info.login}')
    print(f'  余额: {info.balance}')
    print(f'  货币: {info.currency}')
    print(f'  净值: {info.equity}')
    print(f'  杠杆: {info.leverage}')
    mt5.shutdown()
else:
    print("连接失败！")
