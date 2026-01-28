"""
MT5 连接管理服务

提供单例模式的 MT5 连接管理，确保整个 Django 应用共享同一个连接
"""

from django.conf import settings
from utils import EMT5, logger


class MT5Service:
    """MT5 服务单例类"""

    _instance = None
    _mt5 = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._mt5 is None:
            # 从配置中获取参数
            default_magic = getattr(settings, 'MT5_CONFIG', {}).get('DEFAULT_MAGIC', 0)
            keep_alive = getattr(settings, 'MT5_CONFIG', {}).get('KEEP_ALIVE', True)

            # 创建 EMT5 实例，keep_alive=True 适配 Web 服务
            self._mt5 = EMT5(default_magic=default_magic, keep_alive=keep_alive)
            logger.info("MT5 服务已初始化")

    @property
    def mt5(self):
        """获取 MT5 实例"""
        return self._mt5

    def initialize(self, path=None, login=None, password=None, server=None, timeout=60000, portable=False):
        """
        初始化 MT5 连接

        参数:
            path: MT5 终端路径
            login: 账户号码
            password: 账户密码
            server: 服务器名称
            timeout: 超时时间（毫秒）
            portable: 是否使用便携模式

        返回:
            bool: 连接成功返回 True
        """
        print(path, login, password, server, timeout, portable)
        return self._mt5.initialize(path, login, password, server, timeout, portable)

    def shutdown(self):
        """关闭 MT5 连接"""
        if self._mt5:
            self._mt5.shutdown()

    def is_connected(self):
        """检查是否已连接"""
        return self._mt5.is_connected() if self._mt5 else False


# 创建全局单例实例
mt5_service = MT5Service()
