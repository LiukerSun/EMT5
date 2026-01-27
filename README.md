# EMT5 - MetaTrader 5 Python 封装库

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个简洁易用的 MetaTrader 5 Python 封装库，提供了连接管理、账户信息、品种信息、交易操作、多账户管理等完整功能。

## 特性

- 🔌 **连接管理** - 简化 MT5 终端连接和断开操作
- 📊 **账户信息** - 获取账户余额、权益、保证金等信息
- 📈 **品种管理** - 查询和管理交易品种，获取实时报价
- 💰 **交易操作** - 支持市价单、限价单、止损止盈等
- 📋 **持仓查询** - 获取当前持仓和挂单信息
- 👥 **多账户管理** - 支持管理多个 MT5 账户，快速切换
- 📝 **日志记录** - 统一的日志接口，支持多级别输出
- 🎯 **类型提示** - 完整的类型注解，提供更好的 IDE 支持
- 🔄 **上下文管理** - 支持 `with` 语句自动管理连接

## 安装

### 前置要求

- Python 3.7+
- MetaTrader 5 终端
- MetaTrader5 Python 包

### 安装依赖

```bash
pip install MetaTrader5
```

## 快速开始

### 基本使用

```python
from utils import EMT5, logger

# 创建 EMT5 实例
mt5_client = EMT5()

# 连接到 MT5 终端
if mt5_client.initialize(
    path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
    login=你的账号,
    password="你的密码",
    server="你的服务器"
):
    logger.info("连接成功")

    # 获取账户信息
    account_info = mt5_client.get_account_info()
    print(f"账户余额: {account_info['balance']}")

    # 断开连接
    mt5_client.shutdown()
else:
    logger.error("连接失败")
```

### 使用上下文管理器

```python
from utils import EMT5, logger

# 使用 with 语句自动管理连接
with EMT5() as mt5_client:
    if mt5_client.initialize(login=你的账号, password="你的密码", server="你的服务器"):
        # 执行交易操作
        account_info = mt5_client.get_account_info()
        logger.info(f"账户余额: {account_info['balance']}")
    # 退出时自动断开连接
```

## 核心功能

### 1. 连接管理

```python
# 初始化连接
mt5_client.initialize(
    path=r"C:\Program Files\MetaTrader 5\terminal64.exe",  # MT5 路径（可选）
    login=12345678,           # 账号
    password="your_password",  # 密码
    server="ServerName",       # 服务器
    timeout=60000,            # 超时时间（毫秒）
    portable=False            # 便携模式
)

# 检查连接状态
if mt5_client.is_connected():
    print("已连接")

# 获取终端信息
terminal_info = mt5_client.get_terminal_info()

# 获取版本信息
version = mt5_client.get_version()

# 断开连接
mt5_client.shutdown()
```

### 2. 账户信息

```python
# 获取账户信息
account_info = mt5_client.get_account_info()

print(f"账户余额: {account_info['balance']}")
print(f"账户权益: {account_info['equity']}")
print(f"已用保证金: {account_info['margin']}")
print(f"可用保证金: {account_info['margin_free']}")
print(f"保证金水平: {account_info['margin_level']}%")
print(f"当前浮动盈亏: {account_info['profit']}")
print(f"杠杆比例: {account_info['leverage']}")
```

### 3. 品种管理

```python
# 获取所有品种
symbols = mt5_client.get_symbols()

# 获取特定品种信息
symbol_info = mt5_client.get_symbol_info("EURUSD")
print(f"买价: {symbol_info['ask']}")
print(f"卖价: {symbol_info['bid']}")
print(f"点值: {symbol_info['point']}")
print(f"点差: {symbol_info['spread']}")
print(f"最小交易量: {symbol_info['volume_min']}")
print(f"最大交易量: {symbol_info['volume_max']}")

# 启用品种（在市场观察窗口中显示）
mt5_client.symbol_select("EURUSD", True)

# 禁用品种
mt5_client.symbol_select("EURUSD", False)

# 获取实时报价（tick数据）
tick = mt5_client.get_symbol_info_tick("EURUSD")
if tick:
    print(f"买价: {tick['bid']}")
    print(f"卖价: {tick['ask']}")
    print(f"时间: {tick['time']}")
```

### 4. 交易操作

#### 市价买入

```python
import MetaTrader5 as mt5

# 创建市价买入请求
buy_request = mt5_client.create_market_buy_request(
    symbol="EURUSD",
    volume=0.1,           # 交易量（手数）
    sl=1.0800,           # 止损价格（可选）
    tp=1.0900,           # 止盈价格（可选）
    deviation=20,        # 最大价格偏差（点数）
    magic=123456,        # EA 标识号
    comment="买入订单"    # 订单注释
)

# 设置成交类型（根据品种支持的类型）
symbol_info = mt5_client.get_symbol_info("EURUSD")
filling_mode = symbol_info.get("filling_mode", 0)
if filling_mode & 2:
    buy_request["type_filling"] = mt5.ORDER_FILLING_IOC
elif filling_mode & 1:
    buy_request["type_filling"] = mt5.ORDER_FILLING_FOK

# 检查订单
check_result = mt5_client.order_check(buy_request)
if check_result and (check_result["retcode"] == 0 or check_result["retcode"] == 10009):
    logger.info(f"订单检查通过，所需保证金: {check_result['margin']}")

    # 发送订单
    result = mt5_client.order_send(buy_request)
    if result and result["retcode"] == 10009:
        logger.info(f"开仓成功! 订单号: {result['order']}")
    else:
        logger.error("开仓失败")
```

#### 市价卖出/平仓

```python
# 创建市价卖出请求（开空仓）
sell_request = mt5_client.create_market_sell_request(
    symbol="EURUSD",
    volume=0.1,
    sl=1.0900,
    tp=1.0800,
    deviation=20,
    magic=123456,
    comment="卖出订单"
)

# 平仓（指定持仓号）
close_request = mt5_client.create_market_sell_request(
    symbol="EURUSD",
    volume=0.1,
    position=position_id,  # 指定持仓号用于平仓
    comment="平仓"
)

# 发送订单
result = mt5_client.order_send(close_request)
if result and result["retcode"] == 10009:
    logger.info("平仓成功!")
```

#### 限价挂单

```python
# 限价买入挂单
limit_buy_request = mt5_client.create_limit_buy_request(
    symbol="EURUSD",
    volume=0.1,
    price=1.0850,        # 挂单价格
    sl=1.0800,
    tp=1.0900,
    magic=123456,
    comment="限价买入"
)

result = mt5_client.order_send(limit_buy_request)

# 限价卖出挂单
limit_sell_request = mt5_client.create_limit_sell_request(
    symbol="EURUSD",
    volume=0.1,
    price=1.0950,
    sl=1.1000,
    tp=1.0900,
    magic=123456,
    comment="限价卖出"
)

result = mt5_client.order_send(limit_sell_request)
```

### 5. 持仓和挂单查询

```python
# 获取所有持仓
positions = mt5_client.get_positions()
if positions:
    for pos in positions:
        print(f"品种: {pos['symbol']}, 类型: {pos['type']}, 手数: {pos['volume']}, 盈亏: {pos['profit']}")

# 获取指定品种的持仓
positions = mt5_client.get_positions(symbol="EURUSD")

# 获取指定持仓
position = mt5_client.get_positions(ticket=position_id)

# 获取所有挂单
orders = mt5_client.get_orders()
if orders:
    for order in orders:
        print(f"品种: {order['symbol']}, 类型: {order['type']}, 价格: {order['price_open']}")

# 获取指定品种的挂单
orders = mt5_client.get_orders(symbol="EURUSD")
```

### 6. 多账户管理

```python
from utils import MT5AccountManager

# 创建账户管理器（单例模式）
manager = MT5AccountManager()

# 添加账户
manager.add_account(
    name="账户1",
    login=12345678,
    password="password1",
    server="Server1",
    auto_connect=True
)

manager.add_account(
    name="账户2",
    login=87654321,
    password="password2",
    server="Server2",
    auto_connect=True
)

# 列出所有账户
accounts = manager.list_accounts()
print(f"账户列表: {accounts}")

# 切换账户
manager.switch_account("账户2")

# 获取当前账户
current = manager.get_current_account()
if current:
    account_info = current.get_account_info()
    print(f"当前账户余额: {account_info['balance']}")

# 在所有账户上执行相同操作
results = manager.execute_on_all("get_account_info")
for name, info in results.items():
    if "error" not in info:
        print(f"{name}: 余额 {info['balance']}")

# 断开所有账户
manager.shutdown_all()

# 使用上下文管理器
with MT5AccountManager() as manager:
    manager.add_account("账户1", 12345678, "pwd", "server")
    # ... 执行操作 ...
    # 退出时自动断开所有连接
```

### 7. 日志管理

```python
from utils import logger

# 基本日志输出
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 设置日志级别
logger.set_level('DEBUG')  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 添加文件日志
logger.add_file_handler('mt5_trading.log', level='INFO')
```

## 完整示例

查看 `main.py` 文件获取完整的黄金交易示例，包括：

- 连接 MT5 终端
- 获取品种信息
- 创建市价买入订单
- 设置止损止盈
- 订单检查和发送
- 自动平仓

```bash
python main.py
```

## 项目结构

```
codes/
├── main.py                          # 示例代码
├── utils/                           # 核心库
│   ├── __init__.py                 # 包初始化
│   ├── emt5.py                     # EMT5 主类
│   ├── logger.py                   # 日志模块
│   ├── core/                       # 核心功能
│   │   ├── __init__.py
│   │   └── connection.py           # 连接管理
│   ├── info/                       # 信息查询
│   │   ├── __init__.py
│   │   ├── account.py              # 账户信息
│   │   └── symbol.py               # 品种信息
│   ├── trade/                      # 交易操作
│   │   ├── __init__.py
│   │   └── order.py                # 订单管理
│   └── manager/                    # 管理器
│       ├── __init__.py
│       └── account_manager.py      # 多账户管理器
└── README.md                        # 项目文档
```

## API 文档

### EMT5 类

主要封装类，整合了所有功能模块。

#### 连接管理方法

- `initialize(path, login, password, server, timeout, portable)` - 连接 MT5 终端
- `shutdown()` - 断开连接
- `is_connected()` - 检查连接状态
- `get_terminal_info()` - 获取终端信息
- `get_version()` - 获取版本信息

#### 账户信息方法

- `get_account_info()` - 获取账户信息（余额、权益、保证金等）

#### 品种管理方法

- `get_symbols(group)` - 获取所有品种
- `get_symbol_info(symbol)` - 获取品种详细信息
- `symbol_select(symbol, enable)` - 启用/禁用品种
- `get_symbol_info_tick(symbol)` - 获取实时报价（tick数据）

#### 交易操作方法

- `order_send(request)` - 发送交易请求
- `order_check(request)` - 检查订单有效性
- `create_market_buy_request(...)` - 创建市价买入请求
- `create_market_sell_request(...)` - 创建市价卖出请求
- `create_limit_buy_request(...)` - 创建限价买入请求
- `create_limit_sell_request(...)` - 创建限价卖出请求

#### 持仓和挂单查询方法

- `get_positions(symbol, ticket, group)` - 获取持仓列表
- `get_orders(symbol, ticket, group)` - 获取挂单列表

### MT5AccountManager 类

多账户管理器（单例模式），用于管理多个 MT5 账户。

#### 账户管理方法

- `add_account(name, login, password, server, path, auto_connect)` - 添加账户
- `remove_account(name)` - 移除账户
- `switch_account(name)` - 切换当前账户
- `get_account(name)` - 获取账户实例
- `get_current_account()` - 获取当前账户实例
- `list_accounts()` - 列出所有账户
- `execute_on_all(func_name, *args, **kwargs)` - 在所有账户上执行相同操作
- `shutdown_all()` - 断开所有账户连接

## 常见返回码

### 交易返回码

- `10009` - TRADE_RETCODE_DONE - 请求已完成
- `10004` - TRADE_RETCODE_REQUOTE - 重新报价
- `10006` - TRADE_RETCODE_REJECT - 请求被拒绝
- `10013` - TRADE_RETCODE_INVALID_PRICE - 价格无效
- `10014` - TRADE_RETCODE_INVALID_STOPS - 止损/止盈无效
- `10016` - TRADE_RETCODE_MARKET_CLOSED - 市场关闭
- `10019` - TRADE_RETCODE_NO_MONEY - 资金不足

## 交易风险

- 本库仅供学习和研究使用
- 外汇交易存在高风险，可能导致资金损失
- 请在模拟账户上充分测试后再使用实盘账户
- 使用本库进行交易的风险由使用者自行承担

## 最佳实践

1. **始终检查返回值** - 所有操作都可能失败，务必检查返回结果
2. **使用订单检查** - 发送订单前使用 `order_check()` 验证
3. **设置止损止盈** - 控制风险，保护资金
4. **记录日志** - 使用日志功能记录所有交易操作
5. **异常处理** - 使用 try-except 捕获可能的异常
6. **资源管理** - 使用完毕后及时调用 `shutdown()` 或使用上下文管理器
7. **多账户管理** - 使用 MT5AccountManager 管理多个账户，避免重复连接

## 常见问题

### 1. 连接失败怎么办？

- 确认 MT5 终端已安装并可以正常运行
- 检查账号、密码、服务器名称是否正确
- 确认 MT5 终端路径是否正确
- 查看日志输出的错误代码

### 2. 订单发送失败？

- 使用 `order_check()` 检查订单参数
- 确认账户有足够的保证金
- 检查品种是否已启用（`symbol_select`）
- 确认交易量符合品种的最小/最大限制
- 检查 `type_filling` 是否符合品种要求

### 3. 如何获取历史数据？

本库目前专注于交易操作，历史数据获取可以直接使用 MetaTrader5 包的相关函数：

```python
import MetaTrader5 as mt5
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 100)
```

### 4. 如何管理多个账户？

使用 `MT5AccountManager` 类可以方便地管理多个账户：

```python
from utils import MT5AccountManager

manager = MT5AccountManager()
manager.add_account("账户1", login1, pwd1, server1)
manager.add_account("账户2", login2, pwd2, server2)
manager.switch_account("账户2")
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[liukersun@gmail.com]

---

**免责声明**：本软件按"原样"提供，不提供任何明示或暗示的保证。使用本软件进行交易的所有风险由使用者自行承担。
