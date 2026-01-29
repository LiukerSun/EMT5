"""
API Token 模型

用于 API 认证的 Token，只能通过程序生成，不支持用户自行创建
"""

import secrets
import hashlib
from django.db import models
from django.utils import timezone


class APIToken(models.Model):
    """
    API Token 模型

    Token 只能通过程序生成，用于 API 认证
    """

    name = models.CharField(
        max_length=100,
        verbose_name="Token 名称",
        help_text="用于标识 Token 用途"
    )
    key = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token Key",
        help_text="Token 的哈希值，用于验证"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="过期时间",
        help_text="为空表示永不过期"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否启用"
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最后使用时间"
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="描述"
    )

    class Meta:
        db_table = "api_tokens"
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({'启用' if self.is_active else '禁用'})"

    @property
    def is_expired(self) -> bool:
        """检查 Token 是否已过期"""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """检查 Token 是否有效（启用且未过期）"""
        return self.is_active and not self.is_expired

    def update_last_used(self):
        """更新最后使用时间"""
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])

    @classmethod
    def generate_token(cls, name: str, expires_in_days: int = None, description: str = "") -> tuple:
        """
        生成新的 API Token

        参数:
            name: Token 名称
            expires_in_days: 过期天数，None 表示永不过期
            description: Token 描述

        返回:
            tuple: (APIToken 实例, 原始 Token 字符串)

        注意:
            原始 Token 只在创建时返回一次，之后无法再获取
        """
        raw_token = secrets.token_hex(32)
        token_hash = cls._hash_token(raw_token)

        expires_at = None
        if expires_in_days is not None:
            expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)

        token = cls.objects.create(
            name=name,
            key=token_hash,
            expires_at=expires_at,
            description=description
        )

        return token, raw_token

    @classmethod
    def verify_token(cls, raw_token: str):
        """
        验证 Token

        参数:
            raw_token: 原始 Token 字符串

        返回:
            APIToken: 如果验证成功返回 Token 实例，否则返回 None
        """
        if not raw_token:
            return None

        token_hash = cls._hash_token(raw_token)

        try:
            token = cls.objects.get(key=token_hash)
            if token.is_valid:
                token.update_last_used()
                return token
            return None
        except cls.DoesNotExist:
            return None

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """计算 Token 的哈希值"""
        return hashlib.sha256(raw_token.encode()).hexdigest()
