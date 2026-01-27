"""
EMT5 - MetaTrader 5 Python 封装库

整合了连接管理、账户信息、品种信息等功能
"""

from utils import logger
from .core import MT5Connection
from .info import MT5Account, MT5Symbol, MT5History
from .trade import MT5Order, MT5Calculator


class EMT5:
    """
    MetaTrader 5 封装类

    整合了连接管理、账户信息、品种信息等功能
    """

    def __init__(self, default_magic: int = 0, keep_alive: bool = False):
        """
        初始化 EMT5 实例

        参数:
            default_magic: 默认 EA 标识号，默认 0
            keep_alive: 如果为 True，退出上下文管理器时不会断开连接（适配 Web 服务常驻模式）
                       在 Django 等 Web 框架中，建议设置为 True，避免意外断开连接
        """
        self._connection = MT5Connection()
        self.account = MT5Account(self._connection)
        self.symbol = MT5Symbol(self._connection)
        self.order = MT5Order(self._connection, default_magic)
        self.history = MT5History(self._connection)
        self.calculator = MT5Calculator(self._connection)
        self.default_magic = default_magic
        self.keep_alive = keep_alive

    # ==================== 连接管理 ====================

    def initialize(
        self,
        path=None,
        login=None,
        password=None,
        server=None,
        timeout=60000,
        portable=False,
    ):
        """
        建立与 MetaTrader 5 终端的连接

        此方法用于初始化并连接到 MT5 终端。可以指定终端路径、登录账户信息等参数。
        连接成功后才能执行其他交易操作。

        参数:
            path: MT5 终端可执行文件的完整路径
                - Windows 示例: r"C:\\Program Files\\MetaTrader 5\\terminal64.exe"
                - 如果不指定，会尝试自动查找已安装的 MT5
            login: 交易账户号码（整数）
                - 例如: 12345678
                - 如果不指定，会连接到上次登录的账户
            password: 交易账户密码（字符串）
                - 必须与 login 参数配合使用
            server: 交易服务器名称
                - 例如: "XMGlobal-MT5 9", "MetaQuotes-Demo"
                - 必须与 login 参数配合使用
            timeout: 连接超时时间（毫秒）
                - 默认 60000 毫秒（60秒）
                - 网络较慢时可适当增加
            portable: 是否使用便携模式
                - True: 使用便携模式（数据存储在终端目录）
                - False: 使用标准模式（默认）

        返回:
            bool: 连接成功返回 True，失败返回 False

        使用示例:
            # 示例 1：自动连接（使用上次登录的账户）
            mt5 = EMT5()
            if mt5.initialize():
                print("连接成功")

            # 示例 2：指定终端路径和账户信息
            mt5 = EMT5()
            success = mt5.initialize(
                path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
                login=12345678,
                password="your_password",
                server="XMGlobal-MT5 9",
                timeout=60000
            )

            # 示例 3：使用上下文管理器（推荐）
            with EMT5() as mt5:
                if mt5.initialize(login=12345678, password="pwd", server="server"):
                    # 执行交易操作
                    pass
                # 退出时自动断开连接

        注意事项:
            1. 必须先安装 MT5 终端软件
            2. 如果指定了 login，则必须同时指定 password 和 server
            3. 连接失败时会在日志中输出错误信息
            4. 使用完毕后应调用 shutdown() 断开连接
            5. 推荐使用上下文管理器（with 语句）自动管理连接
        """
        return self._connection.initialize(
            path, login, password, server, timeout, portable
        )

    def shutdown(self):
        """
        关闭与 MetaTrader 5 终端的连接

        断开与 MT5 终端的连接，释放相关资源。建议在程序结束前调用此方法。

        使用示例:
            mt5 = EMT5()
            mt5.initialize()
            # ... 执行交易操作 ...
            mt5.shutdown()  # 断开连接

        注意事项:
            1. 使用上下文管理器（with 语句）时会自动调用此方法
            2. 重复调用此方法是安全的
            3. 断开连接后需要重新调用 initialize() 才能继续使用
        """
        self._connection.shutdown()

    def is_connected(self):
        """
        检查是否已连接到 MT5 终端

        返回:
            bool: 已连接返回 True，未连接返回 False

        使用示例:
            mt5 = EMT5()
            if not mt5.is_connected():
                mt5.initialize()
        """
        return self._connection.is_connected()

    def get_terminal_info(self):
        """获取终端信息"""
        return self._connection.get_terminal_info()

    def get_version(self):
        """获取 MetaTrader 5 版本信息"""
        return self._connection.get_version()

    # ==================== 账户信息 ====================

    def get_account_info(self):
        """
        获取当前交易账户的详细信息

        返回:
            Dict: 账户信息字典，包含以下字段：
                - login: 账户号码
                - balance: 账户余额
                - equity: 账户净值（余额 + 浮动盈亏）
                - margin: 已用保证金
                - margin_free: 可用保证金
                - margin_level: 保证金水平（百分比）
                - profit: 当前浮动盈亏
                - credit: 信用额度
                - leverage: 杠杆比例
                - currency: 账户货币
                - name: 账户持有人姓名
                - server: 服务器名称
                - company: 经纪商名称
            失败时返回 None

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            account = mt5.get_account_info()
            if account:
                print(f"账户余额: {account['balance']}")
                print(f"账户净值: {account['equity']}")
                print(f"可用保证金: {account['margin_free']}")
                print(f"保证金水平: {account['margin_level']}%")
        """
        return self.account.get_account_info()

    # ==================== 品种信息 ====================

    def get_symbols(self, group="*"):
        """获取所有金融交易品种"""
        return self.symbol.get_symbols(group)

    def get_symbol_info(self, symbol):
        """
        获取指定交易品种的详细信息

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_", "BTCUSD"

        返回:
            Dict: 品种信息字典，包含以下重要字段：
                - name: 品种名称
                - ask: 当前卖出价（买入时使用）
                - bid: 当前买入价（卖出时使用）
                - point: 最小价格变动单位
                - digits: 价格小数位数
                - spread: 点差
                - volume_min: 最小交易量
                - volume_max: 最大交易量
                - volume_step: 交易量步进值
                - trade_contract_size: 合约大小
                - trade_stops_level: 止损位最小距离（点数）
                - trade_freeze_level: 冻结距离（点数）
                - filling_mode: 支持的成交类型
                - description: 品种描述
            失败时返回 None

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 获取品种信息
            info = mt5.get_symbol_info("EURUSD")
            if info:
                print(f"当前价格: Ask={info['ask']}, Bid={info['bid']}")
                print(f"点差: {info['spread']} 点")
                print(f"最小交易量: {info['volume_min']} 手")
                print(f"最小价格变动: {info['point']}")

                # 计算止损止盈价格
                point = info['point']
                sl_distance = 50  # 50 点止损
                sl_price = info['ask'] - sl_distance * point
        """
        return self.symbol.get_symbol_info(symbol)

    def symbol_select(self, symbol, enable=True):
        """
        在市场观察窗口中启用或禁用指定交易品种

        交易前必须先启用品种，否则无法获取价格信息和执行交易。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_"
            enable: True 表示启用，False 表示禁用，默认 True

        返回:
            bool: 操作成功返回 True，失败返回 False

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 启用品种
            if mt5.symbol_select("GOLD_", True):
                print("品种已启用")
                # 现在可以获取价格和交易
                info = mt5.get_symbol_info("GOLD_")

            # 禁用品种
            mt5.symbol_select("GOLD_", False)

        注意事项:
            1. 交易前必须先启用品种
            2. 品种名称必须准确，区分大小写
            3. 某些品种可能在特定服务器上不可用
        """
        return self.symbol.symbol_select(symbol, enable)

    def get_symbol_info_tick(self, symbol):
        """
        获取指定品种的最新tick数据（实时报价）

        快捷方法，用于获取品种的最新价格信息。适用于需要实时监控价格的场景。

        参数:
            symbol: 交易品种名称，例如 "EURUSD", "GOLD_"

        返回:
            Dict: tick数据字典，包含：
                - time: tick时间（秒）
                - bid: 买入价
                - ask: 卖出价
                - last: 最后成交价
                - volume: 成交量
                - time_msc: tick时间（毫秒）
                - flags: tick标志
                - volume_real: 实际成交量
            失败时返回 None

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 获取实时价格
            tick = mt5.get_symbol_info_tick("EURUSD")
            if tick:
                print(f"买价: {tick['bid']}, 卖价: {tick['ask']}")

        详细说明请参考 MT5Symbol.get_symbol_info_tick() 方法
        """
        return self.symbol.get_symbol_info_tick(symbol)

    # ==================== 交易操作 ====================

    def order_send(self, request):
        """
        发送交易请求到交易服务器

        此方法用于执行实际的交易操作，包括开仓、平仓、挂单等。

        参数:
            request: 交易请求字典，通常由 create_market_buy_request() 等方法生成
                包含 action, symbol, volume, type, price 等字段

        返回:
            Dict: 交易结果字典，包含以下字段：
                - retcode: 返回码（10009 表示成功）
                - deal: 成交票据号
                - order: 订单票据号（持仓号）
                - volume: 成交量
                - price: 成交价格
                - bid: 当前买价
                - ask: 当前卖价
                - comment: 结果注释
                - request: 原始请求结构
            失败时返回 None

        常见返回码:
            - 10009: TRADE_RETCODE_DONE - 请求已完成
            - 10004: TRADE_RETCODE_REQUOTE - 重新报价
            - 10006: TRADE_RETCODE_REJECT - 请求被拒绝
            - 10013: TRADE_RETCODE_INVALID_PRICE - 价格无效
            - 10014: TRADE_RETCODE_INVALID_STOPS - 止损/止盈无效
            - 10016: TRADE_RETCODE_MARKET_CLOSED - 市场关闭
            - 10019: TRADE_RETCODE_NO_MONEY - 资金不足

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 创建买入请求
            request = mt5.create_market_buy_request(
                symbol="EURUSD",
                volume=0.1,
                sl=1.0950,
                tp=1.1050
            )

            # 发送订单
            result = mt5.order_send(request)
            if result and result['retcode'] == 10009:
                print(f"交易成功！订单号: {result['order']}")
                print(f"成交价格: {result['price']}")
            else:
                print(f"交易失败，返回码: {result['retcode']}")

        注意事项:
            1. 发送前建议使用 order_check() 验证请求
            2. 检查返回码确认交易是否成功
            3. 保存 order 字段作为持仓号，用于后续平仓
            4. 市场关闭时无法交易
            5. 确保账户有足够的保证金
        """
        return self.order.order_send(request)

    def order_check(self, request):
        """
        检查交易请求的正确性（不实际发送到服务器）

        此方法用于在发送订单前验证请求是否有效，可以检查保证金是否足够、
        价格是否合理等，避免发送无效订单。

        参数:
            request: 交易请求字典（格式同 order_send）

        返回:
            Dict: 检查结果字典，包含：
                - retcode: 返回码（10009 或 0 表示检查通过）
                - balance: 操作后的预期余额
                - equity: 操作后的预期净值
                - profit: 预期盈利
                - margin: 所需保证金
                - margin_free: 操作后的可用保证金
                - margin_level: 操作后的保证金水平
                - comment: 结果注释
                - request: 原始请求结构
            失败时返回 None

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 创建交易请求
            request = mt5.create_market_buy_request(
                symbol="EURUSD",
                volume=0.1
            )

            # 检查订单
            check = mt5.order_check(request)
            if check and (check['retcode'] == 0 or check['retcode'] == 10009):
                print(f"订单检查通过")
                print(f"所需保证金: {check['margin']}")
                print(f"操作后可用保证金: {check['margin_free']}")

                # 检查通过后发送订单
                result = mt5.order_send(request)
            else:
                print(f"订单检查失败: {check['comment']}")

        注意事项:
            1. 此方法不会实际执行交易，只是模拟检查
            2. 检查通过不保证实际发送时一定成功（价格可能变化）
            3. 建议在发送大额订单前先检查
            4. 可以用来计算所需保证金
        """
        return self.order.order_check(request)

    def create_market_buy_request(
        self, symbol, volume, sl=0.0, tp=0.0, deviation=20, magic=None, comment=""
    ):
        """
        创建市价买入请求

        快捷方法，用于创建市价买入订单请求。返回的请求字典可以直接传递给 order_send()。

        参数:
            symbol: 交易品种名称
            volume: 交易量（手数）
            sl: 止损价格，0 表示不设置
            tp: 止盈价格，0 表示不设置
            deviation: 最大价格偏差（点数），默认 20
            magic: EA 标识号，None 表示使用默认值
            comment: 订单注释

        返回:
            Dict: 交易请求字典，可直接用于 order_send()

        使用示例:
            mt5 = EMT5()
            mt5.initialize()

            # 创建并发送买入订单
            request = mt5.create_market_buy_request("EURUSD", 0.1)
            result = mt5.order_send(request)

        详细说明请参考 MT5Order.create_market_buy_request() 方法
        """
        return self.order.create_market_buy_request(
            symbol, volume, sl, tp, deviation, magic, comment
        )

    def create_market_sell_request(
        self,
        symbol,
        volume,
        sl=0.0,
        tp=0.0,
        deviation=20,
        magic=None,
        comment="",
        position=0,
    ):
        """
        创建市价卖出请求

        快捷方法，用于创建市价卖出订单请求（开空仓或平多仓）。

        参数:
            symbol: 交易品种名称
            volume: 交易量（手数）
            sl: 止损价格，0 表示不设置
            tp: 止盈价格，0 表示不设置
            deviation: 最大价格偏差（点数），默认 20
            magic: EA 标识号，None 表示使用默认值
            comment: 订单注释
            position: 持仓票据号，用于平仓，0 表示开新仓

        返回:
            Dict: 交易请求字典，可直接用于 order_send()

        使用示例:
            # 开空仓
            request = mt5.create_market_sell_request("EURUSD", 0.1)

            # 平多仓
            request = mt5.create_market_sell_request(
                symbol="EURUSD",
                volume=0.1,
                position=position_id  # 之前买入时获得的持仓号
            )

        详细说明请参考 MT5Order.create_market_sell_request() 方法
        """
        return self.order.create_market_sell_request(
            symbol, volume, sl, tp, deviation, magic, comment, position
        )

    def create_limit_buy_request(
        self, symbol, volume, price, sl=0.0, tp=0.0, magic=None, comment=""
    ):
        """
        创建限价买入挂单请求

        快捷方法，用于创建限价买入挂单（价格低于当前价时触发买入）。

        参数:
            symbol: 交易品种名称
            volume: 交易量（手数）
            price: 挂单价格（必须低于当前价）
            sl: 止损价格，0 表示不设置
            tp: 止盈价格，0 表示不设置
            magic: EA 标识号，None 表示使用默认值
            comment: 订单注释

        返回:
            Dict: 交易请求字典，可直接用于 order_send()

        使用示例:
            # 当前价 1.1000，等待跌到 1.0950 时买入
            request = mt5.create_limit_buy_request(
                symbol="EURUSD",
                volume=0.1,
                price=1.0950
            )
            result = mt5.order_send(request)

        详细说明请参考 MT5Order.create_limit_buy_request() 方法
        """
        return self.order.create_limit_buy_request(
            symbol, volume, price, sl, tp, magic, comment
        )

    def create_limit_sell_request(
        self, symbol, volume, price, sl=0.0, tp=0.0, magic=None, comment=""
    ):
        """
        创建限价卖出挂单请求

        快捷方法，用于创建限价卖出挂单（价格高于当前价时触发卖出）。

        参数:
            symbol: 交易品种名称
            volume: 交易量（手数）
            price: 挂单价格（必须高于当前价）
            sl: 止损价格，0 表示不设置
            tp: 止盈价格，0 表示不设置
            magic: EA 标识号，None 表示使用默认值
            comment: 订单注释

        返回:
            Dict: 交易请求字典，可直接用于 order_send()

        使用示例:
            # 当前价 1.1000，等待涨到 1.1050 时卖出
            request = mt5.create_limit_sell_request(
                symbol="EURUSD",
                volume=0.1,
                price=1.1050
            )
            result = mt5.order_send(request)

        详细说明请参考 MT5Order.create_limit_sell_request() 方法
        """
        return self.order.create_limit_sell_request(
            symbol, volume, price, sl, tp, magic, comment
        )

    def get_orders(self, symbol=None, ticket=None, group=None):
        """
        获取挂单列表

        参数:
            symbol: 交易品种名称，用于过滤
            ticket: 订单票据号，用于获取特定订单
            group: 品种组，用于过滤

        返回:
            List[Dict]: 挂单列表，每个挂单包含订单信息
            失败时返回 None
        """
        import MetaTrader5 as mt5

        if not self.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            elif ticket:
                orders = mt5.orders_get(ticket=ticket)
            elif group:
                orders = mt5.orders_get(group=group)
            else:
                orders = mt5.orders_get()

            if orders is None:
                return []

            # 转换为字典列表
            return [order._asdict() for order in orders]
        except Exception as e:
            logger.error(f"获取挂单失败: {str(e)}")
            return None

    def get_positions(self, symbol=None, ticket=None, group=None):
        """
        获取持仓列表

        参数:
            symbol: 交易品种名称，用于过滤
            ticket: 持仓票据号，用于获取特定持仓
            group: 品种组，用于过滤

        返回:
            List[Dict]: 持仓列表，每个持仓包含持仓信息
            失败时返回 None
        """
        import MetaTrader5 as mt5

        if not self.is_connected():
            logger.error("未连接到 MT5 终端")
            return None

        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            elif ticket:
                positions = mt5.positions_get(ticket=ticket)
            elif group:
                positions = mt5.positions_get(group=group)
            else:
                positions = mt5.positions_get()

            if positions is None:
                return []

            # 转换为字典列表
            return [position._asdict() for position in positions]
        except Exception as e:
            logger.error(f"获取持仓失败: {str(e)}")
            return None

    # ==================== 上下文管理器 ====================

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出时根据配置决定是否关闭连接

        如果 keep_alive=True（Web 服务模式），则不会断开连接
        如果 keep_alive=False（脚本模式），则自动断开连接
        """
        if not self.keep_alive:
            self.shutdown()
        return False

    def __del__(self):
        """析构时确保连接已关闭"""
        if self.is_connected():
            self.shutdown()
