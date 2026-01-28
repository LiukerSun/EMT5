import MetaTrader5 as mt5
import time

# 连接MT5
print("连接MT5...")
result = mt5.initialize(
    path=r'C:\Program Files\MetaTrader 5\terminal64.exe',
    login=316154676,
    password='mniLiuker0520..',
    server='XMGlobal-MT5 7',
    timeout=60000
)

if not result:
    print(f"连接失败: {mt5.last_error()}")
    exit()

print("连接成功！\n")

# 搜索黄金相关品种
print("=== 搜索黄金相关品种 ===")
symbols = mt5.symbols_get()
gold_symbols = [s.name for s in symbols if 'GOLD' in s.name.upper() or 'XAU' in s.name.upper()]

print(f"找到 {len(gold_symbols)} 个黄金品种:")
for symbol in gold_symbols:
    print(f"  - {symbol}")

print("\n=== 尝试获取品种信息 ===")
for symbol in gold_symbols[:5]:  # 只测试前5个
    info = mt5.symbol_info(symbol)
    if info:
        print(f"\n品种: {symbol}")
        print(f"  描述: {info.description}")
        print(f"  可见: {info.visible}")
        print(f"  选中: {info.select}")
        print(f"  买价: {info.ask}")
        print(f"  卖价: {info.bid}")

mt5.shutdown()
