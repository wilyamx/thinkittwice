from PoleLuxe.models import Feed

from api.v1.views.base import ReadOnlyBaseModelViewSet
from api.v2.filters.feed import FeedFilterBackend
from api.v2.serializers.feed import (
    FeedSerializer
)
from api.v1.mixins.views import ReadReplica
from django.db.models import Count


class FeedViewSet(ReadOnlyBaseModelViewSet, ReadReplica):
    """
    Manage feeds
    use readonly database
    """
    queryset = Feed.objects.order_by('-id')
    serializer_class = FeedSerializer

    filter_backends = (
        FeedFilterBackend,
    )

    def get_queryset(self):
        return self.queryset.using(self.get_random_replica_db())

    def get_serializer_context(self):
        context = super(FeedViewSet, self).get_serializer_context()
        context.update({
            'user_id': self.request.authenticated_user.id,
            'user_group_id': self.request.query_params['user_group_id']
        })

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
