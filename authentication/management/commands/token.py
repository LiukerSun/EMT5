"""
Token 管理命令

用法:
    python manage.py token create <name> [--expires <days>] [--description <desc>]
    python manage.py token list
    python manage.py token revoke <token_id>
    python manage.py token info <token_id>
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from authentication.models import APIToken


class Command(BaseCommand):
    help = 'API Token 管理命令'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='操作类型')

        # create 子命令
        create_parser = subparsers.add_parser('create', help='创建新 Token')
        create_parser.add_argument('name', type=str, help='Token 名称')
        create_parser.add_argument(
            '--expires', '-e',
            type=int,
            default=None,
            help='过期天数，不指定则永不过期'
        )
        create_parser.add_argument(
            '--description', '-d',
            type=str,
            default='',
            help='Token 描述'
        )

        # list 子命令
        subparsers.add_parser('list', help='列出所有 Token')

        # revoke 子命令
        revoke_parser = subparsers.add_parser('revoke', help='撤销 Token')
        revoke_parser.add_argument('token_id', type=int, help='Token ID')

        # info 子命令
        info_parser = subparsers.add_parser('info', help='查看 Token 详情')
        info_parser.add_argument('token_id', type=int, help='Token ID')

    def handle(self, *args, **options):
        action = options.get('action')

        if action == 'create':
            self._create_token(options)
        elif action == 'list':
            self._list_tokens()
        elif action == 'revoke':
            self._revoke_token(options)
        elif action == 'info':
            self._token_info(options)
        else:
            self.print_help('manage.py', 'token')

    def _create_token(self, options):
        """创建新 Token"""
        name = options['name']
        expires = options.get('expires')
        description = options.get('description', '')

        token_obj, raw_token = APIToken.generate_token(
            name=name,
            expires_in_days=expires,
            description=description
        )

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Token 创建成功！'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\nID:       {token_obj.id}')
        self.stdout.write(f'名称:     {token_obj.name}')
        self.stdout.write(f'创建时间: {token_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")}')

        if token_obj.expires_at:
            self.stdout.write(f'过期时间: {token_obj.expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write('过期时间: 永不过期')

        self.stdout.write(self.style.WARNING('\n' + '-' * 60))
        self.stdout.write(self.style.WARNING('请妥善保存以下 Token，它只会显示一次：'))
        self.stdout.write(self.style.WARNING('-' * 60))
        self.stdout.write(self.style.SUCCESS(f'\n{raw_token}\n'))
        self.stdout.write(self.style.WARNING('=' * 60 + '\n'))

    def _list_tokens(self):
        """列出所有 Token"""
        tokens = APIToken.objects.all()

        if not tokens.exists():
            self.stdout.write(self.style.WARNING('暂无 Token'))
            return

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(f'{"ID":<6} {"名称":<20} {"状态":<10} {"创建时间":<20} {"最后使用":<20}')
        self.stdout.write('=' * 80)

        for token in tokens:
            status = self._get_status_display(token)
            created = token.created_at.strftime('%Y-%m-%d %H:%M')
            last_used = token.last_used_at.strftime('%Y-%m-%d %H:%M') if token.last_used_at else '从未使用'

            # 根据状态设置颜色
            if token.is_valid:
                line = f'{token.id:<6} {token.name:<20} {status:<10} {created:<20} {last_used:<20}'
                self.stdout.write(self.style.SUCCESS(line))
            else:
                line = f'{token.id:<6} {token.name:<20} {status:<10} {created:<20} {last_used:<20}'
                self.stdout.write(self.style.ERROR(line))

        self.stdout.write('=' * 80 + '\n')

    def _revoke_token(self, options):
        """撤销 Token"""
        token_id = options['token_id']

        try:
            token = APIToken.objects.get(id=token_id)
        except APIToken.DoesNotExist:
            raise CommandError(f'Token ID {token_id} 不存在')

        if not token.is_active:
            self.stdout.write(self.style.WARNING(f'Token "{token.name}" 已经被禁用'))
            return

        token.is_active = False
        token.save(update_fields=['is_active'])

        self.stdout.write(self.style.SUCCESS(f'Token "{token.name}" (ID: {token_id}) 已被撤销'))

    def _token_info(self, options):
        """查看 Token 详情"""
        token_id = options['token_id']

        try:
            token = APIToken.objects.get(id=token_id)
        except APIToken.DoesNotExist:
            raise CommandError(f'Token ID {token_id} 不存在')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'Token 详情 (ID: {token.id})')
        self.stdout.write('=' * 50)
        self.stdout.write(f'名称:       {token.name}')
        self.stdout.write(f'状态:       {self._get_status_display(token)}')
        self.stdout.write(f'创建时间:   {token.created_at.strftime("%Y-%m-%d %H:%M:%S")}')

        if token.expires_at:
            self.stdout.write(f'过期时间:   {token.expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write('过期时间:   永不过期')

        if token.last_used_at:
            self.stdout.write(f'最后使用:   {token.last_used_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write('最后使用:   从未使用')

        if token.description:
            self.stdout.write(f'描述:       {token.description}')

        self.stdout.write('=' * 50 + '\n')

    def _get_status_display(self, token) -> str:
        """获取状态显示文本"""
        if not token.is_active:
            return '已禁用'
        if token.is_expired:
            return '已过期'
        return '有效'
