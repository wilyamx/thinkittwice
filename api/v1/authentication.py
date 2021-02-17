from django.conf import settings
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import authentication

from PoleLuxe.models import User
from api.v1.helpers import push_notification
from api.v1.serializers import LogoutSerializer
from api.v1.constants import PlatformType


class LegacyTokenAuthentication(authentication.BaseAuthentication):  # pragma: no cover
    """
    Legacy token base authentication.
    """

    def authenticate(self, request):
        """
        Authenticate using token provided in the request header.

        :return User: The first user found having the header token.
        """
        token_param = request.META.get('HTTP_X_AUTH_TOKEN')
        users = User.objects.filter(token=token_param).exclude(
            token__isnull=True)

        user = users.first()

        if user is not None:
            request.authenticated_user = user

        return user

    def authenticate_by_id(self, request):
        """
        Authenticate by User ID instead by token.

        Try to check if the id provided belongs to a logged user.

        :return User: The first user found having the header token.
        """
        user_id = request.META.get('HTTP_X_AUTH_TOKEN')
        try:
            users = User.objects.filter(pk=user_id)
        except ValueError:
            return None
        if not users.exists() or not users.first().is_login:
            return None
        return users.first()

    def clear_credentials(self, user):
        """
        Clear user uuid, token and login status. Also delete device from push
        notification table.

        :param User user: User model instance.
        """
        user.uuid = None
        user.token = None
        user.is_login = False
        user.save()
        push_notification.delete_devices(user.id)

    def logout(self, request):
        """
        Logout a user.
        """
        user = self.authenticate(request)
        if user is None:
            user = self.authenticate_by_id(request)
            if user is None:
                return False

        self.clear_credentials(user)

        return True


class WithMultipleLogoutAuthentication(LegacyTokenAuthentication):
    def logout_multiple(self, tokens):
        """
        Logout all users found having from the list of tokens.

        :param list tokens: List of tokens.

        :return tuple(bool, dict or None): On success returns bool(True) and
            dict(result) having token as the key and bool as the value.
            On error returns bool(False) and None
        """
        status = {token: False for token in tokens}
        for token in tokens:
            try:
                user = User.objects.get(token=token.strip())
                self.clear_credentials(user)

                status[token] = True
            except User.DoesNotExist:
                pass

        return status

    def logout(self, request):
        """
        Logout a user of list of users(from list of tokens).
        """
        user = self.authenticate(request)
        if user is None:
            user = self.authenticate_by_id(request)
            if user is None:
                return False, None

        multiple = settings.ENABLE_MULTIPLE_LOGOUT and request.method == 'POST'

        if multiple:
            tokens = request.data.get('tokens')
            if tokens is None:
                result = {}
            else:
                # Check and try multiple users' logout.
                serializer = LogoutSerializer(data=dict(request.data))
                if not serializer.is_valid():
                    return False, serializer.errors

                result = self.logout_multiple(
                    serializer.data.get('tokens', [])
                )

            self.clear_credentials(user)
            push_notification.delete_other_devices(user.id, {
                PlatformType.IOS: 'APNS',
                PlatformType.ANDROID: 'GCM',
            })
            return True, result

        self.clear_credentials(user)
        return True, None


class CustomTokenAuthentication(LegacyTokenAuthentication):
    def authenticate(self, request):
        user = super(CustomTokenAuthentication, self).authenticate(request)
        if user is None:
            return None

        request.authenticated_user = user

        return user, None

    def authenticate_header(self, request):
        return "Token"


class CustomOAuth2Authentication(OAuth2Authentication):
    def authenticate(self, request):
        user = super(CustomOAuth2Authentication, self).authenticate(request)
        if user is None:
            return None

        # user is tuple when successful
        app_user = User.objects.filter(
            django_user=user[0]
        ).first()

        request.authenticated_user = app_user
        return app_user, user[1]

    def authenticate_header(self, request):
        return "Bearer"


class WebhookTokenAuthentication(LegacyTokenAuthentication):
    """
    Requires any User token for the path params
    e.g. api/v1/memsource-events/c1b2dbe9e8d24c08a021c6193c52eb99/
    """
    def authenticate(self, request):
        kwargs = request.parser_context.get('kwargs', None)
        token = kwargs.get('token', None)

        users = User.objects.filter(token=token).exclude(
            token__isnull=True
        )
        if users.count() == 0:
            return None, None

        user = users.first()
        request.authenticated_user = user

        return user, None


legacy = LegacyTokenAuthentication()
multi_logout = WithMultipleLogoutAuthentication()


def authenticate(request):
    return legacy.authenticate(request)
