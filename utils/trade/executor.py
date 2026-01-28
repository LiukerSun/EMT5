"""
订单执行器模块

提供订单发送、检查、修改、取消等功能
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from ..core.decorators import require_connection
from ..core.converters import to_dict, add_datetime_fields
from ..logger import logger
from ..exceptions import MT5OrderError, MT5ValidationError


class MT5Executor:
    """
    MT5 订单执行器

    负责订单的发送、检查、修改和取消操作
    """

    def __init__(self, connection, default_magic: int = 0):
        """
        初始化订单执行器

        参数:
            connection: MT5Connection 实例
            default_magic: 默认 EA 标识号
        """
        self.connection = connection
        self.default_magic = default_magic

    @require_connection
    def send(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送交易请求到交易服务器

        参数:
            request: 交易请求字典，包含以下字段：
                - action: 交易操作类型 (mt5.TRADE_ACTION_DEAL 等)
                - symbol: 交易品种名称
                - volume: 请求的交易量（手数）
                - type: 订单类型 (mt5.ORDER_TYPE_BUY 等)
                - price: 订单执行价格
                - sl: 止损价格
                - tp: 止盈价格
                - deviation: 最大价格偏差（点数）
                - magic: EA 标识号
                - comment: 订单注释
                - type_time: 订单有效期类型
                - type_filling: 订单成交类型

        返回:
            Dict: 交易结果字典，包含以下字段：
                - retcode: 返回码（10009 表示成功）
                - deal: 成交票据号
                - order: 订单票据号
                - volume: 成交量
                - price: 成交价格
                - comment: 结果注释
            失败时返回 None

        常见返回码:
            - 10009: TRADE_RETCODE_DONE - 请求已完成
            - 10004: TRADE_RETCODE_REQUOTE - 重新报价
            - 10006: TRADE_RETCODE_REJECT - 请求被拒绝
            - 10013: TRADE_RETCODE_INVALID_PRICE - 价格无效
            - 10014: TRADE_RETCODE_INVALID_STOPS - 止损/止盈无效
            - 10016: TRADE_RETCODE_MARKET_CLOSED - 市场关闭
            - 10019: TRADE_RETCODE_NO_MONEY - 资金不足

        使用示例:
            request = mt5.order("EURUSD").market_buy(0.1).build()
            result = mt5.executor.send(request)
            if result and result['retcode'] == 10009:
                print(f"交易成功！订单号: {result['order']}")
        """
        if not isinstance(request, dict):
            raise MT5ValidationError("请求参数必须是字典类型")

        try:
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                raise MT5OrderError(f"order_send() 失败", error[0] if error else None)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.warning(f"交易请求未完全成功, 返回码: {result.retcode}")
                logger.warning(f"返回信息: {result.comment}")

            result_dict = to_dict(result)

            # 转换嵌套的 request 结构
            if "request" in result_dict and hasattr(result_dict["request"], "_asdict"):
                result_dict["request"] = result_dict["request"]._asdict()

            # 添加时间字段
            result_dict = add_datetime_fields(
                result_dict,
                ['time', 'time_setup', 'time_expiration', 'time_done']
            )

            return result_dict

        except MT5OrderError:
            raise
        except Exception as e:
            raise MT5OrderError(f"执行异常: {str(e)}")

    @require_connection
    def check(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查交易请求的正确性（不实际发送到服务器）

        参数:
            request: 交易请求字典（格式同 send）

        返回:
            Dict: 检查结果字典，包含：
                - retcode: 返回码（10009 或 0 表示检查通过）
                - balance: 操作后的预期余额
                - equity: 操作后的预期净值
                - profit: 预期盈利
                - margin: 所需保证金
                - margin_free: 操作后的可用保证金
                - margin_level: 操作后的保证金水平
                - comment: 结果注释

        使用示例:
            request = mt5.order("EURUSD").market_buy(0.1).build()
            check_result = mt5.executor.check(request)
            if check_result and check_result['retcode'] in [0, 10009]:
                print(f"订单检查通过，所需保证金: {check_result['margin']}")
        """
        if not isinstance(request, dict):
            raise MT5ValidationError("请求参数必须是字典类型")

        # Python 层面的基础检查
        self._validate_volume(request)

        try:
            result = mt5.order_check(request)

            if result is None:
                error = mt5.last_error()
                raise MT5OrderError(f"order_check() 失败", error[0] if error else None)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.warning(f"订单检查未通过, 返回码: {result.retcode}")
                logger.warning(f"返回信息: {result.comment}")

            result_dict = to_dict(result)

            # 转换嵌套的 request 结构
            if "request" in result_dict and hasattr(result_dict["request"], "_asdict"):
                result_dict["request"] = result_dict["request"]._asdict()

            return result_dict

        except MT5OrderError:
            raise
        except Exception as e:
            raise MT5OrderError(f"执行异常: {str(e)}")

    @require_connection
    def modify(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        修改持仓的止损止盈

        参数:
            ticket: 持仓票据号
            sl: 新的止损价格，None 表示不修改
            tp: 新的止盈价格，None 表示不修改

        返回:
            Dict: 修改结果字典

        使用示例:
            result = mt5.executor.modify(123456, sl=1.0950, tp=1.1050)
        """
        # 获取持仓信息
        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise MT5OrderError(f"找不到票据号为 {ticket} 的持仓")

        position = position[0]

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position.symbol,
            "sl": sl if sl is not None else position.sl,
            "tp": tp if tp is not None else position.tp,
        }

        return self.send(request)

    @require_connection
    def cancel(self, ticket: int) -> Optional[Dict[str, Any]]:
        """
        取消挂单

        参数:
            ticket: 挂单票据号

        返回:
            Dict: 取消结果字典

        使用示例:
            result = mt5.executor.cancel(123456)
        """
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }

        return self.send(request)

    @require_connection
    def close_position(
        self,
        ticket: int,
        volume: Optional[float] = None,
        deviation: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        平仓

        参数:
            ticket: 持仓票据号
            volume: 平仓量，None 表示全部平仓
            deviation: 最大价格偏差

        返回:
            Dict: 平仓结果字典

        使用示例:
            # 全部平仓
            result = mt5.executor.close_position(123456)

            # 部分平仓
            result = mt5.executor.close_position(123456, volume=0.05)
        """
        # 获取持仓信息
        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise MT5OrderError(f"找不到票据号为 {ticket} 的持仓")

        position = position[0]
        symbol = position.symbol
        pos_volume = position.volume if volume is None else volume
        pos_type = position.type

        # 获取当前价格
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5OrderError(f"无法获取 {symbol} 的价格信息")

        # 确定平仓方向和价格
        if pos_type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        # 获取成交模式
        filling_mode = self._get_filling_mode(symbol)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos_volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": deviation,
            "magic": self.default_magic,
            "comment": "close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        return self.send(request)

    def _get_filling_mode(self, symbol: str) -> int:
        """获取品种支持的成交模式"""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return mt5.ORDER_FILLING_IOC

        filling_mode = symbol_info.filling_mode

        if filling_mode & 1:  # SYMBOL_FILLING_IOC
            return mt5.ORDER_FILLING_IOC
        elif filling_mode & 2:  # SYMBOL_FILLING_FOK
            return mt5.ORDER_FILLING_FOK
        else:
            return mt5.ORDER_FILLING_RETURN

    def _validate_volume(self, request: Dict[str, Any]) -> None:
        """验证交易量"""
        if "symbol" not in request or "volume" not in request:
            return

        try:
            symbol_info = mt5.symbol_info(request["symbol"])
            if not symbol_info:
                return

            volume = request["volume"]
            volume_min = symbol_info.volume_min
            volume_max = symbol_info.volume_max
            volume_step = symbol_info.volume_step

            if volume < volume_min:
                raise MT5ValidationError(f"交易量 {volume} 小于最小值 {volume_min}")
            if volume > volume_max:
                raise MT5ValidationError(f"交易量 {volume} 大于最大值 {volume_max}")

            if volume_step > 0:
                steps = round((volume - volume_min) / volume_step)
                expected_volume = volume_min + steps * volume_step
                if abs(volume - expected_volume) > 1e-8:
                    raise MT5ValidationError(
                        f"交易量 {volume} 不符合步进值 {volume_step}，建议使用 {expected_volume}"
                    )
        except MT5ValidationError:
            raise
        except Exception as e:
            logger.warning(f"预检查时出现警告: {str(e)}")
