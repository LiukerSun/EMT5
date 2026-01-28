"""
MT5 API 序列化器

定义所有 API 请求和响应的数据结构
"""

from rest_framework import serializers


# ==================== 连接管理 ====================

class InitializeSerializer(serializers.Serializer):
    """初始化连接请求"""
    path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="MT5 终端路径")
    login = serializers.IntegerField(required=False, allow_null=True, help_text="账户号码")
    password = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="账户密码")
    server = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="服务器名称")
    timeout = serializers.IntegerField(default=60000, min_value=1000, max_value=300000, help_text="超时时间（毫秒，1-300秒）")
    portable = serializers.BooleanField(default=False, help_text="是否使用便携模式")


class ConnectionStatusSerializer(serializers.Serializer):
    """连接状态响应"""
    connected = serializers.BooleanField(help_text="是否已连接")
    terminal_info = serializers.DictField(required=False, allow_null=True, help_text="终端信息")
    version = serializers.ListField(required=False, allow_null=True, help_text="版本信息")


# ==================== 品种信息 ====================

class SymbolSelectSerializer(serializers.Serializer):
    """启用/禁用品种请求"""
    symbol = serializers.CharField(help_text="品种名称")
    enable = serializers.BooleanField(default=True, help_text="是否启用")


class SymbolInfoSerializer(serializers.Serializer):
    """品种信息请求"""
    symbol = serializers.CharField(help_text="品种名称")


class SymbolsListSerializer(serializers.Serializer):
    """品种列表请求"""
    group = serializers.CharField(default="*", help_text="品种组过滤")


# ==================== 交易操作 ====================

class MarketOrderSerializer(serializers.Serializer):
    """市价单请求"""
    symbol = serializers.CharField(help_text="品种名称")
    volume = serializers.FloatField(help_text="交易量（手数）")
    sl = serializers.FloatField(default=0.0, help_text="止损价格")
    tp = serializers.FloatField(default=0.0, help_text="止盈价格")
    deviation = serializers.IntegerField(default=20, help_text="最大价格偏差（点数）")
    magic = serializers.IntegerField(required=False, allow_null=True, help_text="EA 标识号")
    comment = serializers.CharField(default="", allow_blank=True, help_text="订单注释")
    position = serializers.IntegerField(default=0, required=False, help_text="持仓票据号（用于平仓）")


class LimitOrderSerializer(serializers.Serializer):
    """限价单请求"""
    symbol = serializers.CharField(help_text="品种名称")
    volume = serializers.FloatField(help_text="交易量（手数）")
    price = serializers.FloatField(help_text="挂单价格")
    sl = serializers.FloatField(default=0.0, help_text="止损价格")
    tp = serializers.FloatField(default=0.0, help_text="止盈价格")
    magic = serializers.IntegerField(required=False, allow_null=True, help_text="EA 标识号")
    comment = serializers.CharField(default="", allow_blank=True, help_text="订单注释")


class OrderCheckSerializer(serializers.Serializer):
    """订单检查请求"""
    request = serializers.DictField(help_text="交易请求字典")


class PositionsSerializer(serializers.Serializer):
    """持仓查询请求"""
    symbol = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="品种名称")
    ticket = serializers.IntegerField(required=False, allow_null=True, help_text="持仓票据号")
    group = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="品种组")


class OrdersSerializer(serializers.Serializer):
    """挂单查询请求"""
    symbol = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="品种名称")
    ticket = serializers.IntegerField(required=False, allow_null=True, help_text="订单票据号")
    group = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="品种组")


# ==================== 通用响应 ====================

class SuccessResponseSerializer(serializers.Serializer):
    """成功响应"""
    success = serializers.BooleanField(help_text="操作是否成功")
    message = serializers.CharField(required=False, help_text="响应消息")
    data = serializers.DictField(required=False, allow_null=True, help_text="响应数据")


class ErrorResponseSerializer(serializers.Serializer):
    """错误响应"""
    success = serializers.BooleanField(default=False, help_text="操作是否成功")
    error = serializers.CharField(help_text="错误信息")
