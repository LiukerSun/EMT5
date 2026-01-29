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

## API 认证

项目提供基于 Token 的 API 认证系统。Token 只能通过命令行生成，确保安全性。

### 初始化数据库

```bash
# 创建迁移文件
python manage.py makemigrations authentication

# 执行迁移
python manage.py migrate
```

### Token 管理命令

```bash
# 创建 Token（永不过期）
python manage.py token create <name>

# 创建 Token（指定过期天数）
python manage.py token create <name> --expires 30

# 创建 Token（带描述）
python manage.py token create <name> --expires 30 --description "用于测试"

# 列出所有 Token
python manage.py token list

# 查看 Token 详情
python manage.py token info <token_id>

# 撤销 Token
python manage.py token revoke <token_id>
```

### 示例

```bash
# 创建一个 30 天后过期的 API Token
$ python manage.py token create my-api-token --expires 30

============================================================
Token 创建成功！
============================================================

ID:       1
名称:     my-api-token
创建时间: 2024-01-28 12:00:00
过期时间: 2024-02-27 12:00:00

------------------------------------------------------------
请妥善保存以下 Token，它只会显示一次：
------------------------------------------------------------

4bad13e23fab864a01ac1fd794fb608acab1447e68e378b31b9523058419cc90
============================================================
```

### API 调用

在请求头中携带 Token：

```bash
# 使用 Bearer 格式
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/xxx

# 或使用 Token 格式
curl -H "Authorization: Token <your-token>" http://localhost:8000/api/xxx
```

### 豁免路径

以下路径不需要 Token 认证：
- `/admin/` - Django 管理后台
- `/api/docs/` - Swagger 文档
- `/api/redoc/` - ReDoc 文档
- `/api/v1/health/` - 健康检查端点

### 在视图中获取 Token 信息

```python
def my_view(request):
    # 中间件会将验证通过的 Token 附加到 request 对象
    token = request.api_token
    print(f"请求来自: {token.name}")
    print(f"Token 创建时间: {token.created_at}")
```

## API 文档

项目使用 drf-spectacular 自动生成 OpenAPI 3.0 文档。

### 访问文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### API 端点概览

| 分类 | 端点 | 方法 | 说明 | 需登录 |
|------|------|------|------|--------|
| Health | `/api/v1/health/` | GET | 健康检查 | 否 |
| Account | `/api/v1/account/login/` | POST | 登录交易账户 | 否 |
| Account | `/api/v1/account/` | GET | 获取账户信息 | 是 |
| Symbol | `/api/v1/symbols/` | GET | 获取品种列表 | 否 |
| Symbol | `/api/v1/symbols/{symbol}/` | GET | 获取品种详情 | 否 |
| Symbol | `/api/v1/symbols/{symbol}/tick/` | GET | 获取实时报价 | 否 |
| Position | `/api/v1/positions/` | GET | 获取持仓列表 | 是 |
| Position | `/api/v1/positions/{ticket}/` | GET | 获取持仓详情 | 是 |
| Position | `/api/v1/orders/` | GET | 获取挂单列表 | 是 |
| Trade | `/api/v1/trade/buy/` | POST | 市价买入 | 是 |
| Trade | `/api/v1/trade/sell/` | POST | 市价卖出 | 是 |
| Trade | `/api/v1/trade/close/` | POST | 平仓 | 是 |
| Trade | `/api/v1/trade/modify/` | POST | 修改止损止盈 | 是 |
| History | `/api/v1/history/bars/` | GET | 获取K线数据 | 是 |
| History | `/api/v1/history/deals/` | GET | 获取历史成交 | 是 |
| Calc | `/api/v1/calc/margin/` | GET | 计算保证金 | 是 |
| Calc | `/api/v1/calc/profit/` | GET | 计算盈亏 | 是 |

### 登录流程

1. 调用健康检查确认 MT5 终端已连接
2. 调用登录接口登录交易账户
3. 登录成功后可调用其他需要登录的接口

```bash
# 1. 检查状态
curl http://localhost:8000/api/v1/health/

# 2. 登录账户
curl -X POST http://localhost:8000/api/v1/account/login/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"login": 12345678, "password": "your_password", "server": "XMGlobal-MT5"}'

# 3. 获取账户信息
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/v1/account/
```

### 启动服务

```bash
# 开发服务器
python manage.py runserver

# 指定端口
python manage.py runserver 0.0.0.0:8080
```

## 项目结构

```
EMT5/
├── utils/                         # MT5 封装库
│   ├── emt5.py                    # 主入口类
│   ├── core/
│   │   ├── connection.py          # 连接管理
│   │   ├── decorators.py          # 通用装饰器
│   │   └── converters.py          # 数据转换工具
│   ├── info/
│   │   ├── account.py             # 账户信息
│   │   ├── symbol.py              # 品种信息
│   │   ├── history.py             # 历史数据
│   │   └── position.py            # 持仓和挂单
│   ├── trade/
│   │   ├── request_builder.py     # 订单构建器
│   │   ├── executor.py            # 订单执行器
│   │   └── calculator.py          # 交易计算
│   ├── manager/
│   │   └── account_manager.py     # 多账户管理
│   ├── exceptions.py              # 自定义异常
│   └── logger.py                  # 日志系统
├── api_server/                    # Django 项目配置
│   ├── settings.py                # Django 设置
│   ├── urls.py                    # URL 路由
│   ├── api_urls.py                # API 路由
│   ├── views.py                   # API 视图
│   ├── serializers.py             # 序列化器
│   ├── wsgi.py
│   └── asgi.py
├── authentication/                # API 认证模块
│   ├── models.py                  # APIToken 模型
│   ├── middleware.py              # Token 认证中间件
│   └── management/commands/
│       └── token.py               # Token 管理命令
└── manage.py
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
