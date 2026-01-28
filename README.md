# EMT5 - MetaTrader 5 Python 封装库

一个简洁易用的 MetaTrader 5 Python 封装库，提供流畅的 API 来与 MT5 终端交互。

## 特性

- **链式调用** - Builder 模式构建订单，API 简洁流畅
- **模块化设计** - 职责分离，代码结构清晰
- **Django 友好** - 时区感知时间字段，Web 框架集成支持
- **多账户管理** - 支持同时管理多个交易账户
- **完善的异常处理** - 自定义异常类和装饰器

## 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/EMT5.git
cd EMT5

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 依赖

- Python 3.8+
- MetaTrader 5 终端（需要安装并运行）
- metatrader5==5.0.5509
- numpy==2.4.1

## 快速开始

### 基本连接

```python
from utils import EMT5

mt5 = EMT5()
mt5.initialize()

# 获取账户信息
account = mt5.account.get_account_info()
print(f"账户: {account['login']}")
print(f"余额: {account['balance']} {account['currency']}")

mt5.shutdown()
```

### 使用上下文管理器

```python
with EMT5() as mt5:
    mt5.initialize()
    account = mt5.account.get_account_info()
    print(f"余额: {account['balance']}")
# 自动断开连接
```

### 指定账户登录

```python
mt5 = EMT5()
mt5.initialize(
    login=12345678,
    password="your_password",
    server="XMGlobal-MT5 9"
)
```

## 交易操作

### 链式调用下单（推荐）

```python
# 市价买入
result = (mt5.order("EURUSD")
    .market_buy(0.1)
    .with_sl(1.0950)
    .with_tp(1.1050)
    .send())

if result and result['retcode'] == 10009:
    print(f"交易成功！订单号: {result['order']}")

# 市价卖出
result = (mt5.order("EURUSD")
    .market_sell(0.1)
    .with_sl(1.1050)
    .with_tp(1.0950)
    .send())

# 限价买入挂单
result = (mt5.order("GOLD")
    .limit_buy(0.01, 1950.00)
    .with_sl(1940.00)
    .with_tp(1970.00)
    .with_comment("黄金回调买入")
    .send())

# 止损卖出挂单
result = (mt5.order("EURUSD")
    .stop_sell(0.1, 1.0900)
    .send())
```

### 检查订单

```python
# 发送前检查订单有效性
check = (mt5.order("EURUSD")
    .market_buy(0.1)
    .check())

if check and check['retcode'] in [0, 10009]:
    print(f"检查通过，所需保证金: {check['margin']}")
```

### 只构建不发送

```python
# 构建请求字典
request = (mt5.order("EURUSD")
    .market_buy(0.1)
    .with_sl(1.0950)
    .build())

# 稍后发送
result = mt5.executor.send(request)
```

## 持仓和挂单管理

### 查询持仓

```python
# 获取所有持仓
positions = mt5.position.get_positions()

# 按品种过滤
positions = mt5.position.get_positions(symbol="EURUSD")

# 按票据号查询
position = mt5.position.get_position_by_ticket(123456)

# 获取持仓总数
total = mt5.position.get_positions_total()
```

### 查询挂单

```python
# 获取所有挂单
orders = mt5.position.get_orders()

# 按品种过滤
orders = mt5.position.get_orders(symbol="GOLD")
```

### 平仓和修改

```python
# 平仓
result = mt5.executor.close_position(ticket=123456)

# 部分平仓
result = mt5.executor.close_position(ticket=123456, volume=0.05)

# 修改止损止盈
result = mt5.executor.modify(ticket=123456, sl=1.0950, tp=1.1050)

# 取消挂单
result = mt5.executor.cancel(ticket=789012)
```

## 账户和品种信息

### 账户信息

```python
account = mt5.account.get_account_info()
print(f"账户号: {account['login']}")
print(f"余额: {account['balance']}")
print(f"净值: {account['equity']}")
print(f"可用保证金: {account['margin_free']}")
print(f"杠杆: {account['leverage']}")
```

### 品种信息

```python
# 获取品种详情
info = mt5.symbol.get_symbol_info("EURUSD")
print(f"点差: {info['spread']}")
print(f"最小交易量: {info['volume_min']}")

# 获取实时报价
tick = mt5.symbol.get_symbol_info_tick("EURUSD")
print(f"买价: {tick['bid']}, 卖价: {tick['ask']}")

# 启用品种
mt5.symbol.symbol_select("GOLD", True)

# 获取所有品种名称
symbols = mt5.symbol.get_symbol_names()
```

## 历史数据

```python
import MetaTrader5 as mt5_api
from datetime import datetime, timezone

# 获取最近 100 根 H1 K线
bars = mt5.history.get_bars(
    "EURUSD",
    mt5_api.TIMEFRAME_H1,
    start_pos=0,
    count=100
)

# 获取指定时间范围的 K线
start = datetime(2024, 1, 1, tzinfo=timezone.utc)
end = datetime(2024, 1, 31, tzinfo=timezone.utc)
bars = mt5.history.get_bars(
    "EURUSD",
    mt5_api.TIMEFRAME_D1,
    date_from=start,
    date_to=end
)

# 获取 Tick 数据
ticks = mt5.history.get_ticks(
    "EURUSD",
    date_from=start,
    count=1000
)

# 获取历史订单
result = mt5.history.get_history_orders(start, end)
print(f"共有 {result['total']} 个历史订单")

# 获取历史成交
result = mt5.history.get_history_deals(start, end)
total_profit = sum(deal['profit'] for deal in result['deals'])
print(f"总盈亏: {total_profit}")
```

## 交易计算

```python
# 计算所需保证金
margin = mt5.calculator.calc_margin("EURUSD", 0.1)
print(f"所需保证金: {margin}")

# 计算预期盈利
profit = mt5.calculator.calc_profit(
    "EURUSD", 0.1,
    price_open=1.1000,
    price_close=1.1050,
    action='buy'
)
print(f"预期盈利: {profit}")

# 计算风险回报比
result = mt5.calculator.calc_risk_reward(
    symbol="EURUSD",
    volume=0.1,
    entry_price=1.1000,
    sl_price=1.0950,
    tp_price=1.1100,
    action='buy'
)
print(f"风险回报比: 1:{result['risk_reward_ratio']:.2f}")

# 根据风险金额计算仓位
volume = mt5.calculator.calc_position_size(
    symbol="EURUSD",
    risk_amount=100,  # 愿意承担 100 USD 风险
    entry_price=1.1000,
    sl_price=1.0950,
    action='buy'
)
print(f"建议交易量: {volume} 手")
```

## 多账户管理

```python
from utils import MT5AccountManager

manager = MT5AccountManager()

# 添加账户
manager.add_account(
    name="account1",
    login=12345678,
    password="pwd1",
    server="Server1"
)
manager.add_account(
    name="account2",
    login=87654321,
    password="pwd2",
    server="Server2"
)

# 切换账户
manager.switch_account("account1")

# 获取当前账户
mt5 = manager.get_current_account()
account = mt5.account.get_account_info()

# 在所有账户上执行操作
results = manager.execute_on_all("account.get_account_info")
for name, info in results.items():
    print(f"{name}: 余额 {info['balance']}")

# 断开所有连接
manager.shutdown_all()
```

## Django 集成

```python
# settings.py 中配置日志
LOGGING = {
    'loggers': {
        'MT5': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    },
}

# views.py 中使用
from utils import EMT5

# keep_alive=True 避免请求结束时断开连接
mt5 = EMT5(keep_alive=True)
mt5.initialize()

def get_account_view(request):
    account = mt5.account.get_account_info()
    return JsonResponse(account)
```

## 项目结构

```
utils/
├── emt5.py                    # 主入口类
├── core/
│   ├── connection.py          # 连接管理
│   ├── decorators.py          # 通用装饰器
│   └── converters.py          # 数据转换工具
├── info/
│   ├── account.py             # 账户信息
│   ├── symbol.py              # 品种信息
│   ├── history.py             # 历史数据
│   └── position.py            # 持仓和挂单
├── trade/
│   ├── request_builder.py     # 订单构建器
│   ├── executor.py            # 订单执行器
│   └── calculator.py          # 交易计算
├── manager/
│   └── account_manager.py     # 多账户管理
├── exceptions.py              # 自定义异常
└── logger.py                  # 日志系统
```

## 异常处理

```python
from utils import (
    MT5ConnectionError,
    MT5OrderError,
    MT5SymbolError,
    MT5ValidationError
)

try:
    mt5.initialize()
except MT5ConnectionError as e:
    print(f"连接失败: {e}")

try:
    result = mt5.order("EURUSD").market_buy(0.1).send()
except MT5OrderError as e:
    print(f"订单失败: {e}")
except MT5ValidationError as e:
    print(f"验证失败: {e}")
```

## 装饰器

```python
from utils import require_connection, retry, catch_exceptions

# 连接检查装饰器
@require_connection
def my_function(self):
    # 自动检查连接状态
    pass

# 重试装饰器
@retry(max_attempts=3, delay=1.0)
def unstable_operation():
    pass

# 异常捕获装饰器
@catch_exceptions(default_return=None)
def risky_operation():
    pass
```

## 常见返回码

| 返回码 | 说明 |
|--------|------|
| 10009 | TRADE_RETCODE_DONE - 请求已完成 |
| 10004 | TRADE_RETCODE_REQUOTE - 重新报价 |
| 10006 | TRADE_RETCODE_REJECT - 请求被拒绝 |
| 10013 | TRADE_RETCODE_INVALID_PRICE - 价格无效 |
| 10014 | TRADE_RETCODE_INVALID_STOPS - 止损/止盈无效 |
| 10016 | TRADE_RETCODE_MARKET_CLOSED - 市场关闭 |
| 10019 | TRADE_RETCODE_NO_MONEY - 资金不足 |

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。
