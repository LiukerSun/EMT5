"""
核心功能模块

包含连接管理、装饰器、数据转换等核心功能
"""

from .connection import MT5Connection
from .decorators import require_connection, retry, catch_exceptions, log_execution
from .converters import (
    to_dict,
    add_datetime_fields,
    convert_bars_to_dict,
    convert_ticks_to_dict,
    convert_orders_to_dict,
    convert_positions_to_dict,
    convert_deals_to_dict,
)

__all__ = [
    "MT5Connection",
    "require_connection",
    "retry",
    "catch_exceptions",
    "log_execution",
    "to_dict",
    "add_datetime_fields",
    "convert_bars_to_dict",
    "convert_ticks_to_dict",
    "convert_orders_to_dict",
    "convert_positions_to_dict",
    "convert_deals_to_dict",
]
