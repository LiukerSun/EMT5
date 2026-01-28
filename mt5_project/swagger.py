"""
Swagger 文档配置
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger 文档配置
schema_view = get_schema_view(
    openapi.Info(
        title="MT5 Trading API",
        default_version='v1',
        description="""
# MT5 Trading REST API 文档

这是一个基于 Django REST Framework 的 MetaTrader 5 交易 API。

## 功能模块

### 连接管理
- 初始化 MT5 连接
- 关闭连接
- 查询连接状态

### 账户信息
- 获取账户详细信息（余额、净值、保证金等）

### 品种信息
- 获取交易品种列表
- 获取品种详细信息
- 获取实时 Tick 数据
- 启用/禁用品种

### 交易操作
- 市价买入/卖出
- 限价买入/卖出
- 订单检查
- 持仓查询
- 挂单查询

## 使用说明

1. 首先调用 `/api/connection/initialize/` 初始化 MT5 连接
2. 连接成功后即可调用其他接口
3. 所有接口返回统一的 JSON 格式

## 响应格式

成功响应：
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

错误响应：
```json
{
    "success": false,
    "error": "错误信息"
}
```

## 注意事项

- 交易操作会实际执行，请谨慎使用
- 使用前需要安装并运行 MetaTrader 5 终端
- 建议先使用 order_check 接口验证订单
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@mt5api.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
