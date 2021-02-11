import coreapi
import coreschema

from django.db.models import Q

from rest_framework import filters
from rest_framework import exceptions

from PoleLuxe.constants import CategoryType
from PoleLuxe.models import (
    Feed,
    Media,
    UserGroup,
)
from api.v1.views.base import (
    LEGACY_SCHEMA_AUTH_FIELD,
    INCLUDE_SCHEMA_FIELD
)


LEGACY_SCHEMA_FIELDS = [
    LEGACY_SCHEMA_AUTH_FIELD,
    coreapi.Field(
        name='feed_id',
        location='query',
        required=False,
        schema=coreschema.Integer(),
        description='Feed ID.'
    ),
    coreapi.Field(
        name='user_group_id',
        location='query',
        required=True,
        type='string',
        schema=coreschema.Integer(),
        description='User group ID.'
    ),
    coreapi.Field(
        name='oldest_feed_id',
        location='query',
        required=False,
        schema=coreschema.Integer(),
        description='''Oldest feed ID.
        For pagination use. The parameter should be the last object id
        returned in the last of this API (last page). If it is the
        first call of API (first page) it should be '0'.
        '''
    )
]

SCHEMA_FIELDS = [
    LEGACY_SCHEMA_AUTH_FIELD,
    coreapi.Field(
        name='feed_id',
        location='query',
        required=False,
        schema=coreschema.Integer(),
        description='Feed ID.'
    ),
    coreapi.Field(
        name='user_group_id',
        location='query',
        required=True,
        schema=coreschema.Integer(),
        description='User group ID.'
    ),
    coreapi.Field(
        name='oldest_feed_id',
        location='query',
        required=False,
        schema=coreschema.Integer(),
        description='''Oldest feed ID.
        For pagination use. The parameter should be the last object id
        returned in the last of this API (last page). If it is the
        first call of API (first page) it should be '0'.
        '''
    ),
    coreapi.Field(
        name="language_code",
        required=False,
        location="query",
        schema=coreschema.String(),
        description="Language code (EN, CN, TC, FR, JP, KR)",
    ),
    INCLUDE_SCHEMA_FIELD,
    coreapi.Field(
        name="category",
        required=False,
        location="query",
        schema=coreschema.String(),
        description="Filter by category (unread, brand, market, community)",
    ),
    coreapi.Field(
        name='pinned_tag_id',
        location='query',
        required=False,
        schema=coreschema.Integer(),
        description='''Only show pinned feed with tag
        '''
    )
]


class FeedFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user_group_id = request.query_params.get('user_group_id', None)
        feed_id = request.query_params.get('feed_id', None)
        oldest_feed_id = request.query_params.get('oldest_feed_id', 0)

        category = request.query_params.get('category')

        try:
            user_group = UserGroup.objects.get(
                pk=user_group_id
            )
        except UserGroup.DoesNotExist:
            raise exceptions.NotFound(
                detail='Usergroup {}'.format(user_group_id)
            )

        if feed_id:
            queryset = queryset.filter(
                id=feed_id
            ).exclude_expired_contents(user_group.timezone)
            return queryset

        if request and not hasattr(request, 'authenticated_user'):
            raise exceptions.NotAuthenticated()

        # We should be doing queryset chain but `get_general`
        # is defined inside the manager.
        queryset = Feed.objects.get_general(
            request.authenticated_user.id,
            user_group.id,
            user_group.timezone,
            excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
        ).filter_evaluation_reminders(
            request.authenticated_user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).exclude(
            # exclude pinned in normal feed
            is_pinned=True
        )

        if int(oldest_feed_id) != 0:
            queryset = queryset.filter(id__lt=oldest_feed_id)

        if category:
            if category == CategoryType.UNREAD:
                queryset = queryset.filter(
                    type__in=[
                        Feed.NEW_CONTENT_AVAILABLE_TYPE,
                        Feed.NEW_POSTED_MEDIA_TYPE,
                        Feed.TIPS_OF_THE_DAY_TYPE
                    ]
                ).exclude_read_contents(request.authenticated_user)

            elif category == CategoryType.BRAND:
                queryset = queryset.filter(
                    type=Feed.NEW_CONTENT_AVAILABLE_TYPE
                ).filter_contents_with_tags(['brand'])

            elif category == CategoryType.MARKET:
                queryset = queryset.filter(
                    type=Feed.NEW_CONTENT_AVAILABLE_TYPE
                ).filter_contents_with_tags(['market'])

            elif category == CategoryType.COMMUNITY:
                queryset = queryset.filter(
                    type__in=[
                        Feed.NEW_POSTED_MEDIA_TYPE
                    ]
                )

        return queryset

    def get_schema_fields(self, view):
        if view.action == 'legacy':
            return LEGACY_SCHEMA_FIELDS
        return SCHEMA_FIELDS
