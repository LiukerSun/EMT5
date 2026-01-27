"""
EMT5 - MetaTrader 5 Python 封装库

一个简洁易用的 MetaTrader 5 Python 封装库
"""

from .emt5 import EMT5
from .core import MT5Connection
from .info import MT5Account, MT5Symbol
from .trade import MT5Order
from .manager import MT5AccountManager
from .logger import logger, MT5Logger
from .exceptions import (
    MT5Error,
    MT5ConnectionError,
    MT5OrderError,
    MT5SymbolError,
    MT5ValidationError,
)

__version__ = "1.0.0"
__author__ = "EMT5 Team"

__all__ = [
    "EMT5",
    "MT5Connection",
    "MT5Account",
    "MT5Symbol",
    "MT5Order",
    "MT5AccountManager",
    "logger",
    "MT5Logger",
    "MT5Error",
    "MT5ConnectionError",
    "MT5OrderError",
    "MT5SymbolError",
    "MT5ValidationError",
]
