"""
EMT5 自定义异常类

定义了 MT5 操作中可能出现的各种异常
"""

import functools
from typing import Callable, Type, Union, Tuple
from utils import logger


class MT5Error(Exception):
    """MT5 基础异常类"""

    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code is not None:
            return f"{self.message} (错误代码: {self.error_code})"
        return self.message


class MT5ConnectionError(MT5Error):
    """MT5 连接异常"""

    pass


class MT5OrderError(MT5Error):
    """MT5 订单异常"""

    pass


class MT5SymbolError(MT5Error):
    """MT5 品种异常"""

    pass


class MT5ValidationError(MT5Error):
    """MT5 验证异常"""

    pass


class MT5AccountError(MT5Error):
    """MT5 账户异常"""

    pass


class MT5TimeoutError(MT5Error):
    """MT5 超时异常"""

    pass


class ExceptionHandler:
    """
    异常处理装饰器类

    提供统一的异常捕获和处理机制，支持自动重试、日志记录等功能
    """

    @staticmethod
    def catch(
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        default_return=None,
        log_error: bool = True,
        raise_error: bool = False,
    ):
        """
        异常捕获装饰器

        参数:
            exceptions: 要捕获的异常类型，可以是单个异常或异常元组
            default_return: 发生异常时的默认返回值
            log_error: 是否记录错误日志
            raise_error: 是否重新抛出异常

        使用示例:
            @ExceptionHandler.catch(MT5ConnectionError, default_return=False)
            def connect():
                # 连接逻辑
                pass

            @ExceptionHandler.catch((ValueError, TypeError), log_error=True)
            def process_data(data):
                # 处理逻辑
                pass
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if log_error:
                        logger.error(
                            f"函数 {func.__name__} 发生异常: {type(e).__name__}: {str(e)}"
                        )

                    if raise_error:
                        raise

                    return default_return

            return wrapper

        return decorator

    @staticmethod
    def retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        log_attempts: bool = True,
    ):
        """
        重试装饰器

        参数:
            max_attempts: 最大重试次数
            delay: 重试间隔（秒）
            exceptions: 触发重试的异常类型
            log_attempts: 是否记录重试日志

        使用示例:
            @ExceptionHandler.retry(max_attempts=3, delay=2.0)
            def unstable_operation():
                # 可能失败的操作
                pass
        """
        import time

        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e

                        if log_attempts:
                            logger.warning(
                                f"函数 {func.__name__} 第 {attempt}/{max_attempts} 次尝试失败: {str(e)}"
                            )

                        if attempt < max_attempts:
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败"
                            )

                raise last_exception

            return wrapper

        return decorator

    @staticmethod
    def validate_connection(func: Callable):
        """
        连接验证装饰器

        自动检查 MT5 连接状态，未连接时抛出异常

        使用示例:
            @ExceptionHandler.validate_connection
            def get_account_info(self):
                # 需要连接的操作
                pass
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.is_connected():
                raise MT5ConnectionError("未连接到 MT5 终端，请先调用 initialize() 方法")
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def log_execution(log_args: bool = False, log_result: bool = False):
        """
        执行日志装饰器

        记录函数的执行情况

        参数:
            log_args: 是否记录函数参数
            log_result: 是否记录函数返回值

        使用示例:
            @ExceptionHandler.log_execution(log_args=True, log_result=True)
            def important_operation(param1, param2):
                # 重要操作
                pass
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_name = func.__name__

                if log_args:
                    logger.debug(f"调用函数 {func_name}，参数: args={args}, kwargs={kwargs}")
                else:
                    logger.debug(f"调用函数 {func_name}")

                try:
                    result = func(*args, **kwargs)

                    if log_result:
                        logger.debug(f"函数 {func_name} 执行成功，返回值: {result}")
                    else:
                        logger.debug(f"函数 {func_name} 执行成功")

                    return result
                except Exception as e:
                    logger.error(f"函数 {func_name} 执行失败: {type(e).__name__}: {str(e)}")
                    raise

            return wrapper

        return decorator
