"""
日志模块

提供统一的日志记录功能
"""

import logging
import sys
from typing import Optional


class MT5Logger:
    """
    MT5 日志记录器

    提供统一的日志接口，支持不同级别的日志输出
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化日志记录器

        如果 logger 已经有处理器（说明 Django 或其他框架可能接管了），
        就不再重复添加默认的控制台输出。
        这样在 Django 中，可以通过 settings.py 的 LOGGING 配置来控制 "MT5" 这个 logger。
        """
        if not MT5Logger._initialized:
            self.logger = logging.getLogger("MT5")

            # 只有当 logger 没有处理器时，才添加默认的控制台输出
            # 这样避免与 Django 等框架的日志配置冲突
            if not self.logger.handlers:
                self.logger.setLevel(logging.DEBUG)

                # 创建控制台处理器
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)

                # 创建格式化器
                formatter = logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                )
                console_handler.setFormatter(formatter)

                # 添加处理器
                self.logger.addHandler(console_handler)

            MT5Logger._initialized = True

    def debug(self, message: str):
        """调试信息"""
        self.logger.debug(message)

    def info(self, message: str):
        """一般信息"""
        self.logger.info(message)

    def warning(self, message: str):
        """警告信息"""
        self.logger.warning(message)

    def error(self, message: str):
        """错误信息"""
        self.logger.error(message)

    def critical(self, message: str):
        """严重错误"""
        self.logger.critical(message)

    def set_level(self, level: str):
        """
        设置日志级别

        参数:
            level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            for handler in self.logger.handlers:
                handler.setLevel(level_map[level.upper()])

    def add_file_handler(self, filename: str, level: str = "DEBUG"):
        """
        添加文件处理器

        参数:
            filename: 日志文件名
            level: 日志级别
        """
        file_handler = logging.FileHandler(filename, encoding="utf-8")

        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        file_handler.setLevel(level_map.get(level.upper(), logging.DEBUG))

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)


# 创建全局日志实例
logger = MT5Logger()
