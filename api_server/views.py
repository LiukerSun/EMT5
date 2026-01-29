"""
EMT5 API 视图

使用 drf-spectacular 装饰器生成 Swagger 文档
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from datetime import datetime, timezone
from api_server.serializers import (
    LoginSerializer, MarketOrderSerializer, ClosePositionSerializer, ModifyPositionSerializer,
    PendingOrderSerializer, OrderCheckSerializer
)
from api_server.mt5_manager import mt5_manager, require_login, require_terminal


def get_mt5():
    """获取 EMT5 实例"""
    return mt5_manager.get_emt5()


# ============================================================
# 健康检查
# ============================================================

@extend_schema(
    tags=['Health'],
    operation_id='health_check',
    summary='健康检查',
    description='检查 API 服务和 MT5 连接状态',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'terminal_connected': {'type': 'boolean', 'example': True},
                'account_logged_in': {'type': 'boolean', 'example': True},
                'account': {'type': 'object', 'nullable': True},
                'timestamp': {'type': 'string', 'format': 'date-time'},
            }
        }
    }
)
@api_view(['GET'])
def health_check(request):
    """
    健康检查接口

    返回 API 服务状态、MT5 终端连接状态和账户登录状态
    """
    status_info = mt5_manager.get_status()
    return Response({
        'status': 'ok',
        'terminal_connected': status_info['terminal_connected'],
        'account_logged_in': status_info['account_logged_in'],
        'account': {
            'login': status_info['account'].get('login'),
            'server': status_info['account'].get('server'),
            'name': status_info['account'].get('name'),
        } if status_info['account'] else None,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


@extend_schema(
    tags=['Health'],
    operation_id='terminal_info',
    summary='获取终端信息',
    description='获取 MT5 终端的详细信息',
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_terminal
def get_terminal_info(request):
    """获取 MT5 终端信息"""
    try:
        mt5 = get_mt5()
        info = mt5.connection.get_terminal_info()
        return Response(info)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Health'],
    operation_id='version',
    summary='获取 MT5 版本',
    description='获取 MetaTrader 5 终端版本信息',
    responses={200: {'type': 'object', 'properties': {
        'version': {'type': 'array', 'items': {'type': 'integer'}},
        'build': {'type': 'integer'},
        'release_date': {'type': 'string'}
    }}}
)
@api_view(['GET'])
@require_terminal
def get_version(request):
    """获取 MT5 版本"""
    try:
        mt5 = get_mt5()
        version = mt5.connection.get_version()
        if version:
            return Response({
                'version': list(version),
                'build': version[1] if len(version) > 1 else None,
                'release_date': version[2] if len(version) > 2 else None
            })
        return Response({'error': '获取版本失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 账户信息
# ============================================================

@extend_schema(
    tags=['Account'],
    operation_id='account_login',
    summary='登录交易账户',
    description='登录 MT5 交易账户',
    request=LoginSerializer,
    responses={
        200: {'type': 'object'},
        400: {'description': '参数错误'},
        401: {'description': '登录失败'}
    }
)
@api_view(['POST'])
def account_login(request):
    """登录交易账户"""
    data = request.data
    login = data.get('login')
    password = data.get('password')
    server = data.get('server')

    if not all([login, password, server]):
        return Response({'error': '缺少 login、password 或 server'}, status=status.HTTP_400_BAD_REQUEST)

    result = mt5_manager.login(int(login), password, server)
    if result['success']:
        return Response(result)
    return Response(result, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    tags=['Account'],
    operation_id='account_info',
    summary='获取账户信息',
    description='获取当前登录账户的详细信息，包括余额、净值、保证金等',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'login': {'type': 'integer', 'description': '账户号', 'example': 12345678},
                'balance': {'type': 'number', 'description': '余额', 'example': 10000.00},
                'equity': {'type': 'number', 'description': '净值', 'example': 10500.00},
                'margin': {'type': 'number', 'description': '已用保证金', 'example': 500.00},
                'margin_free': {'type': 'number', 'description': '可用保证金', 'example': 10000.00},
                'margin_level': {'type': 'number', 'description': '保证金比例', 'example': 2100.00},
                'profit': {'type': 'number', 'description': '浮动盈亏', 'example': 500.00},
                'leverage': {'type': 'integer', 'description': '杠杆', 'example': 100},
                'currency': {'type': 'string', 'description': '账户货币', 'example': 'USD'},
                'server': {'type': 'string', 'description': '服务器', 'example': 'XMGlobal-MT5'},
                'name': {'type': 'string', 'description': '账户名称', 'example': 'John Doe'},
            }
        },
        500: {'description': '获取账户信息失败'}
    }
)
@api_view(['GET'])
@require_login
def get_account_info(request):
    """
    获取账户信息

    返回当前登录账户的余额、净值、保证金、杠杆等信息
    """
    try:
        account = mt5_manager.get_account_info()
        if account:
            return Response(account)
        return Response({'error': '获取账户信息失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 品种信息
# ============================================================

@extend_schema(
    tags=['Symbol'],
    operation_id='symbol_list',
    summary='获取品种列表',
    description='获取所有可用交易品种的名称列表',
    parameters=[
        OpenApiParameter(
            name='group',
            type=str,
            location=OpenApiParameter.QUERY,
            description='品种组过滤，支持通配符，如 "*USD*"',
            required=False,
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total': {'type': 'integer', 'example': 100},
                'symbols': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['EURUSD', 'GBPUSD', 'USDJPY']
                }
            }
        }
    }
)
@api_view(['GET'])
@require_terminal
def get_symbols(request):
    try:
        mt5 = get_mt5()
        group = request.query_params.get('group')
        symbols = mt5.symbol.get_symbol_names(group=group)
        return Response({
            'total': len(symbols) if symbols else 0,
            'symbols': symbols or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Symbol'],
    operation_id='symbol_select',
    summary='选择/取消选择品种',
    description='在市场报价窗口中启用或禁用指定品种。品种必须被选中后才能获取报价和K线数据。',
    parameters=[
        OpenApiParameter(name='enable', type=bool, location=OpenApiParameter.QUERY,
                        description='True 启用，False 禁用，默认 True', required=False),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'symbol': {'type': 'string'},
                'enabled': {'type': 'boolean'},
                'message': {'type': 'string'},
            }
        },
        400: {'description': '操作失败'}
    }
)
@api_view(['POST'])
@require_terminal
def symbol_select(request, symbol: str):
    """
    选择/取消选择品种

    在市场报价窗口中启用或禁用指定品种。
    品种必须被选中（enable=True）后才能获取实时报价和历史K线数据。
    """
    try:
        mt5 = get_mt5()
        enable_str = request.query_params.get('enable', 'true').lower()
        enable = enable_str not in ('false', '0', 'no')

        result = mt5.symbol.symbol_select(symbol, enable)
        action = '启用' if enable else '禁用'

        if result:
            return Response({
                'success': True,
                'symbol': symbol,
                'enabled': enable,
                'message': f'已{action}品种 {symbol}'
            })
        return Response({
            'success': False,
            'symbol': symbol,
            'enabled': not enable,
            'message': f'{action}品种 {symbol} 失败'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Symbol'],
    operation_id='symbol_detail',
    summary='获取品种详情',
    description='获取指定品种的详细信息，包括点差、合约大小、交易时间等',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'example': 'EURUSD'},
                'description': {'type': 'string', 'example': 'Euro vs US Dollar'},
                'spread': {'type': 'integer', 'description': '点差', 'example': 10},
                'digits': {'type': 'integer', 'description': '小数位数', 'example': 5},
                'volume_min': {'type': 'number', 'description': '最小交易量', 'example': 0.01},
                'volume_max': {'type': 'number', 'description': '最大交易量', 'example': 100.0},
                'volume_step': {'type': 'number', 'description': '交易量步长', 'example': 0.01},
                'trade_contract_size': {'type': 'number', 'description': '合约大小', 'example': 100000},
            }
        },
        404: {'description': '品种不存在'}
    }
)
@api_view(['GET'])
@require_terminal
def get_symbol_info(request, symbol: str):
    """
    获取品种详情

    Args:
        symbol: 品种名称，如 EURUSD
    """
    try:
        mt5 = get_mt5()
        info = mt5.symbol.get_symbol_info(symbol)
        if info is None:
            return Response({'error': f'品种 {symbol} 不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(info)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Symbol'],
    operation_id='symbol_tick',
    summary='获取实时报价',
    description='获取指定品种的实时买卖价格',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'example': 'EURUSD'},
                'bid': {'type': 'number', 'description': '买价', 'example': 1.10500},
                'ask': {'type': 'number', 'description': '卖价', 'example': 1.10510},
                'spread': {'type': 'integer', 'description': '点差', 'example': 10},
                'time': {'type': 'string', 'format': 'date-time'},
            }
        },
        404: {'description': '品种不存在'}
    }
)
@api_view(['GET'])
@require_terminal
def get_symbol_tick(request, symbol: str):
    try:
        mt5 = get_mt5()
        tick = mt5.symbol.get_symbol_info_tick(symbol)
        if tick is None:
            return Response({'error': f'品种 {symbol} 不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(tick)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 持仓管理
# ============================================================

@extend_schema(
    tags=['Position'],
    operation_id='positions_total',
    summary='获取持仓总数',
    description='获取当前持仓总数',
    responses={200: {'type': 'object', 'properties': {'total': {'type': 'integer'}}}}
)
@api_view(['GET'])
@require_login
def get_positions_total(request):
    """获取持仓总数"""
    try:
        mt5 = get_mt5()
        total = mt5.position.get_positions_total()
        return Response({'total': total})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Position'],
    operation_id='position_list',
    summary='获取持仓列表',
    description='获取当前所有持仓，可按品种过滤',
    parameters=[
        OpenApiParameter(name='symbol', type=str, description='品种过滤', required=False),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'total': {'type': 'integer', 'example': 5},
                'positions': {'type': 'array', 'items': {'type': 'object'}}
            }
        }
    }
)
@api_view(['GET'])
@require_login
def get_positions(request):
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        positions = mt5.position.get_positions(symbol=symbol)
        return Response({
            'total': len(positions) if positions else 0,
            'positions': positions or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Position'],
    operation_id='position_detail',
    summary='获取持仓详情',
    description='根据票据号获取单个持仓详情',
    responses={200: {'type': 'object'}, 404: {'description': '持仓不存在'}}
)
@api_view(['GET'])
@require_login
def get_position_detail(request, ticket: int):
    try:
        mt5 = get_mt5()
        position = mt5.position.get_position_by_ticket(ticket)
        if position is None:
            return Response({'error': '持仓不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(position)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Position'],
    operation_id='orders_total',
    summary='获取挂单总数',
    description='获取当前挂单总数',
    responses={200: {'type': 'object', 'properties': {'total': {'type': 'integer'}}}}
)
@api_view(['GET'])
@require_login
def get_orders_total(request):
    """获取挂单总数"""
    try:
        mt5 = get_mt5()
        total = mt5.position.get_orders_total()
        return Response({'total': total})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Position'],
    operation_id='order_list',
    summary='获取挂单列表',
    description='获取当前所有挂单',
    parameters=[
        OpenApiParameter(name='symbol', type=str, description='品种过滤', required=False),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_orders(request):
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        orders = mt5.position.get_orders(symbol=symbol)
        return Response({
            'total': len(orders) if orders else 0,
            'orders': orders or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Position'],
    operation_id='order_detail',
    summary='获取挂单详情',
    description='根据票据号获取单个挂单详情',
    responses={200: {'type': 'object'}, 404: {'description': '挂单不存在'}}
)
@api_view(['GET'])
@require_login
def get_order_detail(request, ticket: int):
    try:
        mt5 = get_mt5()
        order = mt5.position.get_order_by_ticket(ticket)
        if order is None:
            return Response({'error': '挂单不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(order)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 交易操作
# ============================================================

@extend_schema(
    tags=['Trade'],
    operation_id='trade_buy',
    summary='市价买入',
    description='以市价买入指定品种',
    request=MarketOrderSerializer,
    responses={
        200: {'type': 'object', 'properties': {
            'retcode': {'type': 'integer'}, 'order': {'type': 'integer'}
        }},
        400: {'description': '参数错误'}
    }
)
@api_view(['POST'])
@require_login
def market_buy(request):
    try:
        mt5 = get_mt5()
        data = request.data
        symbol = data.get('symbol')
        volume = data.get('volume')

        if not symbol or not volume:
            return Response({'error': '缺少 symbol 或 volume'}, status=status.HTTP_400_BAD_REQUEST)

        order = mt5.order(symbol).market_buy(float(volume))
        if data.get('sl'):
            order.with_sl(float(data['sl']))
        if data.get('tp'):
            order.with_tp(float(data['tp']))
        if data.get('comment'):
            order.with_comment(data['comment'])

        result = order.send()
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Trade'],
    operation_id='trade_sell',
    summary='市价卖出',
    description='以市价卖出指定品种',
    request=MarketOrderSerializer,
    responses={200: {'type': 'object'}, 400: {'description': '参数错误'}}
)
@api_view(['POST'])
@require_login
def market_sell(request):
    try:
        mt5 = get_mt5()
        data = request.data
        symbol = data.get('symbol')
        volume = data.get('volume')

        if not symbol or not volume:
            return Response({'error': '缺少 symbol 或 volume'}, status=status.HTTP_400_BAD_REQUEST)

        order = mt5.order(symbol).market_sell(float(volume))
        if data.get('sl'):
            order.with_sl(float(data['sl']))
        if data.get('tp'):
            order.with_tp(float(data['tp']))
        if data.get('comment'):
            order.with_comment(data['comment'])

        result = order.send()
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Trade'],
    operation_id='trade_close',
    summary='平仓',
    description='平掉指定持仓',
    request=ClosePositionSerializer,
    responses={200: {'type': 'object'}, 400: {'description': '参数错误'}}
)
@api_view(['POST'])
@require_login
def close_position(request):
    try:
        mt5 = get_mt5()
        data = request.data
        ticket = data.get('ticket')

        if not ticket:
            return Response({'error': '缺少 ticket'}, status=status.HTTP_400_BAD_REQUEST)

        volume = data.get('volume')
        result = mt5.executor.close_position(ticket=int(ticket), volume=float(volume) if volume else None)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Trade'],
    operation_id='trade_modify',
    summary='修改止损止盈',
    description='修改持仓的止损和止盈价格',
    request=ModifyPositionSerializer,
    responses={200: {'type': 'object'}, 400: {'description': '参数错误'}}
)
@api_view(['POST'])
@require_login
def modify_position(request):
    try:
        mt5 = get_mt5()
        data = request.data
        ticket = data.get('ticket')

        if not ticket:
            return Response({'error': '缺少 ticket'}, status=status.HTTP_400_BAD_REQUEST)

        sl = float(data['sl']) if data.get('sl') else None
        tp = float(data['tp']) if data.get('tp') else None
        result = mt5.executor.modify(ticket=int(ticket), sl=sl, tp=tp)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Trade'],
    operation_id='trade_pending',
    summary='挂单',
    description='创建挂单（限价单或止损单），等价格到达时自动成交',
    request=PendingOrderSerializer,
    responses={
        200: {'type': 'object', 'properties': {
            'retcode': {'type': 'integer'}, 'order': {'type': 'integer'}
        }},
        400: {'description': '参数错误'}
    }
)
@api_view(['POST'])
@require_login
def pending_order(request):
    """
    创建挂单

    订单类型说明：
    - limit_buy: 限价买入，价格必须低于当前价，价格下跌到指定价位时买入
    - limit_sell: 限价卖出，价格必须高于当前价，价格上涨到指定价位时卖出
    - stop_buy: 止损买入，价格必须高于当前价，价格上涨到指定价位时买入（突破追涨）
    - stop_sell: 止损卖出，价格必须低于当前价，价格下跌到指定价位时卖出（突破追跌）
    """
    try:
        mt5 = get_mt5()
        data = request.data
        symbol = data.get('symbol')
        volume = data.get('volume')
        price = data.get('price')
        order_type = data.get('order_type')

        if not all([symbol, volume, price, order_type]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据订单类型调用对应方法
        order = mt5.order(symbol)
        if order_type == 'limit_buy':
            order.limit_buy(float(volume), float(price))
        elif order_type == 'limit_sell':
            order.limit_sell(float(volume), float(price))
        elif order_type == 'stop_buy':
            order.stop_buy(float(volume), float(price))
        elif order_type == 'stop_sell':
            order.stop_sell(float(volume), float(price))
        else:
            return Response({'error': f'无效的订单类型: {order_type}'}, status=status.HTTP_400_BAD_REQUEST)

        # 设置止损止盈
        if data.get('sl'):
            order.with_sl(float(data['sl']))
        if data.get('tp'):
            order.with_tp(float(data['tp']))
        if data.get('comment'):
            order.with_comment(data['comment'])

        result = order.send()
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Trade'],
    operation_id='trade_check',
    summary='检查订单',
    description='检查订单是否可以执行，返回保证金、余额等信息，不实际发送订单',
    request=OrderCheckSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'retcode': {'type': 'integer', 'description': '返回码，0表示检查通过'},
                'balance': {'type': 'number', 'description': '检查后账户余额'},
                'equity': {'type': 'number', 'description': '检查后账户净值'},
                'profit': {'type': 'number', 'description': '浮动盈亏'},
                'margin': {'type': 'number', 'description': '所需保证金'},
                'margin_free': {'type': 'number', 'description': '可用保证金'},
                'margin_level': {'type': 'number', 'description': '保证金比例'},
                'comment': {'type': 'string', 'description': '检查结果说明'},
            }
        },
        400: {'description': '参数错误'}
    }
)
@api_view(['POST'])
@require_login
def order_check(request):
    """
    检查订单

    在不实际发送订单的情况下，检查订单是否可以执行。
    返回账户余额、所需保证金等信息，用于预判交易是否可行。
    """
    try:
        mt5 = get_mt5()
        data = request.data
        symbol = data.get('symbol')
        volume = data.get('volume')
        order_type = data.get('order_type')

        if not all([symbol, volume, order_type]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 构建订单
        order = mt5.order(symbol)
        price = data.get('price')

        if order_type == 'market_buy':
            order.market_buy(float(volume))
        elif order_type == 'market_sell':
            order.market_sell(float(volume))
        elif order_type == 'limit_buy':
            if not price:
                return Response({'error': 'limit_buy 需要指定 price'}, status=status.HTTP_400_BAD_REQUEST)
            order.limit_buy(float(volume), float(price))
        elif order_type == 'limit_sell':
            if not price:
                return Response({'error': 'limit_sell 需要指定 price'}, status=status.HTTP_400_BAD_REQUEST)
            order.limit_sell(float(volume), float(price))
        elif order_type == 'stop_buy':
            if not price:
                return Response({'error': 'stop_buy 需要指定 price'}, status=status.HTTP_400_BAD_REQUEST)
            order.stop_buy(float(volume), float(price))
        elif order_type == 'stop_sell':
            if not price:
                return Response({'error': 'stop_sell 需要指定 price'}, status=status.HTTP_400_BAD_REQUEST)
            order.stop_sell(float(volume), float(price))
        else:
            return Response({'error': f'无效的订单类型: {order_type}'}, status=status.HTTP_400_BAD_REQUEST)

        # 设置止损止盈
        if data.get('sl'):
            order.with_sl(float(data['sl']))
        if data.get('tp'):
            order.with_tp(float(data['tp']))

        # 检查订单（不发送）
        result = order.check()
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 历史数据
# ============================================================

@extend_schema(
    tags=['History'],
    operation_id='history_bars',
    summary='获取K线数据',
    description='获取指定品种的历史K线数据',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True, description='品种'),
        OpenApiParameter(name='timeframe', type=str, required=True, description='时间周期: M1,M5,M15,M30,H1,H4,D1,W1,MN1'),
        OpenApiParameter(name='count', type=int, required=False, description='K线数量', default=100),
        OpenApiParameter(name='start_pos', type=int, required=False, description='起始位置', default=0),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_bars(request):
    import MetaTrader5 as mt5_api

    TIMEFRAME_MAP = {
        'M1': mt5_api.TIMEFRAME_M1, 'M5': mt5_api.TIMEFRAME_M5,
        'M15': mt5_api.TIMEFRAME_M15, 'M30': mt5_api.TIMEFRAME_M30,
        'H1': mt5_api.TIMEFRAME_H1, 'H4': mt5_api.TIMEFRAME_H4,
        'D1': mt5_api.TIMEFRAME_D1, 'W1': mt5_api.TIMEFRAME_W1,
        'MN1': mt5_api.TIMEFRAME_MN1,
    }

    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        tf_str = request.query_params.get('timeframe', 'H1').upper()
        count = int(request.query_params.get('count', 100))
        start_pos = int(request.query_params.get('start_pos', 0))

        if not symbol:
            return Response({'error': '缺少 symbol'}, status=status.HTTP_400_BAD_REQUEST)

        timeframe = TIMEFRAME_MAP.get(tf_str)
        if timeframe is None:
            return Response({'error': f'无效的 timeframe: {tf_str}'}, status=status.HTTP_400_BAD_REQUEST)

        bars = mt5.history.get_bars(symbol, timeframe, start_pos=start_pos, count=count)
        return Response({
            'symbol': symbol,
            'timeframe': tf_str,
            'total': len(bars) if bars else 0,
            'bars': bars or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_bars_range',
    summary='获取时间范围内的K线',
    description='获取指定时间范围内的历史K线数据（使用 copy_rates_range）',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True, description='品种'),
        OpenApiParameter(name='timeframe', type=str, required=True, description='时间周期: M1,M5,M15,M30,H1,H4,D1,W1,MN1'),
        OpenApiParameter(name='date_from', type=str, required=True, description='开始时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_bars_range(request):
    """
    获取时间范围内的K线数据

    使用 copy_rates_range 获取指定时间范围内的所有K线。
    时间使用 UTC 时区。
    """
    import MetaTrader5 as mt5_api

    TIMEFRAME_MAP = {
        'M1': mt5_api.TIMEFRAME_M1, 'M5': mt5_api.TIMEFRAME_M5,
        'M15': mt5_api.TIMEFRAME_M15, 'M30': mt5_api.TIMEFRAME_M30,
        'H1': mt5_api.TIMEFRAME_H1, 'H4': mt5_api.TIMEFRAME_H4,
        'D1': mt5_api.TIMEFRAME_D1, 'W1': mt5_api.TIMEFRAME_W1,
        'MN1': mt5_api.TIMEFRAME_MN1,
    }

    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        tf_str = request.query_params.get('timeframe', 'H1').upper()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not symbol:
            return Response({'error': '缺少 symbol'}, status=status.HTTP_400_BAD_REQUEST)
        if not date_from_str or not date_to_str:
            return Response({'error': '缺少 date_from 或 date_to'}, status=status.HTTP_400_BAD_REQUEST)

        timeframe = TIMEFRAME_MAP.get(tf_str)
        if timeframe is None:
            return Response({'error': f'无效的 timeframe: {tf_str}'}, status=status.HTTP_400_BAD_REQUEST)

        # 解析时间，支持两种格式
        try:
            if ' ' in date_from_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            else:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

            if ' ' in date_to_str:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            else:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            return Response({'error': '日期格式错误，请使用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS'}, status=status.HTTP_400_BAD_REQUEST)

        bars = mt5.history.get_bars(symbol, timeframe, date_from=date_from, date_to=date_to)
        return Response({
            'symbol': symbol,
            'timeframe': tf_str,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'total': len(bars) if bars else 0,
            'bars': bars or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_ticks',
    summary='获取 Tick 数据',
    description='获取指定时间开始的 Tick 数据',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True, description='品种'),
        OpenApiParameter(name='date_from', type=str, required=True, description='开始时间 YYYY-MM-DD HH:MM:SS'),
        OpenApiParameter(name='count', type=int, required=True, description='获取数量'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_ticks(request):
    """获取 Tick 数据"""
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        date_from_str = request.query_params.get('date_from')
        count = request.query_params.get('count')

        if not all([symbol, date_from_str, count]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if ' ' in date_from_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            else:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            return Response({'error': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)

        ticks = mt5.history.get_ticks(symbol, date_from=date_from, count=int(count))
        return Response({
            'symbol': symbol,
            'date_from': date_from.isoformat(),
            'total': len(ticks) if ticks else 0,
            'ticks': ticks or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_ticks_range',
    summary='获取时间范围内的 Tick',
    description='获取指定时间范围内的 Tick 数据',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True, description='品种'),
        OpenApiParameter(name='date_from', type=str, required=True, description='开始时间 YYYY-MM-DD HH:MM:SS'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束时间 YYYY-MM-DD HH:MM:SS'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_ticks_range(request):
    """获取时间范围内的 Tick 数据"""
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not all([symbol, date_from_str, date_to_str]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if ' ' in date_from_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            else:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

            if ' ' in date_to_str:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            else:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            return Response({'error': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)

        ticks = mt5.history.get_ticks(symbol, date_from=date_from, date_to=date_to)
        return Response({
            'symbol': symbol,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'total': len(ticks) if ticks else 0,
            'ticks': ticks or []
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_orders',
    summary='获取历史订单',
    description='获取指定时间范围内的历史订单',
    parameters=[
        OpenApiParameter(name='date_from', type=str, required=True, description='开始日期 YYYY-MM-DD'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束日期 YYYY-MM-DD'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_history_orders(request):
    """获取历史订单"""
    try:
        mt5 = get_mt5()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response({'error': '缺少 date_from 或 date_to'}, status=status.HTTP_400_BAD_REQUEST)

        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        result = mt5.history.get_history_orders(date_from, date_to)
        return Response(result)
    except ValueError:
        return Response({'error': '日期格式错误，请使用 YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_deals',
    summary='获取历史成交',
    description='获取指定时间范围内的历史成交记录',
    parameters=[
        OpenApiParameter(name='date_from', type=str, required=True, description='开始日期 YYYY-MM-DD'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束日期 YYYY-MM-DD'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@require_login
def get_deals(request):
    try:
        mt5 = get_mt5()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response({'error': '缺少 date_from 或 date_to'}, status=status.HTTP_400_BAD_REQUEST)

        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        result = mt5.history.get_history_deals(date_from, date_to)
        return Response(result)
    except ValueError:
        return Response({'error': '日期格式错误，请使用 YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_deals_total',
    summary='获取历史成交总数',
    description='获取指定时间范围内的历史成交总数',
    parameters=[
        OpenApiParameter(name='date_from', type=str, required=True, description='开始日期 YYYY-MM-DD'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束日期 YYYY-MM-DD'),
    ],
    responses={200: {'type': 'object', 'properties': {'total': {'type': 'integer'}}}}
)
@api_view(['GET'])
@require_login
def get_deals_total(request):
    """获取历史成交总数"""
    try:
        mt5 = get_mt5()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response({'error': '缺少 date_from 或 date_to'}, status=status.HTTP_400_BAD_REQUEST)

        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        total = mt5.history.get_history_deals_total(date_from, date_to)
        return Response({'date_from': date_from_str, 'date_to': date_to_str, 'total': total})
    except ValueError:
        return Response({'error': '日期格式错误，请使用 YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['History'],
    operation_id='history_orders_total',
    summary='获取历史订单总数',
    description='获取指定时间范围内的历史订单总数',
    parameters=[
        OpenApiParameter(name='date_from', type=str, required=True, description='开始日期 YYYY-MM-DD'),
        OpenApiParameter(name='date_to', type=str, required=True, description='结束日期 YYYY-MM-DD'),
    ],
    responses={200: {'type': 'object', 'properties': {'total': {'type': 'integer'}}}}
)
@api_view(['GET'])
@require_login
def get_orders_total(request):
    """获取历史订单总数"""
    try:
        mt5 = get_mt5()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response({'error': '缺少 date_from 或 date_to'}, status=status.HTTP_400_BAD_REQUEST)

        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        total = mt5.history.get_history_orders_total(date_from, date_to)
        return Response({'date_from': date_from_str, 'date_to': date_to_str, 'total': total})
    except ValueError:
        return Response({'error': '日期格式错误，请使用 YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# 交易计算
# ============================================================

@extend_schema(
    tags=['Calculator'],
    operation_id='calc_margin',
    summary='计算保证金',
    description='计算开仓所需保证金',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True),
        OpenApiParameter(name='volume', type=float, required=True),
        OpenApiParameter(name='action', type=str, required=False, description='buy 或 sell', default='buy'),
    ],
    responses={200: {'type': 'object', 'properties': {'margin': {'type': 'number'}}}}
)
@api_view(['GET'])
@require_login
def calc_margin(request):
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        volume = request.query_params.get('volume')
        action = request.query_params.get('action', 'buy')

        if not symbol or not volume:
            return Response({'error': '缺少 symbol 或 volume'}, status=status.HTTP_400_BAD_REQUEST)

        margin = mt5.calculator.calc_margin(symbol, float(volume), action=action)
        return Response({'symbol': symbol, 'volume': float(volume), 'action': action, 'margin': margin})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Calculator'],
    operation_id='calc_profit',
    summary='计算盈亏',
    description='计算预期盈亏',
    parameters=[
        OpenApiParameter(name='symbol', type=str, required=True),
        OpenApiParameter(name='volume', type=float, required=True),
        OpenApiParameter(name='price_open', type=float, required=True),
        OpenApiParameter(name='price_close', type=float, required=True),
        OpenApiParameter(name='action', type=str, required=False, default='buy'),
    ],
    responses={200: {'type': 'object', 'properties': {'profit': {'type': 'number'}}}}
)
@api_view(['GET'])
@require_login
def calc_profit(request):
    try:
        mt5 = get_mt5()
        symbol = request.query_params.get('symbol')
        volume = request.query_params.get('volume')
        price_open = request.query_params.get('price_open')
        price_close = request.query_params.get('price_close')
        action = request.query_params.get('action', 'buy')

        if not all([symbol, volume, price_open, price_close]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        profit = mt5.calculator.calc_profit(
            symbol, float(volume),
            price_open=float(price_open),
            price_close=float(price_close),
            action=action
        )
        return Response({
            'symbol': symbol, 'volume': float(volume), 'action': action,
            'price_open': float(price_open), 'price_close': float(price_close),
            'profit': profit
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
