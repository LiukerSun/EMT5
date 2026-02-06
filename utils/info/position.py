"""
持仓和挂单管理模块

提供持仓查询、挂单查询等功能
"""

import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any
from ..core.decorators import require_connection
from ..core.converters import convert_positions_to_dict, convert_orders_to_dict
from ..logger import logger


class MT5Position:
    """
    MT5 持仓和挂单管理类

    提供持仓查询、挂单查询等功能
    """

    def __init__(self, connection):
        """
        初始化持仓管理器

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    @require_connection
    def get_positions(
        self,
        symbol: Optional[str] = None,
        ticket: Optional[int] = None,
        group: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取持仓列表

        参数:
            symbol: 交易品种名称，用于过滤
            ticket: 持仓票据号，用于获取特定持仓
            group: 品种组，用于过滤（支持通配符，如 "*USD*"）

        返回:
            List[Dict]: 持仓列表，每个持仓包含以下字段：
                - ticket: 持仓票据号
                - time: 开仓时间（时间戳）
                - time_dt: 开仓时间（datetime 对象，UTC）
                - type: 持仓类型（0=买入，1=卖出）
                - magic: EA 标识号
                - identifier: 持仓标识符
                - reason: 开仓原因
                - volume: 持仓量
                - price_open: 开仓价格
                - sl: 止损价格
                - tp: 止盈价格
                - price_current: 当前价格
                - swap: 隔夜利息
                - profit: 当前盈亏
                - symbol: 交易品种
                - comment: 注释
            失败时返回 None

        使用示例:
            # 获取所有持仓
            positions = mt5.position.get_positions()

            # 获取指定品种的持仓
            positions = mt5.position.get_positions(symbol="EURUSD")

            # 获取指定票据号的持仓
            position = mt5.position.get_positions(ticket=123456)

            # 获取美元相关品种的持仓
            positions = mt5.position.get_positions(group="*USD*")
        """
        try:
            if ticket is not None:
                positions = mt5.positions_get(ticket=ticket)
            elif symbol is not None:
                positions = mt5.positions_get(symbol=symbol)
            elif group is not None:
                positions = mt5.positions_get(group=group)
            else:
                positions = mt5.positions_get()

            if positions is None:
                return []

            return convert_positions_to_dict(positions)

        except Exception as e:
            logger.error(f"获取持仓失败: {str(e)}")
            return None

    @require_connection
    def get_position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """
        根据票据号获取单个持仓

        参数:
            ticket: 持仓票据号

        返回:
            Dict: 持仓信息字典，如果不存在返回 None

        使用示例:
            position = mt5.position.get_position_by_ticket(123456)
            if position:
                print(f"盈亏: {position['profit']}")
        """
        positions = self.get_positions(ticket=ticket)
        if positions and len(positions) > 0:
            return positions[0]
        return None

    @require_connection
    def get_positions_total(self) -> int:
        """
        获取持仓总数

        返回:
            int: 持仓数量
        """
        total = mt5.positions_total()
        return total if total is not None else 0

    @require_connection
    def get_orders(
        self,
        symbol: Optional[str] = None,
        ticket: Optional[int] = None,
        group: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取挂单列表

        参数:
            symbol: 交易品种名称，用于过滤
            ticket: 订单票据号，用于获取特定订单
            group: 品种组，用于过滤（支持通配符）

        返回:
            List[Dict]: 挂单列表，每个挂单包含以下字段：
                - ticket: 订单票据号
                - time_setup: 挂单时间（时间戳）
                - time_setup_dt: 挂单时间（datetime 对象，UTC）
                - type: 订单类型
                - state: 订单状态
                - time_expiration: 过期时间
                - time_done: 完成时间
                - magic: EA 标识号
                - volume_initial: 初始交易量
                - volume_current: 当前交易量
                - price_open: 挂单价格
                - sl: 止损价格
                - tp: 止盈价格
                - price_current: 当前价格
                - symbol: 交易品种
                - comment: 注释
            失败时返回 None

        使用示例:
            # 获取所有挂单
            orders = mt5.position.get_orders()

            # 获取指定品种的挂单
            orders = mt5.position.get_orders(symbol="EURUSD")
        """
        try:
            if ticket is not None:
                orders = mt5.orders_get(ticket=ticket)
            elif symbol is not None:
                orders = mt5.orders_get(symbol=symbol)
            elif group is not None:
                orders = mt5.orders_get(group=group)
            else:
                orders = mt5.orders_get()

            if orders is None:
                return []

            return convert_orders_to_dict(orders)

        except Exception as e:
            logger.error(f"获取挂单失败: {str(e)}")
            return None

    @require_connection
    def get_order_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """
        根据票据号获取单个挂单

        参数:
            ticket: 订单票据号

        返回:
            Dict: 挂单信息字典，如果不存在返回 None
        """
        orders = self.get_orders(ticket=ticket)
        if orders and len(orders) > 0:
            return orders[0]
        return None

    @require_connection
    def get_orders_total(self) -> int:
        """
        获取挂单总数

        返回:
            int: 挂单数量
        """
        total = mt5.orders_total()
        return total if total is not None else 0
