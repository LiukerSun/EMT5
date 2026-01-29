"""
MT5 历史数据模块

提供K线数据、Tick数据、历史订单和历史成交的查询功能
"""

import MetaTrader5 as mt5
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from ..logger import logger


class MT5History:
    """MT5 历史数据查询类"""

    def __init__(self, connection):
        """
        初始化历史数据管理器

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    def get_bars(
        self,
        symbol: str,
        timeframe: int,
        date_from: Optional[Union[datetime, int]] = None,
        date_to: Optional[Union[datetime, int]] = None,
        count: Optional[int] = None,
        start_pos: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        统一的K线数据获取方法（合并了3个原生函数）

        此方法整合了 MT5 的三个 K线获取函数：
        - copy_rates_from: 从指定时间获取N根K线
        - copy_rates_from_pos: 从指定位置获取N根K线
        - copy_rates_range: 获取时间范围内的K线

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD#"
            timeframe: 时间周期，使用 mt5.TIMEFRAME_* 常量
                - mt5.TIMEFRAME_M1: 1分钟
                - mt5.TIMEFRAME_M5: 5分钟
                - mt5.TIMEFRAME_H1: 1小时
                - mt5.TIMEFRAME_D1: 1天
                等等...
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳）
            count: 获取的K线数量
            start_pos: 起始位置索引（0表示当前K线）

        参数组合方式:
            1. date_from + count: 从指定时间获取N根K线
            2. start_pos + count: 从指定位置获取N根K线（0是当前K线）
            3. date_from + date_to: 获取时间范围内的所有K线

        返回:
            List[Dict]: K线数据列表，每根K线包含以下字段：
                - time: K线开盘时间（Unix时间戳，秒）
                - time_dt: K线开盘时间（带时区的 datetime 对象，UTC）
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - tick_volume: Tick成交量
                - spread: 点差
                - real_volume: 真实成交量
            失败时返回 None

        使用示例:
            # 示例 1: 获取最近100根H1 K线
            bars = history.get_bars("EURUSD", mt5.TIMEFRAME_H1, start_pos=0, count=100)

            # 示例 2: 从指定时间获取50根K线
            from datetime import datetime, timezone
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
            bars = history.get_bars("EURUSD", mt5.TIMEFRAME_D1, date_from=start_time, count=50)

            # 示例 3: 获取时间范围内的所有K线
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 31, tzinfo=timezone.utc)
            bars = history.get_bars("EURUSD", mt5.TIMEFRAME_H4, date_from=start, date_to=end)

            # 示例 4: 使用时间戳
            bars = history.get_bars("GOLD#", mt5.TIMEFRAME_M5, date_from=1704067200, count=100)

        注意事项:
            1. 时间必须使用 UTC 时区
            2. MT5 只提供图表历史范围内的数据
            3. 可用数据量受 "Max. bars in chart" 参数限制
            4. start_pos=0 表示当前K线，1表示上一根K线，以此类推
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        # 2. 参数验证
        if start_pos is not None and count is not None:
            # 模式1: 从指定位置获取N根K线
            return self._get_bars_from_pos(symbol, timeframe, start_pos, count)
        elif date_from is not None and count is not None and date_to is None:
            # 模式2: 从指定时间获取N根K线
            return self._get_bars_from_date(symbol, timeframe, date_from, count)
        elif date_from is not None and date_to is not None and count is None:
            # 模式3: 获取时间范围内的K线
            return self._get_bars_range(symbol, timeframe, date_from, date_to)
        else:
            logger.error("参数组合无效，请使用以下组合之一：")
            logger.error("1. start_pos + count")
            logger.error("2. date_from + count")
            logger.error("3. date_from + date_to")
            return None

    def _get_bars_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """从指定位置获取K线数据"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)

            if rates is None:
                error = mt5.last_error()
                logger.error(
                    f"copy_rates_from_pos({symbol}, {timeframe}, {start_pos}, {count}) 失败, 错误代码: {error}"
                )
                return None

            # 转换为字典列表并添加时区感知时间
            return self._convert_bars_to_dict(rates)

        except Exception as e:
            logger.error(f"获取K线数据异常: {str(e)}")
            return None

    def _get_bars_from_date(
        self, symbol: str, timeframe: int, date_from: Union[datetime, int], count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """从指定时间获取K线数据"""
        try:
            # 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                # 确保是 UTC 时区
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            rates = mt5.copy_rates_from(symbol, timeframe, date_from, count)

            if rates is None:
                error = mt5.last_error()
                logger.error(
                    f"copy_rates_from({symbol}, {timeframe}, {date_from}, {count}) 失败, 错误代码: {error}"
                )
                return None

            # 转换为字典列表并添加时区感知时间
            return self._convert_bars_to_dict(rates)

        except Exception as e:
            logger.error(f"获取K线数据异常: {str(e)}")
            return None

    def _get_bars_range(
        self,
        symbol: str,
        timeframe: int,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
    ) -> Optional[List[Dict[str, Any]]]:
        """获取时间范围内的K线数据"""
        try:
            # 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    logger.warning("date_to 没有时区信息，假定为 UTC")
                    date_to = date_to.replace(tzinfo=timezone.utc)

            rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)

            if rates is None:
                error = mt5.last_error()
                logger.error(
                    f"copy_rates_range({symbol}, {timeframe}, {date_from}, {date_to}) 失败, 错误代码: {error}"
                )
                return None

            # 转换为字典列表并添加时区感知时间
            return self._convert_bars_to_dict(rates)

        except Exception as e:
            logger.error(f"获取K线数据异常: {str(e)}")
            return None

    def _convert_bars_to_dict(self, rates) -> List[Dict[str, Any]]:
        """
        将 numpy 数组转换为字典列表，并添加时区感知时间

        参数:
            rates: MT5 返回的 numpy 数组

        返回:
            List[Dict]: 转换后的字典列表
        """
        bars = []
        for rate in rates:
            bar = {
                'time': int(rate['time']),
                'open': float(rate['open']),
                'high': float(rate['high']),
                'low': float(rate['low']),
                'close': float(rate['close']),
                'tick_volume': int(rate['tick_volume']),
                'spread': int(rate['spread']),
                'real_volume': int(rate['real_volume']),
            }

            # 添加时区感知的 datetime 对象（Django 友好）
            bar['time_dt'] = datetime.fromtimestamp(bar['time'], tz=timezone.utc)

            bars.append(bar)

        return bars

    def get_ticks(
        self,
        symbol: str,
        date_from: Union[datetime, int],
        date_to: Optional[Union[datetime, int]] = None,
        count: Optional[int] = None,
        flags: int = mt5.COPY_TICKS_ALL,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        统一的Tick数据获取方法（合并了2个原生函数）

        此方法整合了 MT5 的两个 Tick 获取函数：
        - copy_ticks_from: 从指定时间获取N个tick
        - copy_ticks_range: 获取时间范围内的tick

        参数:
            symbol: 交易品种名称
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳，可选）
            count: 获取的tick数量（可选）
            flags: Tick类型标志，可选值：
                - mt5.COPY_TICKS_ALL: 所有tick（默认）
                - mt5.COPY_TICKS_INFO: 仅价格变化的tick
                - mt5.COPY_TICKS_TRADE: 仅成交tick

        参数组合方式:
            1. date_from + count: 从指定时间获取N个tick
            2. date_from + date_to: 获取时间范围内的所有tick

        返回:
            List[Dict]: Tick数据列表，每个tick包含：
                - time: tick时间（Unix时间戳，秒）
                - time_dt: tick时间（带时区的 datetime 对象，UTC）
                - time_msc: tick时间（毫秒）
                - time_msc_dt: tick时间（带时区的 datetime 对象，毫秒级精度，UTC）
                - bid: 买入价
                - ask: 卖出价
                - last: 最后成交价
                - volume: 成交量
                - flags: tick标志
            失败时返回 None

        使用示例:
            # 示例 1: 获取最近1000个tick
            from datetime import datetime, timezone
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            ticks = history.get_ticks("EURUSD", date_from=start, count=1000)

            # 示例 2: 获取时间范围内的所有tick
            start = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
            end = datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc)
            ticks = history.get_ticks("EURUSD", date_from=start, date_to=end)

            # 示例 3: 只获取成交tick
            ticks = history.get_ticks(
                "EURUSD",
                date_from=start,
                count=1000,
                flags=mt5.COPY_TICKS_TRADE
            )
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        # 2. 参数验证
        if date_to is not None and count is None:
            # 模式1: 获取时间范围内的tick
            return self._get_ticks_range(symbol, date_from, date_to, flags)
        elif count is not None and date_to is None:
            # 模式2: 从指定时间获取N个tick
            return self._get_ticks_from(symbol, date_from, count, flags)
        else:
            logger.error("参数组合无效，请使用以下组合之一：")
            logger.error("1. date_from + count")
            logger.error("2. date_from + date_to")
            return None

    def _get_ticks_from(
        self, symbol: str, date_from: Union[datetime, int], count: int, flags: int
    ) -> Optional[List[Dict[str, Any]]]:
        """从指定时间获取tick数据"""
        try:
            # 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            ticks = mt5.copy_ticks_from(symbol, date_from, count, flags)

            if ticks is None:
                error = mt5.last_error()
                logger.error(
                    f"copy_ticks_from({symbol}, {date_from}, {count}, {flags}) 失败, 错误代码: {error}"
                )
                return None

            # 转换为字典列表并添加时区感知时间
            return self._convert_ticks_to_dict(ticks)

        except Exception as e:
            logger.error(f"获取Tick数据异常: {str(e)}")
            return None

    def _get_ticks_range(
        self,
        symbol: str,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
        flags: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """获取时间范围内的tick数据"""
        try:
            # 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    logger.warning("date_to 没有时区信息，假定为 UTC")
                    date_to = date_to.replace(tzinfo=timezone.utc)

            ticks = mt5.copy_ticks_range(symbol, date_from, date_to, flags)

            if ticks is None:
                error = mt5.last_error()
                logger.error(
                    f"copy_ticks_range({symbol}, {date_from}, {date_to}, {flags}) 失败, 错误代码: {error}"
                )
                return None

            # 转换为字典列表并添加时区感知时间
            return self._convert_ticks_to_dict(ticks)

        except Exception as e:
            logger.error(f"获取Tick数据异常: {str(e)}")
            return None

    def _convert_ticks_to_dict(self, ticks) -> List[Dict[str, Any]]:
        """
        将 numpy 数组转换为字典列表，并添加时区感知时间

        参数:
            ticks: MT5 返回的 numpy 数组

        返回:
            List[Dict]: 转换后的字典列表
        """
        tick_list = []
        for tick in ticks:
            tick_dict = {
                'time': int(tick['time']),
                'bid': float(tick['bid']),
                'ask': float(tick['ask']),
                'last': float(tick['last']),
                'volume': int(tick['volume']),
                'time_msc': int(tick['time_msc']),
                'flags': int(tick['flags']),
            }

            # 添加时区感知的 datetime 对象（Django 友好）
            tick_dict['time_dt'] = datetime.fromtimestamp(tick_dict['time'], tz=timezone.utc)
            tick_dict['time_msc_dt'] = datetime.fromtimestamp(
                tick_dict['time_msc'] / 1000.0, tz=timezone.utc
            )

            tick_list.append(tick_dict)

        return tick_list

    def get_history_orders(
        self,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
        group: str = "",
        ticket: int = 0,
        position: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        获取历史订单（自动包含总数）

        参数:
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳）
            group: 品种组过滤，例如 "*EUR*"
            ticket: 订单票据号过滤
            position: 持仓票据号过滤

        返回:
            Dict: 包含总数和订单列表的字典：
                {
                    'total': 订单总数,
                    'orders': [订单列表]
                }
            失败时返回 None

        使用示例:
            from datetime import datetime, timezone

            # 获取2024年1月的所有历史订单
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
            result = history.get_history_orders(start, end)

            if result:
                print(f"共有 {result['total']} 个历史订单")
                for order in result['orders']:
                    print(f"订单号: {order['ticket']}, 品种: {order['symbol']}")
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            # 2. 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    logger.warning("date_to 没有时区信息，假定为 UTC")
                    date_to = date_to.replace(tzinfo=timezone.utc)

            # 3. 调用 MT5 API
            if ticket > 0:
                orders = mt5.history_orders_get(ticket=ticket)
            elif position > 0:
                orders = mt5.history_orders_get(position=position)
            elif group:
                orders = mt5.history_orders_get(date_from, date_to, group=group)
            else:
                orders = mt5.history_orders_get(date_from, date_to)

            # 4. 错误处理
            if orders is None:
                error = mt5.last_error()
                logger.error(f"history_orders_get() 失败, 错误代码: {error}")
                return None

            # 5. 转换为字典列表
            order_list = []
            for order in orders:
                order_dict = order._asdict()

                # 添加时区感知的时间字段
                time_fields = ['time_setup', 'time_expiration', 'time_done']
                for field in time_fields:
                    if field in order_dict and order_dict[field] > 0:
                        order_dict[f'{field}_dt'] = datetime.fromtimestamp(
                            order_dict[field], tz=timezone.utc
                        )

                order_list.append(order_dict)

            # 6. 返回包含总数的字典
            return {
                'total': len(order_list),
                'orders': order_list
            }

        except Exception as e:
            logger.error(f"获取历史订单异常: {str(e)}")
            return None

    def get_history_deals(
        self,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
        group: str = "",
        ticket: int = 0,
        position: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        获取历史成交（自动包含总数）

        参数:
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳）
            group: 品种组过滤，例如 "*EUR*"
            ticket: 成交票据号过滤
            position: 持仓票据号过滤

        返回:
            Dict: 包含总数和成交列表的字典：
                {
                    'total': 成交总数,
                    'deals': [成交列表]
                }
            失败时返回 None

        使用示例:
            from datetime import datetime, timezone

            # 获取2024年1月的所有历史成交
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
            result = history.get_history_deals(start, end)

            if result:
                print(f"共有 {result['total']} 笔成交")
                total_profit = sum(deal['profit'] for deal in result['deals'])
                print(f"总盈亏: {total_profit}")
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            # 2. 转换 datetime 为时间戳（如果需要）
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    logger.warning("date_from 没有时区信息，假定为 UTC")
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    logger.warning("date_to 没有时区信息，假定为 UTC")
                    date_to = date_to.replace(tzinfo=timezone.utc)

            # 3. 调用 MT5 API
            if ticket > 0:
                deals = mt5.history_deals_get(ticket=ticket)
            elif position > 0:
                deals = mt5.history_deals_get(position=position)
            elif group:
                deals = mt5.history_deals_get(date_from, date_to, group=group)
            else:
                deals = mt5.history_deals_get(date_from, date_to)

            # 4. 错误处理
            if deals is None:
                error = mt5.last_error()
                logger.error(f"history_deals_get() 失败, 错误代码: {error}")
                return None

            # 5. 转换为字典列表
            deal_list = []
            for deal in deals:
                deal_dict = deal._asdict()

                # 添加时区感知的时间字段
                if 'time' in deal_dict and deal_dict['time'] > 0:
                    deal_dict['time_dt'] = datetime.fromtimestamp(
                        deal_dict['time'], tz=timezone.utc
                    )

                # 如果有毫秒级时间
                if 'time_msc' in deal_dict and deal_dict['time_msc'] > 0:
                    deal_dict['time_msc_dt'] = datetime.fromtimestamp(
                        deal_dict['time_msc'] / 1000.0, tz=timezone.utc
                    )

                deal_list.append(deal_dict)

            # 6. 返回包含总数的字典
            return {
                'total': len(deal_list),
                'deals': deal_list
            }

        except Exception as e:
            logger.error(f"获取历史成交异常: {str(e)}")
            return None

    def get_history_deals_total(
        self,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
    ) -> Optional[int]:
        """
        获取历史成交总数

        参数:
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳）

        返回:
            int: 历史成交总数，失败时返回 None

        使用示例:
            from datetime import datetime, timezone

            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 12, 31, tzinfo=timezone.utc)
            total = history.get_history_deals_total(start, end)
            print(f"历史成交总数: {total}")
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    date_to = date_to.replace(tzinfo=timezone.utc)

            total = mt5.history_deals_total(date_from, date_to)
            return total

        except Exception as e:
            logger.error(f"获取历史成交总数异常: {str(e)}")
            return None

    def get_history_orders_total(
        self,
        date_from: Union[datetime, int],
        date_to: Union[datetime, int],
    ) -> Optional[int]:
        """
        获取历史订单总数

        参数:
            date_from: 起始时间（datetime 对象或时间戳）
            date_to: 结束时间（datetime 对象或时间戳）

        返回:
            int: 历史订单总数，失败时返回 None

        使用示例:
            from datetime import datetime, timezone

            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 12, 31, tzinfo=timezone.utc)
            total = history.get_history_orders_total(start, end)
            print(f"历史订单总数: {total}")
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            if isinstance(date_from, datetime):
                if date_from.tzinfo is None:
                    date_from = date_from.replace(tzinfo=timezone.utc)

            if isinstance(date_to, datetime):
                if date_to.tzinfo is None:
                    date_to = date_to.replace(tzinfo=timezone.utc)

            total = mt5.history_orders_total(date_from, date_to)
            return total

        except Exception as e:
            logger.error(f"获取历史订单总数异常: {str(e)}")
            return None
