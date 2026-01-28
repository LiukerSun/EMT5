"""
多账户管理器

使用工厂模式和单例模式管理多个 MT5 账户
"""

from __future__ import annotations
import threading
from typing import Dict, Optional, List, TYPE_CHECKING
from ..logger import logger

if TYPE_CHECKING:
    from ..emt5 import EMT5


class MT5AccountManager:
    """
    MT5 账户管理器（单例模式）

    用于管理多个 MT5 账户连接，支持快速切换和批量操作
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.accounts: Dict[str, EMT5] = {}
        self.current_account: Optional[str] = None
        self._lock = threading.Lock()  # 线程锁
        self._initialized = True

    def add_account(
        self,
        name: str,
        login: int,
        password: str,
        server: str,
        path: Optional[str] = None,
        auto_connect: bool = True,
    ) -> bool:
        """
        添加账户

        参数:
            name: 账户别名（用于识别）
            login: MT5 账户号
            password: 密码
            server: 服务器名称
            path: MT5 路径（可选）
            auto_connect: 是否自动连接，默认 True

        返回:
            bool: 添加成功返回 True
        """
        with self._lock:
            # 延迟导入避免循环依赖
            from ..emt5 import EMT5

            if name in self.accounts:
                logger.warning(f"账户 '{name}' 已存在")
                return False

            client = EMT5()

            if auto_connect:
                try:
                    if not client.initialize(
                        path=path, login=login, password=password, server=server
                    ):
                        logger.error(f"账户 '{name}' 连接失败")
                        return False
                except Exception as e:
                    logger.error(f"账户 '{name}' 连接异常: {str(e)}")
                    return False

            self.accounts[name] = client

            # 如果是第一个账户，设为当前账户
            if self.current_account is None:
                self.current_account = name

            logger.info(f"账户 '{name}' 已添加")
            return True

    def remove_account(self, name: str) -> bool:
        """
        移除账户

        参数:
            name: 账户别名

        返回:
            bool: 移除成功返回 True
        """
        with self._lock:
            if name not in self.accounts:
                logger.error(f"账户 '{name}' 不存在")
                return False

            # 断开连接
            self.accounts[name].shutdown()

            # 移除账户
            del self.accounts[name]

            # 如果移除的是当前账户，切换到第一个可用账户
            if self.current_account == name:
                self.current_account = next(iter(self.accounts), None)

            logger.info(f"账户 '{name}' 已移除")
            return True

    def switch_account(self, name: str) -> bool:
        """
        切换当前账户

        参数:
            name: 账户别名

        返回:
            bool: 切换成功返回 True
        """
        with self._lock:
            if name not in self.accounts:
                logger.error(f"账户 '{name}' 不存在")
                return False

            self.current_account = name
            logger.info(f"已切换到账户 '{name}'")
            return True

    def get_account(self, name: Optional[str] = None) -> Optional[EMT5]:
        """
        获取账户实例

        参数:
            name: 账户别名，如果为 None 则返回当前账户

        返回:
            EMT5: 账户实例，如果不存在返回 None
        """
        with self._lock:
            if name is None:
                name = self.current_account

            return self.accounts.get(name)

    def get_current_account(self) -> Optional[EMT5]:
        """获取当前账户实例"""
        return self.get_account()

    def list_accounts(self) -> List[str]:
        """
        列出所有账户

        返回:
            List[str]: 账户别名列表
        """
        with self._lock:
            return list(self.accounts.keys())

    def execute_on_all(self, func_name: str, *args, **kwargs) -> Dict[str, any]:
        """
        在所有账户上执行相同操作

        参数:
            func_name: 方法名称
            *args, **kwargs: 方法参数

        返回:
            Dict[str, any]: 每个账户的执行结果
        """
        results = {}

        for name, client in self.accounts.items():
            if not client.is_connected():
                results[name] = {"error": "未连接"}
                continue

            try:
                method = getattr(client, func_name)
                result = method(*args, **kwargs)
                results[name] = result
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def shutdown_all(self) -> None:
        """断开所有账户连接"""
        for name, client in self.accounts.items():
            if client.is_connected():
                client.shutdown()
                logger.info(f"账户 '{name}' 已断开")

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动断开所有连接"""
        self.shutdown_all()
        return False
