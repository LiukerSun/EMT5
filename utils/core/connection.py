import MetaTrader5 as mt5
import time
from typing import Optional
from ..logger import logger
from ..exceptions import MT5ConnectionError


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
        retry: int = 3,
        retry_delay: float = 2.0,
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
            retry: 重试次数，默认 3
            retry_delay: 重试间隔（秒），默认 2.0

        返回:
            bool: 连接成功返回 True，否则抛出异常

        异常:
            MT5ConnectionError: 连接失败时抛出
        """
        last_error = None

        for attempt in range(retry):
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

                # 如果初始化失败且错误是IPC通信失败，尝试启动MT5终端
                if not result:
                    error = mt5.last_error()
                    if error[0] == -10001 and path and attempt == 0:  # IPC send failed
                        logger.info(f"检测到MT5终端未运行，尝试启动: {path}")
                        import subprocess
                        try:
                            subprocess.Popen([path], shell=False)
                            logger.info("MT5终端启动中，等待5秒...")
                            time.sleep(5)  # 等待MT5启动
                            continue  # 重新尝试连接
                        except Exception as start_error:
                            logger.warning(f"启动MT5终端失败: {start_error}")

                if result:
                    self.connected = True
                    self.login = login
                    self.server = server
                    logger.info("已连接到 MetaTrader 5 终端")
                    return True
                else:
                    error = mt5.last_error()
                    last_error = error
                    logger.warning(f"initialize() 失败 (尝试 {attempt + 1}/{retry}), 错误代码: {error}")
                    self.connected = False

                    # 如果还有重试机会，等待后重试
                    if attempt < retry - 1:
                        time.sleep(retry_delay)

            except Exception as e:
                last_error = str(e)
                logger.warning(f"连接异常 (尝试 {attempt + 1}/{retry}): {str(e)}")
                self.connected = False

                # 如果还有重试机会，等待后重试
                if attempt < retry - 1:
                    time.sleep(retry_delay)

        # 所有重试都失败，抛出异常
        error_msg = f"连接失败，已重试 {retry} 次"
        if last_error:
            raise MT5ConnectionError(error_msg, last_error if isinstance(last_error, int) else None)
        raise MT5ConnectionError(error_msg)

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
            dict: 终端信息字典

        异常:
            MT5ConnectionError: 未连接时抛出
        """
        if not self.connected:
            raise MT5ConnectionError("未连接到 MT5 终端")

        info = mt5.terminal_info()
        if info is not None:
            return info._asdict()
        return None

    def get_version(self) -> Optional[tuple]:
        """
        获取 MetaTrader 5 版本信息

        返回:
            tuple: 版本信息元组

        异常:
            MT5ConnectionError: 未连接时抛出
        """
        if not self.connected:
            raise MT5ConnectionError("未连接到 MT5 终端")

        return mt5.version()

    def login(
        self,
        login: int,
        password: Optional[str] = None,
        server: Optional[str] = None,
        timeout: int = 60000,
    ) -> bool:
        """
        连接到指定的交易账户

        此方法用于在已初始化的 MT5 终端中切换到不同的交易账户。
        与 initialize() 不同,login() 不需要重新启动终端连接。

        参数:
            login: 交易账户号码(必填)
            password: 交易账户密码(可选)
                - 如果不设置,将自动使用终端数据库中保存的密码
            server: 交易服务器名称(可选)
                - 如果不设置,将自动使用上次使用的服务器
            timeout: 连接超时时间(毫秒),默认 60000(60秒)

        返回:
            bool: 连接成功返回 True,失败返回 False

        异常:
            MT5ConnectionError: MT5 终端未初始化时抛出

        使用示例:
            # 示例 1: 使用保存的密码登录
            mt5 = MT5Connection()
            mt5.initialize()  # 先初始化终端
            if mt5.login(17221085):
                print("已连接到账户 #17221085")

            # 示例 2: 指定密码和服务器
            if mt5.login(25115284, password="password123", server="MetaQuotes-Demo"):
                print("已切换到账户 #25115284")

        注意事项:
            1. 使用 login() 前必须先调用 initialize() 初始化终端
            2. 如果密码错误或账户不存在,将返回 False
            3. 成功登录后,账户信息会自动更新
        """
        # 检查终端是否已初始化
        if not self.connected:
            raise MT5ConnectionError("MT5 终端未初始化,请先调用 initialize()")

        try:
            # 构建登录参数
            kwargs = {"login": login, "timeout": timeout}
            if password is not None:
                kwargs["password"] = password
            if server is not None:
                kwargs["server"] = server

            # 调用 MT5 API 登录
            result = mt5.login(**kwargs)

            if result:
                # 更新连接信息
                self.login = login
                self.server = server
                logger.info(f"已成功登录到交易账户 #{login}")
                return True
            else:
                error = mt5.last_error()
                logger.error(f"登录失败,账户 #{login}, 错误代码: {error}")
                return False

        except Exception as e:
            logger.error(f"登录异常: {str(e)}")
            return False
