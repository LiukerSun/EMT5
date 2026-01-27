"""
EMT5 自定义异常类

定义了 MT5 操作中可能出现的各种异常
"""


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
