"""
订单请求构建器模块

提供 Builder 模式的订单请求构建，支持链式调用
"""

import MetaTrader5 as mt5
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .executor import MT5Executor


class OrderRequestBuilder:
    """
    订单请求构建器（Builder 模式 + 链式调用）

    提供流畅的 API 来构建交易请求，支持链式调用直接发送订单。

    使用示例:
        # 链式调用直接发送
        result = (mt5.order("EURUSD")
            .market_buy(0.1)
            .with_sl(1.0950)
            .with_tp(1.1050)
            .send())

        # 只构建不发送
        request = (mt5.order("EURUSD")
            .market_buy(0.1)
            .build())

        # 检查订单
        check_result = (mt5.order("EURUSD")
            .market_buy(0.1)
            .check())
    """

    def __init__(
        self,
        symbol: str,
        connection,
        executor: 'MT5Executor',
        default_magic: int = 0
    ):
        """
        初始化订单构建器

        参数:
            symbol: 交易品种名称
            connection: MT5Connection 实例
            executor: MT5Executor 实例
            default_magic: 默认 EA 标识号
        """
        self._symbol = symbol
        self._connection = connection
        self._executor = executor
        self._default_magic = default_magic

        # 请求参数
        self._action = None
        self._order_type = None
        self._volume = 0.0
        self._price = 0.0
        self._sl = 0.0
        self._tp = 0.0
        self._deviation = 20
        self._magic = default_magic
        self._comment = ""
        self._position = 0

    # ==================== 订单类型方法 ====================

    def market_buy(self, volume: float) -> 'OrderRequestBuilder':
        """
        市价买入

        参数:
            volume: 交易量（手数）

        返回:
            self: 支持链式调用

        使用示例:
            mt5.order("EURUSD").market_buy(0.1).send()
        """
        self._action = mt5.TRADE_ACTION_DEAL
        self._order_type = mt5.ORDER_TYPE_BUY
        self._volume = volume
        self._price = self._get_ask_price()
        return self

    def market_sell(self, volume: float, position: int = 0) -> 'OrderRequestBuilder':
        """
        市价卖出

        参数:
            volume: 交易量（手数）
            position: 持仓票据号（用于平仓），0 表示开新仓

        返回:
            self: 支持链式调用

        使用示例:
            # 开空仓
            mt5.order("EURUSD").market_sell(0.1).send()

            # 平多仓
            mt5.order("EURUSD").market_sell(0.1, position=123456).send()
        """
        self._action = mt5.TRADE_ACTION_DEAL
        self._order_type = mt5.ORDER_TYPE_SELL
        self._volume = volume
        self._price = self._get_bid_price()
        self._position = position
        return self

    def limit_buy(self, volume: float, price: float) -> 'OrderRequestBuilder':
        """
        限价买入挂单

        参数:
            volume: 交易量（手数）
            price: 挂单价格（必须低于当前价）

        返回:
            self: 支持链式调用

        使用示例:
            mt5.order("EURUSD").limit_buy(0.1, 1.0950).send()
        """
        self._action = mt5.TRADE_ACTION_PENDING
        self._order_type = mt5.ORDER_TYPE_BUY_LIMIT
        self._volume = volume
        self._price = price
        return self

    def limit_sell(self, volume: float, price: float) -> 'OrderRequestBuilder':
        """
        限价卖出挂单

        参数:
            volume: 交易量（手数）
            price: 挂单价格（必须高于当前价）

        返回:
            self: 支持链式调用

        使用示例:
            mt5.order("EURUSD").limit_sell(0.1, 1.1050).send()
        """
        self._action = mt5.TRADE_ACTION_PENDING
        self._order_type = mt5.ORDER_TYPE_SELL_LIMIT
        self._volume = volume
        self._price = price
        return self

    def stop_buy(self, volume: float, price: float) -> 'OrderRequestBuilder':
        """
        止损买入挂单

        参数:
            volume: 交易量（手数）
            price: 挂单价格（必须高于当前价）

        返回:
            self: 支持链式调用

        使用示例:
            mt5.order("EURUSD").stop_buy(0.1, 1.1050).send()
        """
        self._action = mt5.TRADE_ACTION_PENDING
        self._order_type = mt5.ORDER_TYPE_BUY_STOP
        self._volume = volume
        self._price = price
        return self

    def stop_sell(self, volume: float, price: float) -> 'OrderRequestBuilder':
        """
        止损卖出挂单

        参数:
            volume: 交易量（手数）
            price: 挂单价格（必须低于当前价）

        返回:
            self: 支持链式调用

        使用示例:
            mt5.order("EURUSD").stop_sell(0.1, 1.0950).send()
        """
        self._action = mt5.TRADE_ACTION_PENDING
        self._order_type = mt5.ORDER_TYPE_SELL_STOP
        self._volume = volume
        self._price = price
        return self

    # ==================== 可选参数方法 ====================

    def with_sl(self, sl: float) -> 'OrderRequestBuilder':
        """
        设置止损价格

        参数:
            sl: 止损价格

        返回:
            self: 支持链式调用
        """
        self._sl = sl
        return self

    def with_tp(self, tp: float) -> 'OrderRequestBuilder':
        """
        设置止盈价格

        参数:
            tp: 止盈价格

        返回:
            self: 支持链式调用
        """
        self._tp = tp
        return self

    def with_sl_tp(self, sl: float, tp: float) -> 'OrderRequestBuilder':
        """
        同时设置止损和止盈

        参数:
            sl: 止损价格
            tp: 止盈价格

        返回:
            self: 支持链式调用
        """
        self._sl = sl
        self._tp = tp
        return self

    def with_deviation(self, deviation: int) -> 'OrderRequestBuilder':
        """
        设置最大价格偏差

        参数:
            deviation: 最大偏差（点数）

        返回:
            self: 支持链式调用
        """
        self._deviation = deviation
        return self

    def with_magic(self, magic: int) -> 'OrderRequestBuilder':
        """
        设置 EA 标识号

        参数:
            magic: EA 标识号

        返回:
            self: 支持链式调用
        """
        self._magic = magic
        return self

    def with_comment(self, comment: str) -> 'OrderRequestBuilder':
        """
        设置订单注释

        参数:
            comment: 注释内容（最多 31 个字符）

        返回:
            self: 支持链式调用
        """
        self._comment = comment
        return self

    # ==================== 终结方法 ====================

    def build(self) -> Dict[str, Any]:
        """
        构建请求字典

        返回:
            Dict: 交易请求字典，可传递给 executor.send()

        使用示例:
            request = mt5.order("EURUSD").market_buy(0.1).build()
            result = mt5.executor.send(request)
        """
        if self._action is None or self._order_type is None:
            raise ValueError("必须先调用订单类型方法（如 market_buy, limit_sell 等）")

        filling_mode = self._get_filling_mode()

        request = {
            "action": self._action,
            "symbol": self._symbol,
            "volume": self._volume,
            "type": self._order_type,
            "price": self._price,
            "sl": self._sl,
            "tp": self._tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": self._comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        # 如果指定了持仓号（用于平仓）
        if self._position > 0:
            request["position"] = self._position

        return request

    def send(self) -> Optional[Dict[str, Any]]:
        """
        构建并发送订单

        返回:
            Dict: 交易结果字典

        使用示例:
            result = mt5.order("EURUSD").market_buy(0.1).send()
            if result and result['retcode'] == 10009:
                print(f"成功！订单号: {result['order']}")
        """
        request = self.build()
        return self._executor.send(request)

    def check(self) -> Optional[Dict[str, Any]]:
        """
        构建并检查订单

        返回:
            Dict: 检查结果字典

        使用示例:
            check = mt5.order("EURUSD").market_buy(0.1).check()
            if check and check['retcode'] in [0, 10009]:
                print(f"检查通过，所需保证金: {check['margin']}")
        """
        request = self.build()
        return self._executor.check(request)

    # ==================== 私有方法 ====================

    def _get_ask_price(self) -> float:
        """获取当前卖出价（Ask）"""
        tick = mt5.symbol_info_tick(self._symbol)
        if tick is None:
            raise ValueError(f"无法获取 {self._symbol} 的价格信息")
        return tick.ask

    def _get_bid_price(self) -> float:
        """获取当前买入价（Bid）"""
        tick = mt5.symbol_info_tick(self._symbol)
        if tick is None:
            raise ValueError(f"无法获取 {self._symbol} 的价格信息")
        return tick.bid

    def _get_filling_mode(self) -> int:
        """获取品种支持的成交模式"""
        symbol_info = mt5.symbol_info(self._symbol)
        if symbol_info is None:
            return mt5.ORDER_FILLING_IOC

        filling_mode = symbol_info.filling_mode

        if filling_mode & 1:  # SYMBOL_FILLING_IOC
            return mt5.ORDER_FILLING_IOC
        elif filling_mode & 2:  # SYMBOL_FILLING_FOK
            return mt5.ORDER_FILLING_FOK
        else:
            return mt5.ORDER_FILLING_RETURN
