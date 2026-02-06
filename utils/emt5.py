"""
EMT5 - MetaTrader 5 Python 封装库

整合了连接管理、账户信息、品种信息、交易操作等功能
"""

from .core import MT5Connection
from .core.decorators import require_connection
from .info import MT5Account, MT5Symbol, MT5History, MT5Position
from .trade import MT5Executor, MT5Calculator, OrderRequestBuilder
from .logger import logger


class EMT5:
    """
    MetaTrader 5 封装类

    提供简洁的 API 来与 MT5 终端交互。

    使用示例:
        # 基本使用
        mt5 = EMT5()
        mt5.initialize()

        # 获取账户信息
        account = mt5.account.get_account_info()

        # 获取持仓
        positions = mt5.position.get_positions()

        # 链式调用下单
        result = (mt5.order("EURUSD")
            .market_buy(0.1)
            .with_sl(1.0950)
            .with_tp(1.1050)
            .send())

        mt5.shutdown()

        # 使用上下文管理器
        with EMT5() as mt5:
            mt5.initialize()
            # 执行操作
    """

    def __init__(self, default_magic: int = 0, keep_alive: bool = False):
        """
        初始化 EMT5 实例

        参数:
            default_magic: 默认 EA 标识号，默认 0
            keep_alive: 如果为 True，退出上下文管理器时不会断开连接
                       在 Django 等 Web 框架中，建议设置为 True
        """
        self._connection = MT5Connection()
        self._default_magic = default_magic
        self.keep_alive = keep_alive

        # 子模块
        self.account = MT5Account(self._connection)
        self.symbol = MT5Symbol(self._connection)
        self.position = MT5Position(self._connection)
        self.history = MT5History(self._connection)
        self.calculator = MT5Calculator(self._connection)
        self.executor = MT5Executor(self._connection, default_magic)

    # ==================== 连接管理 ====================

    def initialize(
        self,
        path=None,
        login=None,
        password=None,
        server=None,
        timeout=60000,
        portable=False,
    ):
        """
        建立与 MetaTrader 5 终端的连接

        参数:
            path: MT5 终端可执行文件的完整路径
            login: 交易账户号码（整数）
            password: 交易账户密码（字符串）
            server: 交易服务器名称
            timeout: 连接超时时间（毫秒），默认 60000
            portable: 是否使用便携模式

        返回:
            bool: 连接成功返回 True，失败抛出异常

        使用示例:
            mt5 = EMT5()

            # 自动连接
            mt5.initialize()

            # 指定账户信息
            mt5.initialize(
                login=12345678,
                password="your_password",
                server="XMGlobal-MT5 9"
            )
        """
        return self._connection.initialize(
            path, login, password, server, timeout, portable
        )

    def shutdown(self):
        """
        关闭与 MetaTrader 5 终端的连接

        使用示例:
            mt5 = EMT5()
            mt5.initialize()
            # ... 执行操作 ...
            mt5.shutdown()
        """
        self._connection.shutdown()

    def is_connected(self):
        """
        检查是否已连接到 MT5 终端

        返回:
            bool: 已连接返回 True，未连接返回 False
        """
        return self._connection.is_connected()

    def get_terminal_info(self):
        """获取终端信息"""
        return self._connection.get_terminal_info()

    def get_version(self):
        """获取 MetaTrader 5 版本信息"""
        return self._connection.get_version()

    def login(self, login, password=None, server=None, timeout=60000):
        """
        连接到指定的交易账户

        此方法用于在已初始化的 MT5 终端中切换到不同的交易账户。

        参数:
            login: 交易账户号码（整数，必填）
            password: 交易账户密码（可选）
            server: 交易服务器名称（可选）
            timeout: 连接超时时间（毫秒），默认 60000

        返回:
            bool: 连接成功返回 True，失败返回 False

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 切换账户
            if mt5.login(17221085):
                print("切换成功")

            # 指定密码和服务器
            mt5.login(25115284, password="pwd", server="MetaQuotes-Demo")
        """
        return self._connection.login(login, password, server, timeout)

    # ==================== 订单构建器 ====================

    def order(self, symbol: str) -> OrderRequestBuilder:
        """
        创建订单构建器

        参数:
            symbol: 交易品种名称

        返回:
            OrderRequestBuilder: 订单构建器实例

        使用示例:
            # 市价买入
            result = mt5.order("EURUSD").market_buy(0.1).send()

            # 带止损止盈
            result = (mt5.order("EURUSD")
                .market_buy(0.1)
                .with_sl(1.0950)
                .with_tp(1.1050)
                .send())

            # 限价挂单
            result = (mt5.order("GOLD")
                .limit_buy(0.01, 1950.00)
                .with_sl(1940.00)
                .with_tp(1970.00)
                .send())

            # 只构建不发送
            request = mt5.order("EURUSD").market_buy(0.1).build()

            # 检查订单
            check = mt5.order("EURUSD").market_buy(0.1).check()
        """
        return OrderRequestBuilder(
            symbol, self._connection, self.executor, self._default_magic
        )

    # ==================== 上下文管理器 ====================

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出时根据配置决定是否关闭连接

        如果 keep_alive=True（Web 服务模式），则不会断开连接
        如果 keep_alive=False（脚本模式），则自动断开连接
        """
        if not self.keep_alive:
            self.shutdown()
        return False

    def __del__(self):
        """析构时确保连接已关闭"""
        if self.is_connected():
            self.shutdown()
