import MetaTrader5 as mt5
from typing import Optional
from datetime import datetime, timezone
from ..logger import logger


class MT5Symbol:
    """MT5 交易品种管理类"""

    def __init__(self, connection):
        """
        初始化品种管理器

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    def get_symbols(self, group: str = "*") -> Optional[tuple]:
        """
        获取所有金融交易品种（完整信息）

        参数:
            group: 品种筛选过滤器，默认 "*" 表示所有品种

        返回:
            tuple: 品种信息元组，如果未连接或失败则返回 None
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            symbols = mt5.symbols_get(group=group)
            if symbols is None:
                error = mt5.last_error()
                logger.error(f"symbols_get() 失败, 错误代码: {error}")
                return None
            return symbols
        except Exception as e:
            logger.error(f"获取品种信息异常: {str(e)}")
            return None

    def get_symbol_names(self, group: str = "*") -> Optional[list]:
        """
        获取所有金融交易品种名称列表（仅名称）

        参数:
            group: 品种筛选过滤器，默认 "*" 表示所有品种

        返回:
            list: 品种名称列表，例如 ["EURUSD", "GBPUSD", "GOLD#"]
                 如果未连接或失败则返回 None
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            symbols = mt5.symbols_get(group=group)
            if symbols is None:
                error = mt5.last_error()
                logger.error(f"symbols_get() 失败, 错误代码: {error}")
                return None
            # 只提取品种名称
            return [symbol.name for symbol in symbols]
        except Exception as e:
            logger.error(f"获取品种名称异常: {str(e)}")
            return None

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        获取指定品种的详细信息

        参数:
            symbol: 品种名称，例如 "EURUSD"

        返回:
            dict: 品种详细信息字典，如果未连接或失败则返回 None
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                error = mt5.last_error()
                logger.error(f"symbol_info({symbol}) 失败, 错误代码: {error}")
                return None
            return symbol_info._asdict()
        except Exception as e:
            logger.error(f"获取品种信息异常: {str(e)}")
            return None

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """
        在市场观察窗口中启用或禁用指定品种

        参数:
            symbol: 品种名称，例如 "EURUSD"
            enable: True 为启用，False 为禁用，默认 True

        返回:
            bool: 操作成功返回 True，否则返回 False
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return False

        try:
            result = mt5.symbol_select(symbol, enable)
            if not result:
                error = mt5.last_error()
                logger.error(
                    f"symbol_select({symbol}, {enable}) 失败, 错误代码: {error}"
                )
                return False
            action = "启用" if enable else "禁用"
            logger.info(f"已{action}品种 {symbol}")
            return True
        except Exception as e:
            logger.error(f"选择品种异常: {str(e)}")
            return False

    def get_symbol_info_tick(self, symbol: str) -> Optional[dict]:
        """
        获取指定品种的最新tick数据（实时报价）

        此方法用于获取品种的最新价格信息，包括买价、卖价、成交价、成交量等。
        适用于需要实时监控价格变化的场景。

        参数:
            symbol: 品种名称，例如 "EURUSD", "GOLD_", "BTCUSD"

        返回:
            Dict: tick数据字典，包含以下字段：
                - time: tick时间（Unix时间戳，秒）
                - time_dt: tick时间（带时区的 datetime 对象，UTC）
                - bid: 当前买入价（Bid）
                - ask: 当前卖出价（Ask）
                - last: 最后成交价
                - volume: 成交量
                - time_msc: tick时间（Unix时间戳，毫秒）
                - time_msc_dt: tick时间（带时区的 datetime 对象，毫秒级精度，UTC）
                - flags: tick标志
                - volume_real: 实际成交量
            失败时返回 None

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 获取最新tick数据
            tick = mt5.get_symbol_info_tick("EURUSD")
            if tick:
                print(f"买价: {tick['bid']}")
                print(f"卖价: {tick['ask']}")
                print(f"点差: {tick['ask'] - tick['bid']}")
                print(f"时间: {tick['time_dt']}")  # Django 友好的时区感知时间

            # 实时监控价格
            while True:
                tick = mt5.get_symbol_info_tick("GOLD_")
                if tick:
                    print(f"黄金价格: {tick['ask']}")
                time.sleep(1)

        注意事项:
            1. 调用前必须先启用品种（使用 symbol_select）
            2. 返回的是最新的tick数据，不是历史数据
            3. time 字段是秒级时间戳，time_msc 是毫秒级时间戳
            4. time_dt 和 time_msc_dt 是带时区的 datetime 对象（UTC），适配 Django
            5. bid 用于卖出，ask 用于买入
            6. 高频调用时注意性能影响
        """
        # 1. 检查连接状态
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        # 2. 调用 MT5 API 获取tick数据
        try:
            tick = mt5.symbol_info_tick(symbol)

            # 3. 错误处理
            if tick is None:
                error = mt5.last_error()
                logger.error(f"symbol_info_tick({symbol}) 失败, 错误代码: {error}")
                return None

            # 4. 转换为字典格式
            tick_dict = tick._asdict()

            # 5. 将时间戳转换为带时区的 datetime 对象（Django 友好）
            # MT5 的 time 字段通常是 UTC 时间戳
            if "time" in tick_dict and tick_dict["time"]:
                tick_dict["time_dt"] = datetime.fromtimestamp(
                    tick_dict["time"], tz=timezone.utc
                )

            # 6. 如果需要毫秒级精度
            if "time_msc" in tick_dict and tick_dict["time_msc"]:
                tick_dict["time_msc_dt"] = datetime.fromtimestamp(
                    tick_dict["time_msc"] / 1000.0, tz=timezone.utc
                )

            return tick_dict

        except Exception as e:
            logger.error(f"获取tick数据异常: {str(e)}")
            return None
