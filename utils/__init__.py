"""
EMT5 - MetaTrader 5 Python 封装库

一个简洁易用的 MetaTrader 5 Python 封装库
"""

from .emt5 import EMT5
from .core import MT5Connection, require_connection, retry, catch_exceptions
from .info import MT5Account, MT5Symbol, MT5History, MT5Position
from .trade import MT5Executor, MT5Calculator, OrderRequestBuilder
from .manager import MT5AccountManager
from .logger import logger, MT5Logger
from .exceptions import (
    MT5Error,
    MT5ConnectionError,
    MT5OrderError,
    MT5SymbolError,
    MT5ValidationError,
    MT5AccountError,
    MT5TimeoutError,
)

__version__ = "2.0.0"
__author__ = "EMT5 Team"

__all__ = [
    # 主类
    "EMT5",
    # 核心
    "MT5Connection",
    "require_connection",
    "retry",
    "catch_exceptions",
    # 信息查询
    "MT5Account",
    "MT5Symbol",
    "MT5History",
    "MT5Position",
    # 交易
    "MT5Executor",
    "MT5Calculator",
    "OrderRequestBuilder",
    # 管理
    "MT5AccountManager",
    # 日志
    "logger",
    "MT5Logger",
    # 异常
    "MT5Error",
    "MT5ConnectionError",
    "MT5OrderError",
    "MT5SymbolError",
    "MT5ValidationError",
    "MT5AccountError",
    "MT5TimeoutError",
]
