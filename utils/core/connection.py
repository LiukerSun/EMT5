import MetaTrader5 as mt5
from typing import Optional
from ..logger import logger


class MT5Connection:
    """MT5 连接管理类"""

    def __init__(self):
        """初始化连接管理器"""
        self.connected = False
        self.login = None
        self.server = None

    def initialize(
        self,
        path: Optional[str] = None,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        timeout: int = 60000,
        portable: bool = False,
    ) -> bool:
        """
        建立与 MetaTrader 5 终端的连接

        参数:
            path: MT5 终端 EXE 文件路径（可选）
            login: 交易账户号码（可选）
            password: 交易账户密码（可选）
            server: 交易服务器名称（可选）
            timeout: 连接超时时间（毫秒），默认 60000
            portable: 便携模式标志，默认 False

        返回:
            bool: 连接成功返回 True，否则返回 False
        """
        try:
            # 根据参数构建初始化调用
            if path is None and login is None:
                result = mt5.initialize()
            elif login is not None:
                kwargs = {"login": login, "timeout": timeout, "portable": portable}
                if password is not None:
                    kwargs["password"] = password
                if server is not None:
                    kwargs["server"] = server

                if path is not None:
                    result = mt5.initialize(path, **kwargs)
                else:
                    result = mt5.initialize(**kwargs)
            else:
                result = mt5.initialize(path)

            if result:
                self.connected = True
                self.login = login
                self.server = server
                logger.info("已连接到 MetaTrader 5 终端")
                return True
            else:
                error = mt5.last_error()
                logger.error(f"initialize() 失败, 错误代码: {error}")
                self.connected = False
                return False

        except Exception as e:
            logger.error(f"连接异常: {str(e)}")
            self.connected = False
            return False

    def shutdown(self) -> None:
        """关闭与 MetaTrader 5 终端的连接"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("已断开 MetaTrader 5 连接")

    def is_connected(self) -> bool:
        """
        检查是否已连接到 MT5 终端

        返回:
            bool: 已连接返回 True，否则返回 False
        """
        return self.connected

    def get_terminal_info(self) -> Optional[dict]:
        """
        获取终端信息

        返回:
            dict: 终端信息字典，如果未连接则返回 None
        """
        if not self.connected:
            logger.error("未连接到 MT5 终端")
            return None

        info = mt5.terminal_info()
        if info is not None:
            return info._asdict()
        return None

    def get_version(self) -> Optional[tuple]:
        """
        获取 MetaTrader 5 版本信息

        返回:
            tuple: 版本信息元组，如果未连接则返回 None
        """
        if not self.connected:
            logger.error("未连接到 MT5 终端")
            return None

        return mt5.version()
