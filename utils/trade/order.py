"""
MT5 交易订单模块

提供订单发送、检查等交易操作功能
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any
from ..logger import logger


class MT5Order:
    """
    MT5 交易订单类

    封装了订单发送、订单检查等交易操作
    """

    def __init__(self, connection):
        """
        初始化 MT5Order 实例

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    def order_send(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送交易请求到交易服务器

        参数:
            request: 交易请求字典，包含以下字段：
                - action: 交易操作类型 (mt5.TRADE_ACTION_DEAL 等)
                - magic: EA 标识号
                - order: 订单票据号（修改挂单时需要）
                - symbol: 交易品种名称
                - volume: 请求的交易量（手数）
                - price: 订单执行价格
                - stoplimit: 挂单限价
                - sl: 止损价格
                - tp: 止盈价格
                - deviation: 最大价格偏差（点数）
                - type: 订单类型 (mt5.ORDER_TYPE_BUY 等)
                - type_filling: 订单成交类型
                - type_time: 订单有效期类型
                - expiration: 订单过期时间
                - comment: 订单注释
                - position: 持仓票据号（修改/平仓时需要）
                - position_by: 反向持仓票据号（对冲平仓时需要）

        返回:
            Dict: 交易结果字典，包含以下字段：
                - retcode: 返回码
                - deal: 成交票据号
                - order: 订单票据号
                - volume: 成交量
                - price: 成交价格
                - bid: 当前买价
                - ask: 当前卖价
                - comment: 结果注释
                - request_id: 请求ID
                - retcode_external: 外部返回码
                - request: 原始请求结构
            失败时返回 None
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        # 2. 验证必要参数
        if not isinstance(request, dict):
            logger.error("请求参数必须是字典类型")
            return None

        # 3. 调用 MT5 API
        try:
            result = mt5.order_send(request)

            # 4. 错误处理
            if result is None:
                error = mt5.last_error()
                logger.error(f"order_send() 失败, 错误代码: {error}")
                return None

            # 5. 检查返回码
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.warning(f"交易请求未完全成功, 返回码: {result.retcode}")
                logger.warning(f"返回信息: {result.comment}")

            # 6. 转换为字典
            result_dict = result._asdict()

            # 7. 转换嵌套的 request 结构
            if "request" in result_dict and hasattr(result_dict["request"], "_asdict"):
                result_dict["request"] = result_dict["request"]._asdict()

            return result_dict

        except Exception as e:
            logger.error(f"执行异常: {str(e)}")
            return None

    def order_check(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查交易请求的正确性（不实际发送到服务器）

        参数:
            request: 交易请求字典（格式同 order_send）

        返回:
            Dict: 检查结果字典，包含：
                - retcode: 返回码
                - balance: 操作后的余额
                - equity: 操作后的净值
                - profit: 预期盈利
                - margin: 所需保证金
                - margin_free: 操作后的可用保证金
                - margin_level: 操作后的保证金水平
                - comment: 结果注释
                - request: 原始请求结构
            失败时返回 None
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        # 2. 验证必要参数
        if not isinstance(request, dict):
            logger.error("请求参数必须是字典类型")
            return None

        # 3. 调用 MT5 API
        try:
            result = mt5.order_check(request)

            # 4. 错误处理
            if result is None:
                error = mt5.last_error()
                logger.error(f"order_check() 失败, 错误代码: {error}")
                return None

            # 5. 检查返回码
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.warning(f"订单检查未通过, 返回码: {result.retcode}")
                logger.warning(f"返回信息: {result.comment}")

            # 6. 转换为字典
            result_dict = result._asdict()

            # 7. 转换嵌套的 request 结构
            if "request" in result_dict and hasattr(result_dict["request"], "_asdict"):
                result_dict["request"] = result_dict["request"]._asdict()

            return result_dict

        except Exception as e:
            logger.error(f"执行异常: {str(e)}")
            return None

    def create_market_buy_request(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        deviation: int = 20,
        magic: int = 0,
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        创建市价买入请求

        此方法用于构建一个市价买入订单的请求字典，可以直接传递给 order_send() 或 order_check() 方法。
        市价买入会以当前市场的卖出价（Ask）立即执行。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_", "BTCUSD" 等
            volume: 交易量（手数），例如 0.01 表示 0.01 手，必须符合品种的最小/最大交易量限制
            sl: 止损价格（绝对价格，不是点数）
                - 0.0 表示不设置止损
                - 买入订单的止损价格必须低于当前价格
                - 例如：当前价格 1.1000，止损可设为 1.0950
            tp: 止盈价格（绝对价格，不是点数）
                - 0.0 表示不设置止盈
                - 买入订单的止盈价格必须高于当前价格
                - 例如：当前价格 1.1000，止盈可设为 1.1050
            deviation: 最大价格偏差（点数），允许的滑点范围
                - 默认 20 点，表示实际成交价格可以偏离请求价格最多 20 点
                - 市场波动大时可适当增加此值
            magic: EA 标识号（Expert Advisor 魔术数字）
                - 用于标识订单来源，方便管理和过滤订单
                - 默认 0 表示手动交易
            comment: 订单注释，最多 31 个字符
                - 用于记录订单用途或备注信息

        返回:
            Dict: 交易请求字典，包含以下字段：
                - action: TRADE_ACTION_DEAL（立即执行）
                - symbol: 交易品种
                - volume: 交易量
                - type: ORDER_TYPE_BUY（买入）
                - price: 当前卖出价（Ask）
                - sl: 止损价格
                - tp: 止盈价格
                - deviation: 最大偏差
                - magic: EA 标识号
                - comment: 订单注释
                - type_time: ORDER_TIME_GTC（Good Till Cancelled，取消前一直有效）
                - type_filling: ORDER_FILLING_IOC（Immediate or Cancel，立即成交或取消）
            失败时返回空字典 {}

        使用示例:
            # 基本用法：创建简单的市价买入请求
            request = order.create_market_buy_request(
                symbol="EURUSD",
                volume=0.1
            )

            # 带止损止盈的买入请求
            request = order.create_market_buy_request(
                symbol="GOLD_",
                volume=0.01,
                sl=1950.00,      # 止损价格
                tp=2050.00,      # 止盈价格
                deviation=50,    # 允许 50 点滑点
                magic=123456,    # EA 标识号
                comment="黄金买入"
            )

            # 发送订单前建议先检查
            check_result = order.order_check(request)
            if check_result and check_result['retcode'] == 10009:
                result = order.order_send(request)

        注意事项:
            1. 调用此方法前必须确保已连接到 MT5 终端
            2. 交易品种必须在市场观察窗口中启用（使用 symbol_select）
            3. 止损止盈价格必须符合品种的止损位要求（SYMBOL_TRADE_STOPS_LEVEL）
            4. 返回的请求字典可能需要根据品种特性调整 type_filling 参数
            5. 建议使用 order_check() 验证请求的有效性后再发送
        """
        # 1. 获取当前市场价格（买入使用卖出价 Ask）
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"无法获取 {symbol} 的价格信息")
            return {}

        # 2. 构建交易请求字典
        request = {
            "action": mt5.TRADE_ACTION_DEAL,  # 立即执行交易
            "symbol": symbol,  # 交易品种
            "volume": volume,  # 交易量（手数）
            "type": mt5.ORDER_TYPE_BUY,  # 买入订单
            "price": tick.ask,  # 使用当前卖出价（Ask）
            "sl": sl,  # 止损价格
            "tp": tp,  # 止盈价格
            "deviation": deviation,  # 最大价格偏差（点数）
            "magic": magic,  # EA 标识号
            "comment": comment,  # 订单注释
            "type_time": mt5.ORDER_TIME_GTC,  # 订单有效期：取消前一直有效
            "type_filling": mt5.ORDER_FILLING_IOC,  # 成交类型：立即成交或取消
        }

        return request

    def create_market_sell_request(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        deviation: int = 20,
        magic: int = 0,
        comment: str = "",
        position: int = 0,
    ) -> Dict[str, Any]:
        """
        创建市价卖出请求

        此方法用于构建一个市价卖出订单的请求字典。市价卖出会以当前市场的买入价（Bid）立即执行。
        可用于开新仓（做空）或平掉已有的买入持仓。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_", "BTCUSD" 等
            volume: 交易量（手数），例如 0.01 表示 0.01 手
            sl: 止损价格（绝对价格，不是点数）
                - 0.0 表示不设置止损
                - 卖出订单的止损价格必须高于当前价格
                - 例如：当前价格 1.1000，止损可设为 1.1050
            tp: 止盈价格（绝对价格，不是点数）
                - 0.0 表示不设置止盈
                - 卖出订单的止盈价格必须低于当前价格
                - 例如：当前价格 1.1000，止盈可设为 1.0950
            deviation: 最大价格偏差（点数），允许的滑点范围，默认 20 点
            magic: EA 标识号，用于标识订单来源，默认 0
            comment: 订单注释，最多 31 个字符
            position: 持仓票据号（用于平仓操作）
                - 0 表示开新仓（做空）
                - 大于 0 表示平掉指定的买入持仓
                - 持仓号可从 order_send() 返回结果的 'order' 字段获取

        返回:
            Dict: 交易请求字典，包含所有必要的订单参数
            失败时返回空字典 {}

        使用示例:
            # 示例 1：开新仓（做空）
            request = order.create_market_sell_request(
                symbol="EURUSD",
                volume=0.1,
                sl=1.1050,       # 止损高于当前价
                tp=1.0950        # 止盈低于当前价
            )

            # 示例 2：平掉已有的买入持仓
            # 假设之前买入后获得了持仓号 position_id
            close_request = order.create_market_sell_request(
                symbol="GOLD_",
                volume=0.01,
                position=position_id,  # 指定要平掉的持仓号
                comment="平仓"
            )
            result = order.order_send(close_request)

            # 示例 3：完整的开仓-平仓流程
            # 1. 先买入开仓
            buy_request = order.create_market_buy_request("EURUSD", 0.1)
            buy_result = order.order_send(buy_request)
            if buy_result and buy_result['retcode'] == 10009:
                position_id = buy_result['order']

                # 2. 等待一段时间后平仓
                import time
                time.sleep(10)

                # 3. 卖出平仓
                sell_request = order.create_market_sell_request(
                    symbol="EURUSD",
                    volume=0.1,
                    position=position_id
                )
                close_result = order.order_send(sell_request)

        注意事项:
            1. 开新仓（做空）时不需要指定 position 参数
            2. 平仓时必须指定正确的 position 参数
            3. 平仓的交易量必须小于等于持仓量
            4. 止损止盈的方向与买入相反（止损在上方，止盈在下方）
            5. 建议使用 order_check() 验证请求的有效性
        """
        # 1. 获取当前市场价格（卖出使用买入价 Bid）
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"无法获取 {symbol} 的价格信息")
            return {}

        # 2. 构建交易请求字典
        request = {
            "action": mt5.TRADE_ACTION_DEAL,  # 立即执行交易
            "symbol": symbol,  # 交易品种
            "volume": volume,  # 交易量（手数）
            "type": mt5.ORDER_TYPE_SELL,  # 卖出订单
            "price": tick.bid,  # 使用当前买入价（Bid）
            "sl": sl,  # 止损价格
            "tp": tp,  # 止盈价格
            "deviation": deviation,  # 最大价格偏差（点数）
            "magic": magic,  # EA 标识号
            "comment": comment,  # 订单注释
            "type_time": mt5.ORDER_TIME_GTC,  # 订单有效期：取消前一直有效
            "type_filling": mt5.ORDER_FILLING_IOC,  # 成交类型：立即成交或取消
        }

        # 3. 如果指定了持仓号，添加到请求中（用于平仓操作）
        if position > 0:
            request["position"] = position

        return request

    def create_limit_buy_request(
        self,
        symbol: str,
        volume: float,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        创建限价买入挂单请求

        此方法用于创建限价买入挂单（Buy Limit）。挂单会在价格达到指定价格时自动触发买入。
        限价买入挂单的价格必须低于当前市场价格，适用于等待价格回调后买入的策略。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_", "BTCUSD" 等
            volume: 交易量（手数），例如 0.01 表示 0.01 手
            price: 挂单价格（必须低于当前市场价格）
                - 当市场价格下跌到此价格时，订单会自动触发买入
                - 例如：当前价格 1.1000，可设置挂单价格为 1.0950
            sl: 止损价格（绝对价格）
                - 0.0 表示不设置止损
                - 必须低于挂单价格
                - 例如：挂单价 1.0950，止损可设为 1.0900
            tp: 止盈价格（绝对价格）
                - 0.0 表示不设置止盈
                - 必须高于挂单价格
                - 例如：挂单价 1.0950，止盈可设为 1.1000
            magic: EA 标识号，用于标识订单来源，默认 0
            comment: 订单注释，最多 31 个字符

        返回:
            Dict: 交易请求字典，包含挂单所需的所有参数

        使用示例:
            # 示例 1：基本限价买入挂单
            # 当前价格 1.1000，等待价格跌到 1.0950 时买入
            request = order.create_limit_buy_request(
                symbol="EURUSD",
                volume=0.1,
                price=1.0950
            )
            result = order.order_send(request)

            # 示例 2：带止损止盈的限价买入挂单
            request = order.create_limit_buy_request(
                symbol="GOLD_",
                volume=0.01,
                price=1950.00,    # 挂单价格
                sl=1940.00,       # 止损（低于挂单价）
                tp=1970.00,       # 止盈（高于挂单价）
                magic=123456,
                comment="黄金回调买入"
            )

            # 示例 3：检查挂单是否有效
            check_result = order.order_check(request)
            if check_result and check_result['retcode'] == 10009:
                result = order.order_send(request)
                if result and result['retcode'] == 10009:
                    order_id = result['order']
                    print(f"挂单成功，订单号: {order_id}")

        挂单类型说明:
            - Buy Limit（限价买入）：价格低于当前价，等待价格下跌后买入
            - Buy Stop（止损买入）：价格高于当前价，等待价格突破后买入
            - Sell Limit（限价卖出）：价格高于当前价，等待价格上涨后卖出
            - Sell Stop（止损卖出）：价格低于当前价，等待价格跌破后卖出

        注意事项:
            1. 挂单价格必须低于当前市场价格，否则会被拒绝
            2. 挂单价格与当前价格的距离必须满足品种的最小距离要求（SYMBOL_TRADE_FREEZE_LEVEL）
            3. 挂单会一直有效直到被触发、取消或过期（GTC 模式）
            4. 挂单触发后会自动转为市价订单执行
            5. 可以使用 order_send() 发送挂单，使用 order_cancel() 取消挂单
            6. type_filling 设置为 RETURN 表示部分成交后剩余部分继续挂单
        """
        # 构建限价买入挂单请求
        request = {
            "action": mt5.TRADE_ACTION_PENDING,  # 挂单操作（不立即执行）
            "symbol": symbol,  # 交易品种
            "volume": volume,  # 交易量（手数）
            "type": mt5.ORDER_TYPE_BUY_LIMIT,  # 限价买入挂单
            "price": price,  # 挂单价格（必须低于当前价）
            "sl": sl,  # 止损价格
            "tp": tp,  # 止盈价格
            "magic": magic,  # EA 标识号
            "comment": comment,  # 订单注释
            "type_time": mt5.ORDER_TIME_GTC,  # 订单有效期：取消前一直有效
            "type_filling": mt5.ORDER_FILLING_RETURN,  # 成交类型：部分成交后剩余继续挂单
        }

        return request

    def create_limit_sell_request(
        self,
        symbol: str,
        volume: float,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        创建限价卖出挂单请求

        参数:
            symbol: 交易品种
            volume: 交易量（手数）
            price: 挂单价格
            sl: 止损价格（0表示不设置）
            tp: 止盈价格（0表示不设置）
            magic: EA 标识号
            comment: 订单注释

        返回:
            Dict: 交易请求字典
        """
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL_LIMIT,
            "price": price,
            "sl": sl,
            "tp": tp,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        return request
