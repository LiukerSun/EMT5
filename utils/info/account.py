import MetaTrader5 as mt5
from typing import Optional
from ..logger import logger


class MT5Account:
    """MT5 账户信息管理类"""

    def __init__(self, connection):
        """
        初始化账户管理器

        参数:
            connection: MT5Connection 实例
        """
        self.connection = connection

    def get_account_info(self) -> Optional[dict]:
        """
        获取账户信息

        返回:
            dict: 账户信息字典，包含余额、权益、保证金等信息，如果未连接则返回 None
        """
        if not self.connection.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        account_info = mt5.account_info()
        if account_info is not None:
            return account_info._asdict()
        return None
