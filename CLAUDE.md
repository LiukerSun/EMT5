# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

EMT5 是一个 MetaTrader 5 (MT5) 的 Python 封装库，提供简洁易用的接口来与 MT5 终端交互。项目采用模块化设计，整合了连接管理、账户信息查询、品种管理、交易操作和多账户管理等功能。

**版本**: 2.0.0

**核心依赖：**
- `metatrader5==5.0.5509` - MT5 官方 Python SDK
- `numpy==2.4.1` - 数值计算库

## 项目架构

### 目录结构

```
utils/
├── emt5.py                    # 主入口类（精简版）
├── core/
│   ├── __init__.py
│   ├── connection.py          # MT5 连接管理
│   ├── decorators.py          # 通用装饰器（连接检查、重试等）
│   └── converters.py          # 数据转换工具
├── info/
│   ├── __init__.py
│   ├── account.py             # 账户信息查询
│   ├── symbol.py              # 品种信息管理
│   ├── history.py             # 历史数据查询
│   └── position.py            # 持仓和挂单查询
├── trade/
│   ├── __init__.py
│   ├── request_builder.py     # 订单请求构建器（Builder 模式）
│   ├── executor.py            # 订单执行器
│   └── calculator.py          # 交易计算工具
├── manager/
│   ├── __init__.py
│   └── account_manager.py     # 多账户管理（单例模式）
├── exceptions.py              # 自定义异常
├── logger.py                  # 日志系统（单例模式）
└── __init__.py                # 包导出
```

### 核心设计模式

1. **Builder 模式** - `OrderRequestBuilder` 提供链式调用构建订单
2. **单例模式** - `MT5Logger`、`MT5AccountManager`
3. **装饰器模式** - `@require_connection`、`@retry`、`@catch_exceptions`
4. **上下文管理器** - `EMT5` 支持 `with` 语句

### 关键类关系

```
EMT5 (主类)
├── MT5Connection (连接管理)
├── MT5Account (账户信息)
├── MT5Symbol (品种管理)
├── MT5Position (持仓/挂单查询)
├── MT5History (历史数据)
├── MT5Calculator (交易计算)
├── MT5Executor (订单执行)
└── order() -> OrderRequestBuilder (订单构建器)

MT5AccountManager (单例) - 管理多个 EMT5 实例
```

## 常用开发命令

### 环境设置

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 语法检查

```bash
python -m py_compile utils/emt5.py
python -c "from utils import EMT5, MT5Position, OrderRequestBuilder"
```

## API 使用示例

### 基本连接

```python
from utils import EMT5

mt5 = EMT5()
mt5.initialize()

# 获取账户信息
account = mt5.account.get_account_info()
print(f"余额: {account['balance']}")

mt5.shutdown()
```

### 链式调用下单（推荐）

```python
# 市价买入
result = (mt5.order("EURUSD")
    .market_buy(0.1)
    .with_sl(1.0950)
    .with_tp(1.1050)
    .send())

# 限价挂单
result = (mt5.order("GOLD")
    .limit_buy(0.01, 1950.00)
    .with_sl(1940.00)
    .with_tp(1970.00)
    .send())

# 只构建不发送
request = mt5.order("EURUSD").market_buy(0.1).build()

# 检查订单
check = mt5.order("EURUSD").market_buy(0.1).check()
```

### 直接访问子模块

```python
# 持仓查询
positions = mt5.position.get_positions()
positions = mt5.position.get_positions(symbol="EURUSD")

# 挂单查询
orders = mt5.position.get_orders()

# 历史数据
import MetaTrader5 as mt5_api
bars = mt5.history.get_bars("EURUSD", mt5_api.TIMEFRAME_H1, start_pos=0, count=100)

# 交易计算
margin = mt5.calculator.calc_margin("EURUSD", 0.1)
profit = mt5.calculator.calc_profit("EURUSD", 0.1, 1.1000, 1.1050)
```

### 订单执行器

```python
# 修改止损止盈
mt5.executor.modify(ticket=123456, sl=1.0950, tp=1.1050)

# 平仓
mt5.executor.close_position(ticket=123456)

# 取消挂单
mt5.executor.cancel(ticket=123456)
```

## 重要架构特性

### 1. 装饰器 (utils/core/decorators.py)

- `@require_connection` - 自动检查连接状态
- `@retry(max_attempts=3)` - 自动重试
- `@catch_exceptions(default_return=None)` - 异常捕获
- `@log_execution()` - 执行日志

### 2. 数据转换 (utils/core/converters.py)

- `to_dict()` - namedtuple 转字典
- `add_datetime_fields()` - 添加时区感知时间
- `convert_bars_to_dict()` - K线数据转换
- `convert_positions_to_dict()` - 持仓数据转换

### 3. 异常类 (utils/exceptions.py)

- `MT5ConnectionError` - 连接异常
- `MT5OrderError` - 订单异常
- `MT5SymbolError` - 品种异常
- `MT5ValidationError` - 验证异常

## 代码风格

- 类名：PascalCase（如 `MT5Connection`）
- 方法名：snake_case（如 `get_account_info`）
- 私有属性：前缀 `_`（如 `_connection`）
- 所有公共方法都有中文文档字符串

## Web 框架集成

```python
# Django 中使用（keep_alive=True 避免意外断开）
mt5 = EMT5(keep_alive=True)
mt5.initialize()
```

## 关键文件位置

- 主入口：`utils/emt5.py:14` - EMT5 类
- 订单构建器：`utils/trade/request_builder.py:14` - OrderRequestBuilder 类
- 订单执行器：`utils/trade/executor.py:16` - MT5Executor 类
- 持仓管理：`utils/info/position.py:14` - MT5Position 类
- 装饰器：`utils/core/decorators.py` - require_connection 等
