# EMT5

**MetaTrader 5 Python 封装库 / MetaTrader 5 Python Wrapper Library**

EMT5 提供简洁易用的 Python 接口来与 MetaTrader 5 终端交互，支持链式调用下单、模块化查询和多账户管理。

> A clean, modular Python wrapper for MetaTrader 5 with fluent order building, comprehensive querying, and multi-account management.

## 特性 / Features

- **链式调用下单 / Fluent Order Builder** — Builder 模式构建订单，一行代码完成下单
- **模块化设计 / Modular Architecture** — 连接、账户、品种、持仓、历史、交易各司其职
- **多账户管理 / Multi-Account** — 单例模式管理多个 MT5 账户，线程安全切换
- **风险计算 / Risk Calculator** — 保证金、盈亏、风险回报比、仓位计算
- **自动重试 / Auto Retry** — 连接失败自动重试，IPC 失败自动启动终端
- **时区感知 / Timezone Aware** — 所有时间字段自动转换为 UTC timezone-aware datetime
- **装饰器工具 / Decorators** — `@require_connection`、`@retry`、`@catch_exceptions` 等开箱即用
- **上下文管理器 / Context Manager** — 支持 `with` 语句自动管理连接生命周期

## 安装 / Installation

### 环境要求 / Requirements

- Python 3.8+
- Windows（MetaTrader 5 仅支持 Windows / MT5 is Windows-only）
- MetaTrader 5 终端已安装 / MetaTrader 5 terminal installed

### 安装依赖 / Install Dependencies

```bash
pip install MetaTrader5==5.0.5509
pip install numpy==2.4.1
```

## 快速开始 / Quick Start

### 基本连接 / Basic Connection

```python
from utils import EMT5

mt5 = EMT5()
mt5.initialize()

# 获取账户信息 / Get account info
account = mt5.account.get_account_info()
print(f"余额 / Balance: {account['balance']}")

mt5.shutdown()
```

### 使用上下文管理器 / Using Context Manager

```python
with EMT5() as mt5:
    mt5.initialize()
    account = mt5.account.get_account_info()
    print(f"净值 / Equity: {account['equity']}")
# 自动断开连接 / Auto disconnect
```

### 指定账户连接 / Connect with Credentials

```python
mt5 = EMT5()
mt5.initialize(
    login=12345678,
    password="your_password",
    server="YourBroker-MT5"
)
```

### 链式调用下单 / Fluent Order Building

```python
# 市价买入 / Market buy
result = (mt5.order("EURUSD")
    .market_buy(0.1)
    .with_sl(1.0950)
    .with_tp(1.1050)
    .send())

# 限价挂单 / Limit order
result = (mt5.order("GOLD")
    .limit_buy(0.01, 1950.00)
    .with_sl(1940.00)
    .with_tp(1970.00)
    .send())

# 只构建不发送 / Build without sending
request = mt5.order("EURUSD").market_buy(0.1).build()

# 检查订单 / Check order
check = mt5.order("EURUSD").market_buy(0.1).check()
```

### 查询持仓 / Query Positions

```python
# 所有持仓 / All positions
positions = mt5.position.get_positions()

# 按品种过滤 / Filter by symbol
positions = mt5.position.get_positions(symbol="EURUSD")

# 按票据号查询 / By ticket
position = mt5.position.get_position_by_ticket(123456)

# 挂单查询 / Pending orders
orders = mt5.position.get_orders()
```

## API 概览 / API Overview

### EMT5 主类 / Main Class

| 方法 / Method | 说明 / Description |
|---|---|
| `initialize(path, login, password, server)` | 连接 MT5 终端 / Connect to MT5 |
| `shutdown()` | 断开连接 / Disconnect |
| `login(login, password, server)` | 切换账户 / Switch account |
| `order(symbol)` | 创建订单构建器 / Create order builder |
| `is_connected()` | 检查连接状态 / Check connection |

### 子模块访问 / Sub-modules

| 属性 / Property | 类 / Class | 功能 / Purpose |
|---|---|---|
| `mt5.account` | `MT5Account` | 账户信息 / Account info |
| `mt5.symbol` | `MT5Symbol` | 品种管理 / Symbol management |
| `mt5.position` | `MT5Position` | 持仓/挂单查询 / Positions & orders |
| `mt5.history` | `MT5History` | 历史数据 / Historical data |
| `mt5.calculator` | `MT5Calculator` | 交易计算 / Trade calculations |
| `mt5.executor` | `MT5Executor` | 订单执行 / Order execution |

### OrderRequestBuilder 链式方法 / Chain Methods

```
mt5.order("EURUSD")
    .market_buy(volume)          # 市价买入
    .market_sell(volume)         # 市价卖出
    .limit_buy(volume, price)    # 限价买入
    .limit_sell(volume, price)   # 限价卖出
    .stop_buy(volume, price)     # 止损买入
    .stop_sell(volume, price)    # 止损卖出
    .with_sl(price)              # 设置止损
    .with_tp(price)              # 设置止盈
    .with_sl_tp(sl, tp)          # 同时设置止损止盈
    .with_deviation(points)      # 最大偏差
    .with_magic(magic)           # EA 标识号
    .with_comment(text)          # 订单注释
    .build()                     # 构建请求字典
    .send()                      # 发送订单
    .check()                     # 检查订单
```

### MT5Executor 订单执行 / Order Execution

| 方法 / Method | 说明 / Description |
|---|---|
| `send(request)` | 发送交易请求 / Send trade request |
| `check(request)` | 检查交易请求 / Check trade request |
| `modify(ticket, sl, tp)` | 修改止损止盈 / Modify SL/TP |
| `close_position(ticket, volume)` | 平仓 / Close position |
| `cancel(ticket)` | 取消挂单 / Cancel pending order |

### MT5History 历史数据 / Historical Data

```python
import MetaTrader5 as mt5_api
from datetime import datetime, timezone

# K 线数据 / Bar data (3 种参数组合)
bars = mt5.history.get_bars("EURUSD", mt5_api.TIMEFRAME_H1, start_pos=0, count=100)
bars = mt5.history.get_bars("EURUSD", mt5_api.TIMEFRAME_D1, date_from=start, count=50)
bars = mt5.history.get_bars("EURUSD", mt5_api.TIMEFRAME_H4, date_from=start, date_to=end)

# Tick 数据 / Tick data
ticks = mt5.history.get_ticks("EURUSD", date_from=start, count=1000)

# 历史订单和成交 / Historical orders & deals
orders = mt5.history.get_history_orders(start, end)
deals = mt5.history.get_history_deals(start, end)
```

## 高级用法 / Advanced Usage

### 风险计算 / Risk Calculation

```python
# 计算保证金 / Calculate margin
margin = mt5.calculator.calc_margin("EURUSD", 0.1, action='buy')

# 计算盈亏 / Calculate profit
profit = mt5.calculator.calc_profit("EURUSD", 0.1, 1.1000, 1.1050, action='buy')

# 风险回报比 / Risk-reward ratio
result = mt5.calculator.calc_risk_reward(
    symbol="EURUSD", volume=0.1,
    entry_price=1.1000, sl_price=1.0950, tp_price=1.1100,
    action='buy'
)
print(f"风险回报比 / R:R = 1:{result['risk_reward_ratio']:.2f}")

# 根据风险金额计算仓位 / Position sizing by risk amount
volume = mt5.calculator.calc_position_size(
    symbol="EURUSD", risk_amount=100,
    entry_price=1.1000, sl_price=1.0950, action='buy'
)
```

### 多账户管理 / Multi-Account Management

```python
from utils import MT5AccountManager

manager = MT5AccountManager()  # 单例 / Singleton

# 添加账户 / Add accounts
manager.add_account("main", login=111, password="pwd1", server="Server1")
manager.add_account("demo", login=222, password="pwd2", server="Server2")

# 切换账户 / Switch account
manager.switch_account("demo")
demo = manager.get_current_account()
positions = demo.position.get_positions()

# 在所有账户上执行操作 / Execute on all accounts
results = manager.execute_on_all("account.get_account_info")

# 使用上下文管理器 / Context manager
with MT5AccountManager() as mgr:
    mgr.add_account("acc1", login=111, password="pwd", server="Srv")
    # ...
# 自动断开所有连接 / Auto disconnect all
```

### 装饰器 / Decorators

```python
from utils import require_connection, retry, catch_exceptions

@retry(max_attempts=3, delay=2.0)
def unstable_operation():
    # 自动重试 / Auto retry on failure
    pass

@catch_exceptions(default_return=None, log_error=True)
def safe_operation():
    # 异常自动捕获 / Auto catch exceptions
    pass
```

## 项目结构 / Project Structure

```
utils/
├── emt5.py                 # 主入口类 / Main entry class
├── core/
│   ├── connection.py       # 连接管理 / Connection management
│   ├── decorators.py       # 装饰器 / Decorators
│   └── converters.py       # 数据转换 / Data converters
├── info/
│   ├── account.py          # 账户信息 / Account info
│   ├── symbol.py           # 品种管理 / Symbol management
│   ├── history.py          # 历史数据 / Historical data
│   └── position.py         # 持仓/挂单 / Positions & orders
├── trade/
│   ├── request_builder.py  # 订单构建器 / Order builder
│   ├── executor.py         # 订单执行 / Order executor
│   └── calculator.py       # 交易计算 / Trade calculator
├── manager/
│   └── account_manager.py  # 多账户管理 / Multi-account manager
├── exceptions.py           # 异常定义 / Exception classes
└── logger.py               # 日志系统 / Logger
```

## 异常处理 / Exception Handling

```python
from utils import MT5ConnectionError, MT5OrderError, MT5ValidationError

try:
    mt5.initialize()
except MT5ConnectionError as e:
    print(f"连接失败 / Connection failed: {e}")

try:
    result = mt5.order("EURUSD").market_buy(0.1).send()
except MT5OrderError as e:
    print(f"下单失败 / Order failed: {e} (code: {e.error_code})")
except MT5ValidationError as e:
    print(f"验证失败 / Validation failed: {e}")
```

## License

MIT
