"""
API 路由配置
"""
from django.urls import path
from api_server import views

urlpatterns = [
    # 健康检查
    path('health/', views.health_check, name='health'),
    path('terminal/', views.get_terminal_info, name='terminal-info'),
    path('version/', views.get_version, name='version'),

    # 账户
    path('account/login/', views.account_login, name='account-login'),
    path('account/', views.get_account_info, name='account-info'),

    # 品种
    path('symbols/', views.get_symbols, name='symbol-list'),
    path('symbols/<str:symbol>/', views.get_symbol_info, name='symbol-info'),
    path('symbols/<str:symbol>/select/', views.symbol_select, name='symbol-select'),
    path('symbols/<str:symbol>/tick/', views.get_symbol_tick, name='symbol-tick'),

    # 持仓
    path('positions/total/', views.get_positions_total, name='positions-total'),
    path('positions/', views.get_positions, name='position-list'),
    path('positions/<int:ticket>/', views.get_position_detail, name='position-detail'),

    # 挂单
    path('orders/total/', views.get_orders_total, name='orders-total'),
    path('orders/', views.get_orders, name='order-list'),
    path('orders/<int:ticket>/', views.get_order_detail, name='order-detail'),

    # 交易
    path('trade/buy/', views.market_buy, name='trade-buy'),
    path('trade/sell/', views.market_sell, name='trade-sell'),
    path('trade/pending/', views.pending_order, name='trade-pending'),
    path('trade/check/', views.order_check, name='trade-check'),
    path('trade/close/', views.close_position, name='trade-close'),
    path('trade/modify/', views.modify_position, name='trade-modify'),

    # 历史数据
    path('history/bars/', views.get_bars, name='history-bars'),
    path('history/bars/range/', views.get_bars_range, name='history-bars-range'),
    path('history/ticks/', views.get_ticks, name='history-ticks'),
    path('history/ticks/range/', views.get_ticks_range, name='history-ticks-range'),
    path('history/orders/', views.get_history_orders, name='history-orders'),
    path('history/orders/total/', views.get_orders_total, name='history-orders-total'),
    path('history/deals/', views.get_deals, name='history-deals'),
    path('history/deals/total/', views.get_deals_total, name='history-deals-total'),

    # 计算
    path('calc/margin/', views.calc_margin, name='calc-margin'),
    path('calc/profit/', views.calc_profit, name='calc-profit'),
]
