"""
EMT5 完整功能展示
"""

from pprint import pprint
import sys
import io

# 设置 UTF-8 编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from utils import EMT5
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta


def main():
    """主函数"""
    # 账户配置
    config = {
        "path": r"C:\Program Files\MetaTrader 5\terminal64.exe",
        "login": 123,
        "server": "123",
        "password": "123",
    }

    symbol = "GOLD#"

    # 创建并连接
    mt5_client: EMT5 = EMT5(keep_alive=False)
    mt5_client.initialize(**config)

    # 1. 连接信息
    version = mt5_client.get_version()
    terminal = mt5_client.get_terminal_info()
    pprint({"version": version, "terminal": terminal})

    # 2. 账户信息
    account = mt5_client.get_account_info()
    pprint(account)

    # 3. 持仓信息
    positions = mt5_client.get_positions()
    pprint(positions)

    # 4. 挂单信息
    orders = mt5_client.get_orders()
    pprint(orders)

    # 5. 品种信息
    mt5_client.symbol_select(symbol, True)
    symbol_info = mt5_client.get_symbol_info(symbol)
    pprint(symbol_info)

    # 6. 历史K线数据
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=7)
    bars = mt5_client.history.get_bars(
        symbol=symbol,
        timeframe=mt5.TIMEFRAME_H1,
        date_from=date_from,
        date_to=now
    )
    if bars:
        pprint(bars[-5:])  # 最新5根K线

    # 7. Tick数据
    ticks = mt5_client.history.get_ticks(
        symbol=symbol,
        date_from=now - timedelta(minutes=5),
        date_to=now,
        flags=mt5.COPY_TICKS_ALL
    )
    if ticks:
        pprint(ticks[-3:])  # 最新3个Tick

    # 8. 历史订单
    history_orders = mt5_client.history.get_history_orders(
        date_from=now - timedelta(days=7),
        date_to=now
    )
    pprint(history_orders)

    # 9. 历史成交
    history_deals = mt5_client.history.get_history_deals(
        date_from=now - timedelta(days=7),
        date_to=now
    )
    pprint(history_deals)

    # 10. 保证金计算
    margin = mt5_client.calculator.calc_margin(symbol, 0.1, "buy")
    pprint({"margin": margin})

    # 11. 盈利计算
    entry_price = symbol_info['ask']
    close_price = entry_price + 100 * symbol_info['point']
    profit = mt5_client.calculator.calc_profit(
        symbol, 0.1, entry_price, close_price, "buy"
    )
    pprint({"profit": profit})

    # 12. 风险回报比
    risk_reward = mt5_client.calculator.calc_risk_reward(
        symbol=symbol,
        volume=0.1,
        entry_price=entry_price,
        sl_price=entry_price - 50 * symbol_info['point'],
        tp_price=entry_price + 100 * symbol_info['point'],
        action="buy"
    )
    pprint(risk_reward)

    # 13. 仓位计算
    risk_amount = account['balance'] * 0.01  # 1% 风险
    position_size = mt5_client.calculator.calc_position_size(
        symbol=symbol,
        risk_amount=risk_amount,
        entry_price=entry_price,
        sl_price=entry_price - 50 * symbol_info['point'],
        action="buy"
    )
    pprint({"position_size": position_size})

    # 14. 订单检查（Buy Limit挂单）
    pending_request = {
        'action': mt5.TRADE_ACTION_PENDING,
        'symbol': symbol,
        'volume': 0.01,
        'type': mt5.ORDER_TYPE_BUY_LIMIT,
        'price': symbol_info['bid'] - 100 * symbol_info['point'],
        'sl': symbol_info['bid'] - 600 * symbol_info['point'],
        'tp': symbol_info['bid'] + 400 * symbol_info['point'],
        'deviation': 20,
        'magic': 123456,
        'comment': 'EMT5 测试',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_RETURN,
    }
    check_result = mt5_client.order_check(pending_request)
    pprint(check_result)

    # 15. 市价单请求构建
    buy_request = mt5_client.create_market_buy_request(
        symbol=symbol,
        volume=0.01,
        deviation=20,
        magic=123456,
        comment="市价买入测试"
    )
    pprint(buy_request)

    sell_request = mt5_client.create_market_sell_request(
        symbol=symbol,
        volume=0.01,
        deviation=20,
        magic=123456,
        comment="市价卖出测试"
    )
    pprint(sell_request)

    # 断开连接
    mt5_client.shutdown()


if __name__ == "__main__":
    main()
