"""
数据转换工具模块

提供统一的数据转换功能，包括时间戳转换、namedtuple 转字典等
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union


def to_dict(obj) -> Optional[Dict[str, Any]]:
    """
    将 namedtuple 或类似对象转换为字典

    参数:
        obj: 要转换的对象（通常是 MT5 返回的 namedtuple）

    返回:
        Dict: 转换后的字典，如果对象为 None 则返回 None

    使用示例:
        account_info = mt5.account_info()
        account_dict = to_dict(account_info)
    """
    if obj is None:
        return None

    if hasattr(obj, '_asdict'):
        return obj._asdict()

    if isinstance(obj, dict):
        return obj

    # 尝试转换为字典
    try:
        return dict(obj)
    except (TypeError, ValueError):
        return None


def add_datetime_fields(
    data: Dict[str, Any],
    time_fields: List[str],
    suffix: str = '_dt'
) -> Dict[str, Any]:
    """
    为字典中的时间戳字段添加对应的 datetime 对象

    参数:
        data: 包含时间戳的字典
        time_fields: 需要转换的时间戳字段名列表
        suffix: datetime 字段的后缀，默认 '_dt'

    返回:
        Dict: 添加了 datetime 字段的字典

    使用示例:
        tick = {'time': 1704067200, 'bid': 1.1000}
        tick = add_datetime_fields(tick, ['time'])
        # tick['time_dt'] 现在是 datetime 对象
    """
    if data is None:
        return data

    for field in time_fields:
        if field in data and data[field] and data[field] > 0:
            timestamp = data[field]
            # 处理毫秒级时间戳
            if field.endswith('_msc') or timestamp > 10000000000:
                timestamp = timestamp / 1000.0
            data[f'{field}{suffix}'] = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    return data


def convert_bars_to_dict(rates) -> List[Dict[str, Any]]:
    """
    将 K 线数据（numpy 数组）转换为字典列表

    参数:
        rates: MT5 返回的 numpy 数组

    返回:
        List[Dict]: K 线数据字典列表

    使用示例:
        rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 100)
        bars = convert_bars_to_dict(rates)
    """
    if rates is None:
        return []

    bars = []
    for rate in rates:
        bar = {
            'time': int(rate['time']),
            'open': float(rate['open']),
            'high': float(rate['high']),
            'low': float(rate['low']),
            'close': float(rate['close']),
            'tick_volume': int(rate['tick_volume']),
            'spread': int(rate['spread']),
            'real_volume': int(rate['real_volume']),
        }
        # 添加时区感知的 datetime 对象
        bar['time_dt'] = datetime.fromtimestamp(bar['time'], tz=timezone.utc)
        bars.append(bar)

    return bars


def convert_ticks_to_dict(ticks) -> List[Dict[str, Any]]:
    """
    将 Tick 数据（numpy 数组）转换为字典列表

    参数:
        ticks: MT5 返回的 numpy 数组

    返回:
        List[Dict]: Tick 数据字典列表

    使用示例:
        ticks = mt5.copy_ticks_from("EURUSD", start_time, 1000, mt5.COPY_TICKS_ALL)
        tick_list = convert_ticks_to_dict(ticks)
    """
    if ticks is None:
        return []

    tick_list = []
    for tick in ticks:
        tick_dict = {
            'time': int(tick['time']),
            'bid': float(tick['bid']),
            'ask': float(tick['ask']),
            'last': float(tick['last']),
            'volume': int(tick['volume']),
            'time_msc': int(tick['time_msc']),
            'flags': int(tick['flags']),
        }
        # 添加时区感知的 datetime 对象
        tick_dict['time_dt'] = datetime.fromtimestamp(tick_dict['time'], tz=timezone.utc)
        tick_dict['time_msc_dt'] = datetime.fromtimestamp(
            tick_dict['time_msc'] / 1000.0, tz=timezone.utc
        )
        tick_list.append(tick_dict)

    return tick_list


def convert_orders_to_dict(orders) -> List[Dict[str, Any]]:
    """
    将订单数据转换为字典列表

    参数:
        orders: MT5 返回的订单元组

    返回:
        List[Dict]: 订单数据字典列表
    """
    if orders is None:
        return []

    order_list = []
    for order in orders:
        order_dict = order._asdict()
        # 添加时区感知的时间字段
        time_fields = ['time_setup', 'time_expiration', 'time_done']
        for field in time_fields:
            if field in order_dict and order_dict[field] > 0:
                order_dict[f'{field}_dt'] = datetime.fromtimestamp(
                    order_dict[field], tz=timezone.utc
                )
        order_list.append(order_dict)

    return order_list


def convert_positions_to_dict(positions) -> List[Dict[str, Any]]:
    """
    将持仓数据转换为字典列表

    参数:
        positions: MT5 返回的持仓元组

    返回:
        List[Dict]: 持仓数据字典列表
    """
    if positions is None:
        return []

    position_list = []
    for position in positions:
        pos_dict = position._asdict()
        # 添加时区感知的时间字段
        if 'time' in pos_dict and pos_dict['time'] > 0:
            pos_dict['time_dt'] = datetime.fromtimestamp(
                pos_dict['time'], tz=timezone.utc
            )
        if 'time_update' in pos_dict and pos_dict['time_update'] > 0:
            pos_dict['time_update_dt'] = datetime.fromtimestamp(
                pos_dict['time_update'], tz=timezone.utc
            )
        position_list.append(pos_dict)

    return position_list


def convert_deals_to_dict(deals) -> List[Dict[str, Any]]:
    """
    将成交数据转换为字典列表

    参数:
        deals: MT5 返回的成交元组

    返回:
        List[Dict]: 成交数据字典列表
    """
    if deals is None:
        return []

    deal_list = []
    for deal in deals:
        deal_dict = deal._asdict()
        # 添加时区感知的时间字段
        if 'time' in deal_dict and deal_dict['time'] > 0:
            deal_dict['time_dt'] = datetime.fromtimestamp(
                deal_dict['time'], tz=timezone.utc
            )
        if 'time_msc' in deal_dict and deal_dict['time_msc'] > 0:
            deal_dict['time_msc_dt'] = datetime.fromtimestamp(
                deal_dict['time_msc'] / 1000.0, tz=timezone.utc
            )
        deal_list.append(deal_dict)

    return deal_list
