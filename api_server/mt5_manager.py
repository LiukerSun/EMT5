"""
MT5 连接守护管理器

负责：
1. 守护 MT5 终端运行（始终保持 initialize 状态）
2. 缓存连接和登录状态
3. 提供状态检查，避免不必要的 MT5 调用
"""
import threading
import logging
import MetaTrader5 as mt5
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class MT5Manager:
    """
    MT5 连接守护管理器（单例）

    - 始终保持 MT5 终端连接（initialize）
    - 登录状态由用户通过 API 控制
    - 缓存状态，避免重复调用 MT5
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._mt5_connected = False  # MT5 终端是否已连接
        self._account_logged_in = False  # 是否已登录账户
        self._account_info = None  # 缓存的账户信息
        self._emt5 = None  # EMT5 实例
        self._state_lock = threading.Lock()
        self._connecting = False  # 防止重复连接

        # 不在启动时连接 MT5，等用户调用登录 API 时再连接
        # self._connect_terminal()

    def _connect_terminal(self):
        """连接 MT5 终端（不登录账户）"""
        if self._connecting:
            return

        with self._state_lock:
            if self._mt5_connected:
                return

            self._connecting = True
            try:
                logger.info("正在连接 MT5 终端...")

                # 先关闭可能存在的旧连接
                try:
                    mt5.shutdown()
                except Exception:
                    pass

                # 初始化连接，不传入登录信息
                # portable=True 可以避免弹出登录窗口
                if mt5.initialize():
                    self._mt5_connected = True
                    logger.info("MT5 终端连接成功")
                    # 注意：即使 MT5 自动登录了账户，我们也不缓存状态
                    # 强制用户通过 API 显式登录
                    self._account_logged_in = False
                    self._account_info = None
                    logger.info("MT5 终端已连接，等待用户登录")
                else:
                    error = mt5.last_error()
                    logger.error(f"MT5 终端连接失败: {error}")
                    self._mt5_connected = False
            except Exception as e:
                logger.exception(f"MT5 连接异常: {e}")
                self._mt5_connected = False
            finally:
                self._connecting = False

    def ensure_terminal(self):
        """确保 MT5 终端已连接"""
        if not self._mt5_connected:
            self._connect_terminal()
        return self._mt5_connected

    @property
    def is_terminal_connected(self) -> bool:
        """MT5 终端是否已连接"""
        return self._mt5_connected

    @property
    def is_logged_in(self) -> bool:
        """是否已登录账户"""
        return self._account_logged_in

    @property
    def account_info(self) -> dict | None:
        """获取缓存的账户信息"""
        return self._account_info

    def refresh_account_status(self):
        """刷新账户状态"""
        with self._state_lock:
            if self._mt5_connected:
                account = mt5.account_info()
                if account and account.login > 0:
                    self._account_logged_in = True
                    self._account_info = account._asdict()
                else:
                    self._account_logged_in = False
                    self._account_info = None

    def login(self, login: int, password: str, server: str) -> dict:
        """
        登录账户（同时初始化 MT5 终端）

        Returns:
            dict: {'success': bool, 'message': str, 'account': dict|None}
        """
        with self._state_lock:
            try:
                logger.info(f"正在登录账户 {login}@{server}...")

                # 先关闭可能存在的旧连接
                try:
                    mt5.shutdown()
                except Exception:
                    pass

                # 使用账户信息初始化（这样不会弹出登录窗口）
                if mt5.initialize(login=login, password=password, server=server):
                    self._mt5_connected = True
                    account = mt5.account_info()
                    if account and account.login > 0:
                        self._account_logged_in = True
                        self._account_info = account._asdict()
                        logger.info(f"登录成功: {account.login}")
                        return {
                            'success': True,
                            'message': '登录成功',
                            'account': self._account_info
                        }
                    else:
                        self._account_logged_in = False
                        error = mt5.last_error()
                        logger.error(f"登录失败: {error}")
                        return {
                            'success': False,
                            'message': f'登录失败: {error}',
                            'account': None
                        }
                else:
                    error = mt5.last_error()
                    logger.error(f"MT5 初始化失败: {error}")
                    self._mt5_connected = False
                    return {
                        'success': False,
                        'message': f'MT5 初始化失败: {error}',
                        'account': None
                    }

            except Exception as e:
                logger.exception(f"登录异常: {e}")
                return {
                    'success': False,
                    'message': f'登录异常: {e}',
                    'account': None
                }

    def logout(self):
        """登出账户（实际上 MT5 不支持登出，只能切换账户或关闭）"""
        with self._state_lock:
            self._account_logged_in = False
            self._account_info = None

    def get_emt5(self):
        """获取 EMT5 实例（用于需要完整功能的场景）"""
        if self._emt5 is None:
            from utils import EMT5
            self._emt5 = EMT5(keep_alive=True)
        # 同步连接状态
        if self._mt5_connected:
            self._emt5._connection.connected = True
        return self._emt5

    def get_account_info(self) -> dict | None:
        """直接获取账户信息"""
        if not self._mt5_connected or not self._account_logged_in:
            return None
        account = mt5.account_info()
        if account:
            return account._asdict()
        return None

    def get_status(self) -> dict:
        """获取当前状态"""
        self.refresh_account_status()
        return {
            'terminal_connected': self._mt5_connected,
            'account_logged_in': self._account_logged_in,
            'account': self._account_info,
            'terminal_info': mt5.terminal_info()._asdict() if self._mt5_connected else None
        }


# 全局单例
mt5_manager = MT5Manager()


def require_login(func):
    """
    装饰器：要求已登录账户

    在 Django 视图层检查登录状态，未登录直接返回 401 错误，
    避免不必要的 MT5 调用
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not mt5_manager.is_terminal_connected:
            return Response(
                {'error': 'MT5 终端未连接', 'code': 'TERMINAL_NOT_CONNECTED'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not mt5_manager.is_logged_in:
            return Response(
                {'error': '未登录交易账户', 'code': 'NOT_LOGGED_IN'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return func(request, *args, **kwargs)

    return wrapper


def require_terminal(func):
    """
    装饰器：要求 MT5 终端已连接（不要求登录）
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not mt5_manager.ensure_terminal():
            return Response(
                {'error': 'MT5 终端未连接', 'code': 'TERMINAL_NOT_CONNECTED'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return func(request, *args, **kwargs)

    return wrapper
