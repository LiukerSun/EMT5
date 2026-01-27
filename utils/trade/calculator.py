"""
MT5 订单计算模块

提供保证金计算、盈利计算等风险管理工具
"""

import MetaTrader5 as mt5
from typing import Optional
from ..logger import logger


class MT5Calculator:
    """
    MT5 订单计算类

    提供保证金计算、盈利计算等功能，用于风险管理和交易决策
    """

    def __init__(self, connection):
        """
        初始化订单计算器

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    def calc_margin(
        self,
        symbol: str,
        volume: float,
        action: str = 'buy',
        price: Optional[float] = None
    ) -> Optional[float]:
        """
        计算所需保证金

        此方法用于估算执行指定交易操作所需的保证金，不考虑当前的挂单和持仓。
        可以在下单前评估账户是否有足够的保证金。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD#"
            volume: 交易量（手数），例如 0.1 表示 0.1 手
            action: 订单类型，可选值：
                - 'buy': 买入（默认）
                - 'sell': 卖出
                - 'buy_limit': 限价买入
                - 'sell_limit': 限价卖出
                - 'buy_stop': 止损买入
                - 'sell_stop': 止损卖出
            price: 开仓价格，如果为 None 则使用当前市场价

        返回:
            float: 所需保证金（账户货币单位）
            None: 计算失败

        使用示例:
            # 示例 1: 计算买入 0.1 手 EURUSD 所需保证金
            margin = calculator.calc_margin("EURUSD", 0.1, action='buy')
            if margin:
                print(f"所需保证金: {margin} USD")

            # 示例 2: 计算指定价格的保证金
            margin = calculator.calc_margin("EURUSD", 0.5, action='buy', price=1.1000)

            # 示例 3: 批量计算多个品种的保证金
            symbols = ["EURUSD", "GBPUSD", "USDJPY"]
            for symbol in symbols:
                margin = calculator.calc_margin(symbol, 0.1)
                if margin:
                    print(f"{symbol}: {margin}")

        注意事项:
            1. 保证金计算基于当前账户设置和市场环境
            2. 不同品种的保证金要求不同
            3. 杠杆比例会影响保证金大小
            4. 如果未指定价格，会使用当前市场价
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            # 2. 转换 action 为 MT5 订单类型
            order_type = self._get_order_type(action)
            if order_type is None:
                logger.error(f"无效的订单类型: {action}")
                return None

            # 3. 获取价格（如果未指定）
            if price is None:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logger.error(f"无法获取 {symbol} 的价格信息")
                    return None

                # 买入使用 ask，卖出使用 bid
                if action in ['buy', 'buy_limit', 'buy_stop']:
                    price = tick.ask
                else:
                    price = tick.bid

            # 4. 调用 MT5 API 计算保证金
            margin = mt5.order_calc_margin(order_type, symbol, volume, price)

            if margin is None:
                error = mt5.last_error()
                logger.error(f"order_calc_margin() 失败, 错误代码: {error}")
                return None

            return float(margin)

        except Exception as e:
            logger.error(f"计算保证金异常: {str(e)}")
            return None

    def calc_profit(
        self,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
        action: str = 'buy'
    ) -> Optional[float]:
        """
        计算预期盈利

        此方法用于估算指定交易操作的盈利，基于当前账户和市场环境。
        可以在下单前评估潜在的盈亏。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD#"
            volume: 交易量（手数），例如 0.1 表示 0.1 手
            price_open: 开仓价格
            price_close: 平仓价格
            action: 订单类型，可选值：
                - 'buy': 买入（默认）
                - 'sell': 卖出

        返回:
            float: 预期盈利（账户货币单位，正数为盈利，负数为亏损）
            None: 计算失败

        使用示例:
            # 示例 1: 计算买入盈利
            # 假设在 1.1000 买入，在 1.1050 平仓
            profit = calculator.calc_profit(
                symbol="EURUSD",
                volume=0.1,
                price_open=1.1000,
                price_close=1.1050,
                action='buy'
            )
            if profit:
                print(f"预期盈利: {profit} USD")

            # 示例 2: 计算卖出盈利
            profit = calculator.calc_profit(
                symbol="EURUSD",
                volume=0.1,
                price_open=1.1050,
                price_close=1.1000,
                action='sell'
            )

            # 示例 3: 计算止损/止盈的盈亏
            current_price = 1.1000
            sl_price = 1.0950  # 止损 50 点
            tp_price = 1.1100  # 止盈 100 点

            sl_loss = calculator.calc_profit("EURUSD", 0.1, current_price, sl_price, 'buy')
            tp_profit = calculator.calc_profit("EURUSD", 0.1, current_price, tp_price, 'buy')

            print(f"止损亏损: {sl_loss}")
            print(f"止盈盈利: {tp_profit}")
            print(f"风险回报比: {abs(tp_profit / sl_loss):.2f}")

        注意事项:
            1. 盈利计算基于当前账户货币和汇率
            2. 不同品种的点值不同，盈利计算方式也不同
            3. 返回值为正数表示盈利，负数表示亏损
            4. 可以用于计算风险回报比
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            # 2. 转换 action 为 MT5 订单类型
            if action.lower() == 'buy':
                order_type = mt5.ORDER_TYPE_BUY
            elif action.lower() == 'sell':
                order_type = mt5.ORDER_TYPE_SELL
            else:
                logger.error(f"无效的订单类型: {action}，只支持 'buy' 或 'sell'")
                return None

            # 3. 调用 MT5 API 计算盈利
            profit = mt5.order_calc_profit(
                order_type, symbol, volume, price_open, price_close
            )

            if profit is None:
                error = mt5.last_error()
                logger.error(f"order_calc_profit() 失败, 错误代码: {error}")
                return None

            return float(profit)

        except Exception as e:
            logger.error(f"计算盈利异常: {str(e)}")
            return None

    def calc_risk_reward(
        self,
        symbol: str,
        volume: float,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        action: str = 'buy'
    ) -> Optional[dict]:
        """
        计算风险回报比

        此方法综合计算止损亏损、止盈盈利和风险回报比，用于评估交易的风险收益特征。

        参数:
            symbol: 交易品种名称
            volume: 交易量（手数）
            entry_price: 入场价格
            sl_price: 止损价格
            tp_price: 止盈价格
            action: 订单类型 ('buy' 或 'sell')

        返回:
            Dict: 包含以下字段的字典：
                - sl_loss: 止损亏损（负数）
                - tp_profit: 止盈盈利（正数）
                - risk_reward_ratio: 风险回报比
                - risk_amount: 风险金额（绝对值）
                - reward_amount: 回报金额（绝对值）
            None: 计算失败

        使用示例:
            # 计算买入交易的风险回报
            result = calculator.calc_risk_reward(
                symbol="EURUSD",
                volume=0.1,
                entry_price=1.1000,
                sl_price=1.0950,  # 止损 50 点
                tp_price=1.1100,  # 止盈 100 点
                action='buy'
            )

            if result:
                print(f"风险金额: {result['risk_amount']}")
                print(f"回报金额: {result['reward_amount']}")
                print(f"风险回报比: 1:{result['risk_reward_ratio']:.2f}")

                # 判断是否值得交易
                if result['risk_reward_ratio'] >= 2.0:
                    print("风险回报比良好，可以考虑交易")
                else:
                    print("风险回报比不佳，建议调整止损止盈")
        """
        # 1. 计算止损亏损
        sl_loss = self.calc_profit(symbol, volume, entry_price, sl_price, action)
        if sl_loss is None:
            return None

        # 2. 计算止盈盈利
        tp_profit = self.calc_profit(symbol, volume, entry_price, tp_price, action)
        if tp_profit is None:
            return None

        # 3. 计算风险回报比
        risk_amount = abs(sl_loss)
        reward_amount = abs(tp_profit)

        if risk_amount == 0:
            logger.error("风险金额为0，无法计算风险回报比")
            return None

        risk_reward_ratio = reward_amount / risk_amount

        return {
            'sl_loss': sl_loss,
            'tp_profit': tp_profit,
            'risk_reward_ratio': risk_reward_ratio,
            'risk_amount': risk_amount,
            'reward_amount': reward_amount
        }

    def calc_position_size(
        self,
        symbol: str,
        risk_amount: float,
        entry_price: float,
        sl_price: float,
        action: str = 'buy'
    ) -> Optional[float]:
        """
        根据风险金额计算仓位大小

        此方法根据你愿意承担的风险金额，自动计算合适的交易量。
        这是专业交易者常用的资金管理方法。

        参数:
            symbol: 交易品种名称
            risk_amount: 愿意承担的风险金额（账户货币单位）
            entry_price: 入场价格
            sl_price: 止损价格
            action: 订单类型 ('buy' 或 'sell')

        返回:
            float: 建议的交易量（手数）
            None: 计算失败

        使用示例:
            # 示例 1: 风险固定金额
            # 假设账户余额 10000 USD，愿意冒 1% 风险（100 USD）
            volume = calculator.calc_position_size(
                symbol="EURUSD",
                risk_amount=100,
                entry_price=1.1000,
                sl_price=1.0950,
                action='buy'
            )
            if volume:
                print(f"建议交易量: {volume} 手")

            # 示例 2: 根据账户余额百分比计算
            account_info = mt5.account_info()
            balance = account_info.balance
            risk_percent = 0.01  # 1%
            risk_amount = balance * risk_percent

            volume = calculator.calc_position_size(
                symbol="EURUSD",
                risk_amount=risk_amount,
                entry_price=1.1000,
                sl_price=1.0950,
                action='buy'
            )

        注意事项:
            1. 返回的交易量可能需要根据品种的最小/最大交易量调整
            2. 建议使用账户余额的 1-2% 作为单笔交易风险
            3. 止损距离越大，交易量越小
        """
        # 1. 计算 1 手的亏损
        loss_per_lot = self.calc_profit(symbol, 1.0, entry_price, sl_price, action)
        if loss_per_lot is None:
            return None

        loss_per_lot = abs(loss_per_lot)

        if loss_per_lot == 0:
            logger.error("每手亏损为0，无法计算仓位")
            return None

        # 2. 计算交易量
        volume = risk_amount / loss_per_lot

        # 3. 获取品种信息，调整交易量
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            # 调整到最小交易量的整数倍
            volume_min = symbol_info.volume_min
            volume_max = symbol_info.volume_max
            volume_step = symbol_info.volume_step

            # 向下取整到步进值
            if volume_step > 0:
                volume = (volume // volume_step) * volume_step

            # 限制在最小/最大范围内
            volume = max(volume_min, min(volume, volume_max))

        return round(volume, 2)

    def _get_order_type(self, action: str) -> Optional[int]:
        """
        将字符串订单类型转换为 MT5 常量

        参数:
            action: 订单类型字符串

        返回:
            int: MT5 订单类型常量
            None: 无效的订单类型
        """
        action_map = {
            'buy': mt5.ORDER_TYPE_BUY,
            'sell': mt5.ORDER_TYPE_SELL,
            'buy_limit': mt5.ORDER_TYPE_BUY_LIMIT,
            'sell_limit': mt5.ORDER_TYPE_SELL_LIMIT,
            'buy_stop': mt5.ORDER_TYPE_BUY_STOP,
            'sell_stop': mt5.ORDER_TYPE_SELL_STOP,
        }

        return action_map.get(action.lower())
