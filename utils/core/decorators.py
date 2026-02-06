"""
通用装饰器模块

提供连接检查、重试等通用装饰器
"""

import functools
from typing import Callable, Type, Union, Tuple
from ..logger import logger


def require_connection(func: Callable) -> Callable:
    """
    连接检查装饰器

    自动检查 MT5 连接状态，未连接时抛出异常或返回 None

    使用示例:
        @require_connection
        def get_account_info(self):
            # 需要连接的操作
            pass

    注意:
        被装饰的方法所属的类必须有 connection 属性（MT5Connection 实例）
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 支持两种属性名: connection 或 _connection
        conn = getattr(self, 'connection', None) or getattr(self, '_connection', None)
        if conn is None:
            logger.error(f"类 {self.__class__.__name__} 没有 connection 属性")
            return None

        if not conn.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        return func(self, *args, **kwargs)

    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    log_attempts: bool = True,
) -> Callable:
    """
    重试装饰器

    参数:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 触发重试的异常类型
        log_attempts: 是否记录重试日志

    使用示例:
        @retry(max_attempts=3, delay=2.0)
        def unstable_operation():
            # 可能失败的操作
            pass
    """
    import time

    def decorator(func: Callable) -> Callable:
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


def catch_exceptions(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    default_return=None,
    log_error: bool = True,
    raise_error: bool = False,
) -> Callable:
    """
    异常捕获装饰器

    参数:
        exceptions: 要捕获的异常类型，可以是单个异常或异常元组
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        raise_error: 是否重新抛出异常

    使用示例:
        @catch_exceptions(ValueError, default_return=False)
        def risky_operation():
            # 可能抛出异常的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
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


def log_execution(log_args: bool = False, log_result: bool = False) -> Callable:
    """
    执行日志装饰器

    记录函数的执行情况

    参数:
        log_args: 是否记录函数参数
        log_result: 是否记录函数返回值

    使用示例:
        @log_execution(log_args=True, log_result=True)
        def important_operation(param1, param2):
            # 重要操作
            pass
    """
    def decorator(func: Callable) -> Callable:
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
