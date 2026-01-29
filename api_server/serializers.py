"""
API 序列化器

用于请求体验证和 Swagger 文档生成
"""
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """登录请求"""
    login = serializers.IntegerField(help_text='账户号')
    password = serializers.CharField(help_text='密码')
    server = serializers.CharField(help_text='服务器', max_length=100)


class MarketOrderSerializer(serializers.Serializer):
    """市价单请求"""
    symbol = serializers.CharField(help_text='品种名称', max_length=20)
    volume = serializers.FloatField(help_text='交易量', min_value=0.01)
    sl = serializers.FloatField(help_text='止损价格', required=False, allow_null=True)
    tp = serializers.FloatField(help_text='止盈价格', required=False, allow_null=True)
    comment = serializers.CharField(help_text='订单注释', required=False, max_length=100, default='')


class PendingOrderSerializer(serializers.Serializer):
    """挂单请求"""
    symbol = serializers.CharField(help_text='品种名称', max_length=20)
    volume = serializers.FloatField(help_text='交易量', min_value=0.01)
    price = serializers.FloatField(help_text='挂单价格')
    order_type = serializers.ChoiceField(
        help_text='订单类型',
        choices=['limit_buy', 'limit_sell', 'stop_buy', 'stop_sell']
    )
    sl = serializers.FloatField(help_text='止损价格', required=False, allow_null=True)
    tp = serializers.FloatField(help_text='止盈价格', required=False, allow_null=True)
    comment = serializers.CharField(help_text='订单注释', required=False, max_length=100, default='')


class ClosePositionSerializer(serializers.Serializer):
    """平仓请求"""
    ticket = serializers.IntegerField(help_text='持仓票据号')
    volume = serializers.FloatField(help_text='平仓数量（可选，部分平仓）', required=False, allow_null=True)


class ModifyPositionSerializer(serializers.Serializer):
    """修改持仓请求"""
    ticket = serializers.IntegerField(help_text='持仓票据号')
    sl = serializers.FloatField(help_text='新止损价格', required=False, allow_null=True)
    tp = serializers.FloatField(help_text='新止盈价格', required=False, allow_null=True)


class TradeResultSerializer(serializers.Serializer):
    """交易结果"""
    retcode = serializers.IntegerField(help_text='返回码')
    order = serializers.IntegerField(help_text='订单号', required=False)
    deal = serializers.IntegerField(help_text='成交号', required=False)
    volume = serializers.FloatField(help_text='成交量', required=False)
    price = serializers.FloatField(help_text='成交价格', required=False)
    comment = serializers.CharField(help_text='注释', required=False)


class ErrorSerializer(serializers.Serializer):
    """错误响应"""
    error = serializers.CharField(help_text='错误信息')
    code = serializers.CharField(help_text='错误代码', required=False)


class OrderCheckSerializer(serializers.Serializer):
    """订单检查请求"""
    symbol = serializers.CharField(help_text='品种名称', max_length=20)
    volume = serializers.FloatField(help_text='交易量', min_value=0.01)
    order_type = serializers.ChoiceField(
        help_text='订单类型',
        choices=['market_buy', 'market_sell', 'limit_buy', 'limit_sell', 'stop_buy', 'stop_sell']
    )
    price = serializers.FloatField(help_text='价格（挂单时必填）', required=False, allow_null=True)
    sl = serializers.FloatField(help_text='止损价格', required=False, allow_null=True)
    tp = serializers.FloatField(help_text='止盈价格', required=False, allow_null=True)
