"""
MT5 API 视图

提供 RESTful API 接口
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .services import mt5_service
from .serializers import (
    InitializeSerializer,
    ConnectionStatusSerializer,
    SymbolSelectSerializer,
    SymbolInfoSerializer,
    SymbolsListSerializer,
    MarketOrderSerializer,
    LimitOrderSerializer,
    OrderCheckSerializer,
    PositionsSerializer,
    OrdersSerializer,
    SuccessResponseSerializer,
    ErrorResponseSerializer,
)


@method_decorator(csrf_exempt, name="dispatch")
class BaseAPIView(APIView):
    """基础 API 视图"""

    def success_response(self, data=None, message="操作成功"):
        """成功响应"""
        return Response(
            {"success": True, "message": message, "data": data},
            status=status.HTTP_200_OK,
        )

    def error_response(self, error, status_code=status.HTTP_400_BAD_REQUEST):
        """错误响应"""
        return Response({"success": False, "error": str(error)}, status=status_code)


# ==================== 连接管理 ====================


class InitializeView(BaseAPIView):
    """初始化 MT5 连接"""

    @swagger_auto_schema(
        operation_summary="初始化 MT5 连接",
        operation_description="建立与 MetaTrader 5 终端的连接。可以指定终端路径、登录账户信息等参数。",
        request_body=InitializeSerializer,
        responses={
            200: openapi.Response("连接成功", SuccessResponseSerializer),
            400: openapi.Response("连接失败", ErrorResponseSerializer),
        },
        tags=["连接管理"],
    )
    def post(self, request):
        """
        POST /api/connection/initialize/

        请求体:
        {
            "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
            "login": 12345678,
            "password": "your_password",
            "server": "XMGlobal-MT5 9",
            "timeout": 60000,
            "portable": false
        }
        """
        serializer = InitializeSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        success = mt5_service.initialize(
            path=data.get("path"),
            login=data.get("login"),
            password=data.get("password"),
            server=data.get("server"),
            timeout=data.get("timeout", 60000),
            portable=data.get("portable", False),
        )

        if success:
            return self.success_response(
                data={"connected": True}, message="MT5 连接成功"
            )
        else:
            return self.error_response("MT5 连接失败，请检查参数和终端状态")


class ShutdownView(BaseAPIView):
    """关闭 MT5 连接"""

    @swagger_auto_schema(
        operation_summary="关闭 MT5 连接",
        operation_description="断开与 MetaTrader 5 终端的连接，释放相关资源。",
        responses={
            200: openapi.Response("关闭成功", SuccessResponseSerializer),
        },
        tags=["连接管理"],
    )
    def post(self, request):
        """POST /api/connection/shutdown/"""
        mt5_service.shutdown()
        return self.success_response(message="MT5 连接已关闭")


class ConnectionStatusView(BaseAPIView):
    """获取连接状态"""

    @swagger_auto_schema(
        operation_summary="获取连接状态",
        operation_description="检查是否已连接到 MT5 终端，并返回终端信息和版本。",
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
        },
        tags=["连接管理"],
    )
    def get(self, request):
        """GET /api/connection/status/"""
        connected = mt5_service.is_connected()
        data = {"connected": connected}

        if connected:
            mt5 = mt5_service.mt5
            data["terminal_info"] = mt5.get_terminal_info()
            data["version"] = mt5.get_version()

        return self.success_response(data=data)


# ==================== 账户信息 ====================


class AccountInfoView(BaseAPIView):
    """获取账户信息"""

    @swagger_auto_schema(
        operation_summary="获取账户信息",
        operation_description="获取当前交易账户的详细信息，包括余额、净值、保证金等。",
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["账户信息"],
    )
    def get(self, request):
        """GET /api/account/info/"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        account_info = mt5_service.mt5.get_account_info()
        if account_info:
            return self.success_response(data=account_info)
        else:
            return self.error_response("获取账户信息失败")


# ==================== 品种信息 ====================


class SymbolsListView(BaseAPIView):
    """获取品种列表"""

    @swagger_auto_schema(
        operation_summary="获取品种列表",
        operation_description="获取所有可用的交易品种列表，支持按组过滤。",
        manual_parameters=[
            openapi.Parameter(
                "group",
                openapi.IN_QUERY,
                description="品种组过滤（默认 *）",
                type=openapi.TYPE_STRING,
                default="*",
            ),
        ],
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["品种信息"],
    )
    def get(self, request):
        """GET /api/symbols/list/?group=*"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        group = request.query_params.get("group", "*")
        symbols = mt5_service.mt5.get_symbol_names(group)

        if symbols is not None:
            return self.success_response(data={"symbols": symbols})
        else:
            return self.error_response("获取品种列表失败")


class SymbolInfoView(BaseAPIView):
    """获取品种信息"""

    @swagger_auto_schema(
        operation_summary="获取品种信息",
        operation_description="获取指定交易品种的详细信息，包括价格、点差、交易量限制等。",
        manual_parameters=[
            openapi.Parameter(
                "symbol",
                openapi.IN_PATH,
                description="品种名称（如 EURUSD）",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["品种信息"],
    )
    def get(self, request, symbol):
        """GET /api/symbols/info/<symbol>/"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        symbol_info = mt5_service.mt5.get_symbol_info(symbol)
        if symbol_info:
            return self.success_response(data=symbol_info)
        else:
            return self.error_response(f"获取品种 {symbol} 信息失败")


class SymbolTickView(BaseAPIView):
    """获取品种 Tick 数据"""

    @swagger_auto_schema(
        operation_summary="获取品种 Tick 数据",
        operation_description="获取指定品种的最新 Tick 数据（实时报价）。",
        manual_parameters=[
            openapi.Parameter(
                "symbol",
                openapi.IN_PATH,
                description="品种名称（如 EURUSD）",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["品种信息"],
    )
    def get(self, request, symbol):
        """GET /api/symbols/tick/<symbol>/"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        tick = mt5_service.mt5.get_symbol_info_tick(symbol)
        if tick:
            return self.success_response(data=tick)
        else:
            return self.error_response(f"获取品种 {symbol} Tick 数据失败")


class SymbolSelectView(BaseAPIView):
    """启用/禁用品种"""

    @swagger_auto_schema(
        operation_summary="启用/禁用品种",
        operation_description="在市场观察窗口中启用或禁用指定交易品种。交易前必须先启用品种。",
        request_body=SymbolSelectSerializer,
        responses={
            200: openapi.Response("操作成功", SuccessResponseSerializer),
            400: openapi.Response("操作失败", ErrorResponseSerializer),
        },
        tags=["品种信息"],
    )
    def post(self, request):
        """
        POST /api/symbols/select/

        请求体:
        {
            "symbol": "EURUSD",
            "enable": true
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = SymbolSelectSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        success = mt5_service.mt5.symbol_select(
            symbol=data["symbol"], enable=data.get("enable", True)
        )

        if success:
            action = "启用" if data.get("enable", True) else "禁用"
            return self.success_response(message=f"品种 {data['symbol']} 已{action}")
        else:
            return self.error_response(f"操作品种 {data['symbol']} 失败")


# ==================== 交易操作 ====================


class MarketBuyView(BaseAPIView):
    """市价买入"""

    @swagger_auto_schema(
        operation_summary="市价买入",
        operation_description="以当前市场价格执行买入操作。",
        request_body=MarketOrderSerializer,
        responses={
            200: openapi.Response("交易成功", SuccessResponseSerializer),
            400: openapi.Response("交易失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def post(self, request):
        """
        POST /api/trade/market-buy/

        请求体:
        {
            "symbol": "EURUSD",
            "volume": 0.1,
            "sl": 1.0950,
            "tp": 1.1050,
            "deviation": 20,
            "magic": 0,
            "comment": ""
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = MarketOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        trade_request = mt5_service.mt5.create_market_buy_request(
            symbol=data["symbol"],
            volume=data["volume"],
            sl=data.get("sl", 0.0),
            tp=data.get("tp", 0.0),
            deviation=data.get("deviation", 20),
            magic=data.get("magic"),
            comment=data.get("comment", ""),
        )

        result = mt5_service.mt5.order_send(trade_request)
        if result and result.get("retcode") == 10009:
            return self.success_response(data=result, message="买入订单执行成功")
        else:
            error_msg = result.get("comment", "未知错误") if result else "订单发送失败"
            return self.error_response(f"买入订单失败: {error_msg}")


class MarketSellView(BaseAPIView):
    """市价卖出"""

    @swagger_auto_schema(
        operation_summary="市价卖出",
        operation_description="以当前市场价格执行卖出操作（开空仓或平多仓）。",
        request_body=MarketOrderSerializer,
        responses={
            200: openapi.Response("交易成功", SuccessResponseSerializer),
            400: openapi.Response("交易失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def post(self, request):
        """
        POST /api/trade/market-sell/

        请求体:
        {
            "symbol": "EURUSD",
            "volume": 0.1,
            "sl": 1.1050,
            "tp": 1.0950,
            "deviation": 20,
            "magic": 0,
            "comment": "",
            "position": 0
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = MarketOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        trade_request = mt5_service.mt5.create_market_sell_request(
            symbol=data["symbol"],
            volume=data["volume"],
            sl=data.get("sl", 0.0),
            tp=data.get("tp", 0.0),
            deviation=data.get("deviation", 20),
            magic=data.get("magic"),
            comment=data.get("comment", ""),
            position=data.get("position", 0),
        )

        result = mt5_service.mt5.order_send(trade_request)
        if result and result.get("retcode") == 10009:
            return self.success_response(data=result, message="卖出订单执行成功")
        else:
            error_msg = result.get("comment", "未知错误") if result else "订单发送失败"
            return self.error_response(f"卖出订单失败: {error_msg}")


class LimitBuyView(BaseAPIView):
    """限价买入"""

    @swagger_auto_schema(
        operation_summary="限价买入",
        operation_description="创建限价买入挂单（价格低于当前价时触发买入）。",
        request_body=LimitOrderSerializer,
        responses={
            200: openapi.Response("挂单成功", SuccessResponseSerializer),
            400: openapi.Response("挂单失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def post(self, request):
        """
        POST /api/trade/limit-buy/

        请求体:
        {
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 1.0950,
            "sl": 1.0900,
            "tp": 1.1050,
            "magic": 0,
            "comment": ""
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = LimitOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        trade_request = mt5_service.mt5.create_limit_buy_request(
            symbol=data["symbol"],
            volume=data["volume"],
            price=data["price"],
            sl=data.get("sl", 0.0),
            tp=data.get("tp", 0.0),
            magic=data.get("magic"),
            comment=data.get("comment", ""),
        )

        result = mt5_service.mt5.order_send(trade_request)
        if result and result.get("retcode") == 10009:
            return self.success_response(data=result, message="限价买入挂单成功")
        else:
            error_msg = result.get("comment", "未知错误") if result else "订单发送失败"
            return self.error_response(f"限价买入挂单失败: {error_msg}")


class LimitSellView(BaseAPIView):
    """限价卖出"""

    @swagger_auto_schema(
        operation_summary="限价卖出",
        operation_description="创建限价卖出挂单（价格高于当前价时触发卖出）。",
        request_body=LimitOrderSerializer,
        responses={
            200: openapi.Response("挂单成功", SuccessResponseSerializer),
            400: openapi.Response("挂单失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def post(self, request):
        """
        POST /api/trade/limit-sell/

        请求体:
        {
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 1.1050,
            "sl": 1.1100,
            "tp": 1.0950,
            "magic": 0,
            "comment": ""
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = LimitOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        trade_request = mt5_service.mt5.create_limit_sell_request(
            symbol=data["symbol"],
            volume=data["volume"],
            price=data["price"],
            sl=data.get("sl", 0.0),
            tp=data.get("tp", 0.0),
            magic=data.get("magic"),
            comment=data.get("comment", ""),
        )

        result = mt5_service.mt5.order_send(trade_request)
        if result and result.get("retcode") == 10009:
            return self.success_response(data=result, message="限价卖出挂单成功")
        else:
            error_msg = result.get("comment", "未知错误") if result else "订单发送失败"
            return self.error_response(f"限价卖出挂单失败: {error_msg}")


class OrderCheckView(BaseAPIView):
    """检查订单"""

    @swagger_auto_schema(
        operation_summary="检查订单",
        operation_description="检查交易请求的正确性（不实际发送到服务器），可以检查保证金是否足够、价格是否合理等。",
        request_body=OrderCheckSerializer,
        responses={
            200: openapi.Response("检查完成", SuccessResponseSerializer),
            400: openapi.Response("检查失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def post(self, request):
        """
        POST /api/trade/order-check/

        请求体:
        {
            "request": {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.1000
            }
        }
        """
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        serializer = OrderCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        data = serializer.validated_data
        result = mt5_service.mt5.order_check(data["request"])

        if result:
            return self.success_response(data=result, message="订单检查完成")
        else:
            return self.error_response("订单检查失败")


class PositionsView(BaseAPIView):
    """获取持仓列表"""

    @swagger_auto_schema(
        operation_summary="获取持仓列表",
        operation_description="获取当前所有持仓信息，支持按品种、票据号过滤。",
        manual_parameters=[
            openapi.Parameter(
                "symbol",
                openapi.IN_QUERY,
                description="品种名称（可选）",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ticket",
                openapi.IN_QUERY,
                description="持仓票据号（可选）",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "group",
                openapi.IN_QUERY,
                description="品种组（可选）",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def get(self, request):
        """GET /api/trade/positions/?symbol=EURUSD&ticket=123456"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        symbol = request.query_params.get("symbol")
        ticket = request.query_params.get("ticket")
        group = request.query_params.get("group")

        ticket = int(ticket) if ticket else None

        positions = mt5_service.mt5.get_positions(
            symbol=symbol, ticket=ticket, group=group
        )

        if positions is not None:
            return self.success_response(data={"positions": positions})
        else:
            return self.error_response("获取持仓列表失败")


class OrdersView(BaseAPIView):
    """获取挂单列表"""

    @swagger_auto_schema(
        operation_summary="获取挂单列表",
        operation_description="获取当前所有挂单信息，支持按品种、票据号过滤。",
        manual_parameters=[
            openapi.Parameter(
                "symbol",
                openapi.IN_QUERY,
                description="品种名称（可选）",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ticket",
                openapi.IN_QUERY,
                description="订单票据号（可选）",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "group",
                openapi.IN_QUERY,
                description="品种组（可选）",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: openapi.Response("查询成功", SuccessResponseSerializer),
            400: openapi.Response("查询失败", ErrorResponseSerializer),
        },
        tags=["交易操作"],
    )
    def get(self, request):
        """GET /api/trade/orders/?symbol=EURUSD&ticket=123456"""
        if not mt5_service.is_connected():
            return self.error_response("未连接到 MT5 终端")

        symbol = request.query_params.get("symbol")
        ticket = request.query_params.get("ticket")
        group = request.query_params.get("group")

        ticket = int(ticket) if ticket else None

        orders = mt5_service.mt5.get_orders(symbol=symbol, ticket=ticket, group=group)

        if orders is not None:
            return self.success_response(data={"orders": orders})
        else:
            return self.error_response("获取挂单列表失败")
