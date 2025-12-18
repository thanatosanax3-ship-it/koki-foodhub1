from django.core.management.base import BaseCommand
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
import traceback


class Command(BaseCommand):
    help = 'Run the forecast_view under DEBUG=False-like conditions and print any exceptions.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=None, help='Username to use for the request (must be in Admin group if provided)')

    def handle(self, *args, **options):
        # Temporarily ensure DEBUG is False for this run
        prev_debug = settings.DEBUG
        settings.DEBUG = False
        rf = RequestFactory()
        try:
            from core.views import forecast_view
        except Exception as e:
            self.stdout.write(self.style.ERROR('Unable to import forecast_view: %s' % e))
            settings.DEBUG = prev_debug
            return

        username = options.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
        else:
            # Try to pick an admin user
            user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()

        req = rf.get('/forecast/?debug=1')
        # attach a user (or an AnonymousUser) so the group_required decorator behaves similarly
        if user:
            req.user = user
        else:
            from django.contrib.auth.models import AnonymousUser
            req.user = AnonymousUser()

        try:
            resp = forecast_view(req)
            self.stdout.write(self.style.SUCCESS('forecast_view returned status: %s' % getattr(resp, 'status_code', 'unknown')))
        except Exception:
            tb = traceback.format_exc()
            self.stdout.write(self.style.ERROR('Exception calling forecast_view:'))
            self.stdout.write(tb)
        finally:
            settings.DEBUG = prev_debug
