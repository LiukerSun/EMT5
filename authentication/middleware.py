"""
API Token 认证中间件

用于验证 API 请求中的 Token
"""

from django.http import JsonResponse
from .models import APIToken


class TokenAuthMiddleware:
    """
    Token 认证中间件

    从请求头中提取 Token 并验证，支持以下格式：
    - Authorization: Bearer <token>
    - Authorization: Token <token>
    """

    # 不需要认证的路径
    EXEMPT_PATHS = [
        '/admin/',
        '/health/',
        '/api/docs/',
        '/api/schema/',
        '/api/redoc/',
        '/api/v1/health/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 检查是否为豁免路径
        if self._is_exempt(request.path):
            return self.get_response(request)

        # 提取并验证 Token
        token = self._extract_token(request)
        if token is None:
            return JsonResponse(
                {'error': '未提供认证 Token', 'code': 'NO_TOKEN'},
                status=401
            )

        # 验证 Token
        api_token = APIToken.verify_token(token)
        if api_token is None:
            return JsonResponse(
                {'error': 'Token 无效或已过期', 'code': 'INVALID_TOKEN'},
                status=401
            )

        # 将 Token 信息附加到请求对象
        request.api_token = api_token

        return self.get_response(request)

    def _is_exempt(self, path: str) -> bool:
        """检查路径是否豁免认证"""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False

    def _extract_token(self, request) -> str | None:
        """从请求头中提取 Token"""
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2:
            return None

        scheme, token = parts
        if scheme.lower() not in ('bearer', 'token'):
            return None

        return token
