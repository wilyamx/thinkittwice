from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.schemas import ManualSchema

from PoleLuxe.models import Feed

from ..views.base import ReadOnlyBaseModelViewSet
from ..serializers.feed import (
    DetailFeedSerializer,
    FeedSerializer
)
from ..filters.feed import FeedFilterBackend, LEGACY_SCHEMA_FIELDS
from ..decorators import exceptions_catched, active_user_required
from api import permissions


class FeedViewSet(ReadOnlyBaseModelViewSet):
    """
    Manage feeds
    """
    queryset = Feed.objects.order_by('-id')
    serializer_class = FeedSerializer

    filter_backends = (
        FeedFilterBackend,
    )

    def get_permissions(self):
        if self.action != 'legacy':
            self.permission_classes = (permissions.IsCustomAuthenticated,)
        return super(FeedViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == 'legacy':
            return DetailFeedSerializer
        return FeedSerializer

    def get_serializer_context(self):
        context = super(FeedViewSet, self).get_serializer_context()
        context.update({
            'user_id': self.request.authenticated_user.id,
            'user_group_id': self.request.query_params['user_group_id']
        })

        if self.action == 'legacy':
            context.update({
                'language_code': self.request.authenticated_user.language_id,
            })
        else:
            language_code = self.request.authenticated_user.language_id
            if 'language_code' in self.request.query_params:
                language_code = self.request.query_params['language_code']
            context.update({
                'language_code': language_code
            })

            if 'include' in self.request.query_params:
                context.update({
                    'include': self.request.query_params['include']
                })
        return context

    @active_user_required
    @exceptions_catched
    @list_route(
        methods=['get'],
        schema=ManualSchema(
            fields=LEGACY_SCHEMA_FIELDS,
            description='Legacy feeds list'
        ),
    )
    def legacy(self, request, *args, **kwargs):
        """
        Legacy feeds list
        """
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs[:20], many=True)
        return Response({'success': True, 'feeds': serializer.data})
