# MT5 API 使用说明

## 连接测试成功 ✅

您的MT5账户已成功连接：
- **账号**: 316154676
- **服务器**: XMGlobal-MT5 7
- **余额**: 2204.0 USD
- **杠杆**: 1:1000

---

## API 连接端点

### POST /api/connection/initialize/

初始化MT5连接

**正确的请求示例：**

```json
{
    "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    "login": 316154676,
    "password": "mniLiuker0520..",
    "server": "XMGlobal-MT5 7",
    "timeout": 60000,
    "portable": false
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 默认值 | 有效范围 |
|------|------|------|------|--------|----------|
| path | string | 否 | MT5终端路径 | 自动检测 | - |
| login | integer | 否 | 账户号码 | - | - |
| password | string | 否 | 账户密码 | - | - |
| server | string | 否 | 服务器名称 | - | - |
| timeout | integer | 否 | 超时时间（毫秒） | 60000 | 1000-300000 |
| portable | boolean | 否 | 便携模式 | false | - |

**⚠️ 注意事项：**

1. **timeout参数范围**: 1000-300000毫秒（1-300秒）
   - ❌ 错误: `"timeout": 1780679122561` （太大）
   - ✅ 正确: `"timeout": 60000` （60秒）

2. **自动启动MT5**: 如果MT5终端未运行，系统会自动启动

3. **路径格式**: Windows路径需要使用双反斜杠 `\\` 或单正斜杠 `/`

---

## 成功响应示例

```json
{
    "success": true,
    "message": "MT5 连接成功",
    "data": {
        "connected": true
    }
}
```

## 错误响应示例

```json
{
    "success": false,
    "error": "连接失败，已重试 3 次"
}
```

---

## 其他可用端点

### 1. 获取连接状态
```
GET /api/connection/status/
```

### 2. 关闭连接
```
POST /api/connection/shutdown/
```

### 3. 获取账户信息
```
GET /api/account/info/
```

### 4. 获取品种列表
```
GET /api/symbols/list/?group=*
```

### 5. 市价买入
```
POST /api/trade/market-buy/
```

### 6. 市价卖出
```
POST /api/trade/market-sell/
```

---

## 快速测试

使用curl测试连接：

```bash
curl -X POST http://localhost:8000/api/connection/initialize/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": 316154676,
    "password": "mniLiuker0520..",
    "server": "XMGlobal-MT5 7",
    "timeout": 60000
  }'
```

---

## 常见问题

### Q1: 连接失败 "IPC send failed"
**原因**: MT5终端未运行
**解决**: 系统会自动启动MT5，等待几秒后重试

### Q2: timeout参数验证失败
**原因**: timeout值超出范围
**解决**: 使用1000-300000之间的值（推荐60000）

### Q3: 账户信息错误
**原因**: login/password/server不匹配
**解决**: 检查账户信息是否正确

---

## 技术支持

如有问题，请检查：
1. MT5终端是否已安装
2. 账户信息是否正确
3. 网络连接是否正常
4. 防火墙是否允许MT5通信
