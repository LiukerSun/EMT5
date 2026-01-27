from utils import EMT5, logger
import MetaTrader5 as mt5
import time


def main():
    """黄金交易示例 - 简化版本，只保留函数调用和逻辑判断"""
    # 创建 EMT5 实例
    mt5_client = EMT5()

    # 账户信息
    mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    mt_id = 1234
    mt_server = "123"
    password = "123"

    # 交易参数
    symbol = "GOLD_"
    lot = 0.01
    deviation = 20
    magic = 123456
    sl_distance = 500
    tp_distance = 500

    try:
        # 1. 连接到 MT5
        if not mt5_client.initialize(
            path=mt5_path,
            timeout=60000,
            login=mt_id,
            server=mt_server,
            password=password,
        ):
            return

        # 2. 启用品种
        if not mt5_client.symbol_select(symbol, True):
            return

        # 3. 获取品种信息
        symbol_info = mt5_client.get_symbol_info(symbol)
        if not symbol_info:
            return

        # 4. 创建买入订单
        buy_request = mt5_client.create_market_buy_request(
            symbol=symbol,
            volume=lot,
            deviation=deviation,
            magic=magic,
            comment="黄金买入",
        )

        # 5. 设置成交类型
        filling_mode = symbol_info.get("filling_mode", 0)
        if filling_mode & 2:
            buy_request["type_filling"] = mt5.ORDER_FILLING_IOC
        elif filling_mode & 1:
            buy_request["type_filling"] = mt5.ORDER_FILLING_FOK

        # 6. 设置止损止盈
        point = symbol_info["point"]
        buy_request["sl"] = buy_request["price"] - sl_distance * point
        buy_request["tp"] = buy_request["price"] + tp_distance * point

        # 7. 检查订单
        check_result = mt5_client.order_check(buy_request)
        if not check_result or (
            check_result["retcode"] != 0 and check_result["retcode"] != 10009
        ):
            return

        # 8. 发送订单
        result = mt5_client.order_send(buy_request)
        if not result or result["retcode"] != 10009:
            return

        # 9. 获取持仓号
        position_id = result["order"]

        # 10. 等待后平仓
        time.sleep(10)

        # 11. 创建平仓请求
        close_request = mt5_client.create_market_sell_request(
            symbol=symbol,
            volume=lot,
            deviation=deviation,
            magic=magic,
            comment="黄金平仓",
            position=position_id,
        )

        # 12. 发送平仓订单
        close_result = mt5_client.order_send(close_request)
        if not close_result or close_result["retcode"] != 10009:
            return

    except Exception as e:
        logger.error(f"异常: {str(e)}")

    finally:
        mt5_client.shutdown()


if __name__ == "__main__":
    main()
