import itertools

from django.conf import settings
from django.utils.functional import SimpleLazyObject

from rest_framework.permissions import (
    BasePermission,
    DjangoModelPermissions,
    IsAdminUser,
    SAFE_METHODS,
    IsAuthenticated,
)

from PoleLuxe.models.company import CompanyOwner

from api.v1.helpers.company_manager import default_company_manager_helper
from api.v1.mixins.user_type import WithHasPermissionByUserType


def is_swagger_docs(request):  # pragma: no cover
    # for swagger user, calling from API docs route
    if (type(request.user) is SimpleLazyObject and
        request._request.path == u'/{}/'.format(
            settings.SWAGGER_SCHEMA_ROUTE
    )):
        return True
    return False


class CustomPermissions(BasePermission):  # pragma: no cover
    def has_permission(self, request, view):
        """
        Because we're using custom user for authentication we need to replace
        the use in the request to apply permission checking against with.
        """
        user = request.user

        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        request.user = user.django_user

        ret = super(CustomPermissions, self).has_permission(
            request,
            view
        )

        request.user = user

        return ret


class CustomIsAdminUser(CustomPermissions, IsAdminUser):
    pass


class IsCustomAuthenticated(IsAuthenticated):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        return (request.user
                and hasattr(request.user, 'django_user')
                and request.user.django_user.is_authenticated)


class CustomDjangoModelPermissions(CustomPermissions, DjangoModelPermissions):
    def __init__(self):
        self.perms_map = {
            'GET': [],
            'OPTIONS': [],
            'HEAD': [],
            'POST': ['%(app_label)s.add_%(model_name)s'],
            'PUT': ['%(app_label)s.change_%(model_name)s'],
            'PATCH': ['%(app_label)s.change_%(model_name)s'],
            'DELETE': ['%(app_label)s.delete_%(model_name)s'],
        }

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        django_user = request.user.django_user

        if django_user.is_staff:
            self.perms_map['GET'] = itertools.chain(
                self.perms_map['GET'],
                [
                    '%(app_label)s.add_%(model_name)s',
                    '%(app_label)s.change_%(model_name)s'
                ]
            )

        return super(CustomDjangoModelPermissions, self).has_permission(
            request, view)


class ZonePermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        can_view_analytics = request.user.django_user.has_perm(
            'PoleLuxe.view_analytics'
        )
        if request.method == 'GET' and can_view_analytics:
            company = request.query_params.get('company')
            if company and company == str(request.user.company_id.id):
                return True
        return super(ZonePermissions, self).has_permission(request, view)


class PinnedTagPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class TagPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class CountryPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class CompanyPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class DepartmentPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class PositionPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class TranslationPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class BatchUserCreatePermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class UserGroupMembersPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class UserRegionPermission(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class CompanyOwnerPermissions(CustomDjangoModelPermissions):

    # bypass logic for is_staff in company owners
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        return super(CustomDjangoModelPermissions, self).has_permission(
            request, view)


class EvaluationPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    def __init__(self):
        self.perms_map['GET'] = [
            '%(app_label)s.add_evaluation'
        ]


class EvaluateeOrEvaluatePermissions(EvaluationPermissions):
    def has_permission(self, request, view):
        if view.action == 'list':
            self.perms_map['GET'] = []
        elif view.action == 'retrieve':
            try:  # pragma: no cover
                evaluation = view.get_object()
                if evaluation.user == request.user:
                    self.perms_map['GET'] = []
            except AssertionError:
                pass  # TODO bad idea to silently ignore errors

        return super(EvaluateeOrEvaluatePermissions, self).has_permission(
            request, view)


class CustomIsAdminOrEvaluationPermissions(CustomIsAdminUser):
    def has_permission(self, request, view):
        ok = super(CustomIsAdminOrEvaluationPermissions, self).has_permission(
            request,
            view
        )

        return ok or EvaluationPermissions().has_permission(request, view)


class MediaPermissions(CustomDjangoModelPermissions):
    def __init__(self):
        self.perms_map = {
            'GET': [],
            'OPTIONS': [],
            'HEAD': [],
            'POST': ['%(app_label)s.add_%(model_name)s'],
            'PUT': ['%(app_label)s.change_%(model_name)s'],
            'PATCH': ['%(app_label)s.change_%(model_name)s'],
            'DELETE': ['%(app_label)s.delete_%(model_name)s'],
        }

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        # This is mainly for backward compatibilty.
        # We exempt regular users here because the logic is handled in the
        # ViewSet already.

        if view.action in ['like', 'unlike']:
            return True

        if request.method in ['GET', 'POST']:
            if not (request.user.django_user.is_superuser or
                    request.user.django_user.is_staff):
                return True
        elif request.method in ['PUT', 'PATCH']:
            self.perms_map[request.method] = []
            return True

        return super(MediaPermissions, self).has_permission(request, view)

    def is_like_unlike(self, view):
        return view.action in ['like', 'unlike']

    def owns(self, request, obj):
        return request.user.pk == obj.user.pk

    def has_object_permission(self, request, view, obj):
        if self.is_like_unlike(view):
            return True
        if self.owns(request, obj):
            return True
        return CustomDjangoModelPermissions().has_permission(
            request,
            view)


class MediaResourcePermissions(MediaPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        # This is mainly for backward compatibilty.
        # We exempt regular users here because the logic is handled in the
        # ViewSet already.

        if not (request.user.django_user.is_superuser or
                request.user.django_user.is_staff):
            return True

        return super(MediaPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.pk == obj.media.user.pk:
            return True
        return CustomDjangoModelPermissions().has_permission(
            request,
            view)


class MediaResourceWriterPermissions(MediaResourcePermissions):
    """
    User is a media writer (add_media, add_mediaresource)
    """
    def _has_media_writer_permissions(self, django_user):
        return (django_user.has_perm('PoleLuxe.add_media') and
                django_user.has_perm('PoleLuxe.add_mediaresource'))

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        if request.method in ['POST']:
            return self._has_media_writer_permissions(request.user.django_user)

        return super(MediaResourceWriterPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super(MediaResourceWriterPermissions, self).has_object_permission(
            request, view, obj
        )


class AppPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    def has_permission(self, request, view):
        # Anonymous users are allowed to retrieve app information.
        if request.method == 'GET':
            return True

        return super(AppPermissions, self).has_permission(request, view)


class RatingPermissions(BasePermission):
    def has_permission(self, request, view):
        # Anybody can rate.
        return True

    def has_object_permission(self, request, view, obj):
        # Only owners and privileged users can change and delete
        if request.user.pk == obj.user.pk:
            return True
        return CustomDjangoModelPermissions().has_permission(
            request,
            view)


class ProductGroupPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        if request.method in SAFE_METHODS:
            ok = self.is_content_editor(request)
            if ok:
                return True

        return super(
            ProductGroupPermissions,
            self).has_permission(request, view)

    def is_content_editor(self, request):
        """
        Verify if user is a content editor or not.
        """

        # Content editor(s) should have `add` and `change` permissions in any
        # the following contents.
        content_names = [
            "knowledge",
            "knowledgecard",
            "knowledgequiz",
            "dailychallenge",
            "dailychallengequiz",
            "luxuryculture",
            "tipsoftheday",
            "media",
            "mediaresource",
            "cheerupmessage",
        ]
        for v in content_names:
            ok = request.user.django_user.has_perms([
                'PoleLuxe.add_' + v,
                'PoleLuxe.change_' + v,
            ])
            if ok:
                return True

        return False


class UserKnowledgeResultPermissions(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        if request.method in ['GET', 'POST']:
            if not (request.user.django_user.is_superuser or
                    request.user.django_user.is_staff):
                return True
        elif request.method in ['PUT', 'PATCH']:
            return False

        return IsCustomAuthenticated().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Only owners and privileged users can change and delete
        if request.user.pk == obj.user.pk:
            return True
        return CustomDjangoModelPermissions().has_permission(
            request,
            view)


class UserLuxuryCultureResultPermissions(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        if request.method in ['GET', 'POST']:
            if not (request.user.django_user.is_superuser or
                    request.user.django_user.is_staff):
                return True
        elif request.method in ['PUT', 'PATCH']:
            return False

        return IsCustomAuthenticated().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Only owners and privileged users can change and delete
        if request.user.pk == obj.user.pk:
            return True
        return CustomDjangoModelPermissions().has_permission(
            request,
            view)


# TODO deprecate this in favor of ManagerPermission
class CompanyManagerPermissions(CustomDjangoModelPermissions):

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        if request.method in ['GET']:
            if CompanyOwner.objects.filter(
                owner=request.user
            ).exists():
                return True

        elif request.method in ['POST', 'PATCH', 'PUT', 'DELETE']:
            return CompanyOwner.objects.filter(
                owner=request.user
            ).exists()

        return super(CompanyManagerPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super(CompanyManagerPermissions, self).has_object_permission(
            request, view, object
        )


class AccessLevelPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    pass


class CompanyManagerDjangoModelPermissions(WithHasPermissionByUserType, CustomDjangoModelPermissions):
    def get_user_group_ids(self, request):
        """
        Manageable usergroups
        """
        return default_company_manager_helper.get_usergroups(
            user_id=request.user
        ).values_list('id', flat=True)

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        if request.method in ['GET']:
            if view.action == 'retrieve':
                return True

        return super(CompanyManagerDjangoModelPermissions, self).has_permission(request, view)


class ContentWithProductGroupPermissions(CompanyManagerDjangoModelPermissions):
    """
    DailyChallenge, Knowledge, LuxuryCulture, TipsOfTheDay is using product_group.
    Media is using product_groups.
    """
    def get_product_groups(self, request):
        return request.data.get('product_group')

    def get_content_product_groups(self, content):
        return content.product_group

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        return super(ContentWithProductGroupPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self.allow_content(request, obj)

    def allow_content(self, request, obj):
        if request.user.is_company_manager():
            content_product_groups = default_company_manager_helper.get_productgroups(
                request.user
            )
            return content_product_groups.exists()
        return True


class MediaContentWithProductGroupPermissions(WithHasPermissionByUserType, MediaPermissions):
    """
    Media is using product_groups.
    DailyChallenge, Knowledge, LuxuryCulture, TipsOfTheDay is using product_group.
    """
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        return super(MediaContentWithProductGroupPermissions,
                     self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if self.is_like_unlike(view):
            return True
        if self.owns(request, obj):
            return True
        return self.has_permission(
            request,
            view)


class MediaWriterPermissions(MediaContentWithProductGroupPermissions):
    """
    User is a media writer (add_media, add_mediaresource)
    """
    def _has_media_writer_permissions(self, django_user):
        return (django_user.has_perm('PoleLuxe.add_media') and
                django_user.has_perm('PoleLuxe.add_mediaresource'))

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        if request.method in ['POST'] and not self.is_like_unlike(view):
            return self._has_media_writer_permissions(request.user.django_user)

        return super(MediaWriterPermissions, self).has_permission(request, view)

    def owns(self, request, obj):
        """
        Ignore object ownership when checking permissions.
        """
        return False

    def has_object_permission(self, request, view, obj):
        return super(MediaWriterPermissions, self).has_object_permission(
            request, view, obj
        )


class CompanyAnalyticsPermissions(CustomPermissions):
    """
    Allows access only to users who allowed to view company analytics.
    """

    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        return (request.user
                and hasattr(request.user, 'django_user')
                and request.user.django_user.has_perm(
                    'PoleLuxe.view_analytics'
                ))


class AnalyticsPermissions(CustomPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        can_view_analytics = request.user.django_user.has_perm(
            'PoleLuxe.view_analytics'
        )
        if request.method == 'GET' and can_view_analytics:
            company = request.query_params.get('company')
            if company and company == str(request.user.company_id.id):
                return True
            else:
                return request.user.django_user.is_staff

        return super(AnalyticsPermissions, self).has_permission(request, view)


class AnalyticsOrEvaluationPermissions(CustomIsAdminOrEvaluationPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        can_view_analytics = request.user.django_user.has_perm(
            'PoleLuxe.view_analytics'
        )
        if request.method == 'GET' and can_view_analytics:
            company = request.query_params.get('company')
            if company and company == str(request.user.company_id.id):
                return True
            else:
                return request.user.django_user.is_staff

        return super(AnalyticsOrEvaluationPermissions, self).has_permission(request, view)


class OwnerUserPermissions(WithHasPermissionByUserType, AnalyticsOrEvaluationPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):
            return is_swagger_docs(request)

        is_self_request = (
            'pk' in view.kwargs
            and int(view.kwargs['pk']) in [int(request.user.pk), 0]
        )

        if request.method == 'GET' and is_self_request:
            return True

        return super(OwnerUserPermissions, self).has_permission(request, view)


class UsersMetadataPermissions(OwnerUserPermissions):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        if request.method == 'GET' and view.action == 'metadata':
            return True

        return super(UsersMetadataPermissions, self).has_permission(request, view)


class QuizAnswerPermissions(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'django_user'):  # pragma: no cover
            return is_swagger_docs(request)

        # anyone can get and submit answer(s)
        if request.method in ['GET', 'POST']:
            return True

        # submitted answer is final and cannot be change or delete
        elif request.method in ['PUT', 'PATCH', 'DELETE']:
            return False

        return CustomDjangoModelPermissions().has_permission(request, view)
