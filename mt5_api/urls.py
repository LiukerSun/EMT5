"""
MT5 API URL 配置
"""

from django.urls import path
from .views import (
    # 连接管理
    InitializeView,
    ShutdownView,
    ConnectionStatusView,
    # 账户信息
    AccountInfoView,
    # 品种信息
    SymbolsListView,
    SymbolInfoView,
    SymbolTickView,
    SymbolSelectView,
    # 交易操作
    MarketBuyView,
    MarketSellView,
    LimitBuyView,
    LimitSellView,
    OrderCheckView,
    PositionsView,
    OrdersView,
)

app_name = 'mt5_api'

urlpatterns = [
    # ==================== 连接管理 ====================
    path('connection/initialize/', InitializeView.as_view(), name='initialize'),
    path('connection/shutdown/', ShutdownView.as_view(), name='shutdown'),
    path('connection/status/', ConnectionStatusView.as_view(), name='status'),

    # ==================== 账户信息 ====================
    path('account/info/', AccountInfoView.as_view(), name='account-info'),

    # ==================== 品种信息 ====================
    path('symbols/list/', SymbolsListView.as_view(), name='symbols-list'),
    path('symbols/info/<str:symbol>/', SymbolInfoView.as_view(), name='symbol-info'),
    path('symbols/tick/<str:symbol>/', SymbolTickView.as_view(), name='symbol-tick'),
    path('symbols/select/', SymbolSelectView.as_view(), name='symbol-select'),

    # ==================== 交易操作 ====================
    path('trade/market-buy/', MarketBuyView.as_view(), name='market-buy'),
    path('trade/market-sell/', MarketSellView.as_view(), name='market-sell'),
    path('trade/limit-buy/', LimitBuyView.as_view(), name='limit-buy'),
    path('trade/limit-sell/', LimitSellView.as_view(), name='limit-sell'),
    path('trade/order-check/', OrderCheckView.as_view(), name='order-check'),
    path('trade/positions/', PositionsView.as_view(), name='positions'),
    path('trade/orders/', OrdersView.as_view(), name='orders'),
]
