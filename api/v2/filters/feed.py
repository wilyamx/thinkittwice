from rest_framework import filters
from rest_framework import exceptions

from django.db.models import Q, Count, Case, When, IntegerField
from django.db.models.functions import Coalesce

from PoleLuxe.constants import CategoryType
from PoleLuxe.models import (
    Feed,
    UserGroup
)

from api.v1.filters.feed import (
    LEGACY_SCHEMA_FIELDS,
    SCHEMA_FIELDS,
)


class FeedFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user_group_id = request.query_params.get('user_group_id', None)
        feed_id = request.query_params.get('feed_id', None)
        oldest_feed_id = request.query_params.get('oldest_feed_id', 0)
        pinned_tag_id = request.query_params.get('pinned_tag_id', None)

        category = request.query_params.get('category')

        try:
            user_group = UserGroup.objects.get(
                pk=user_group_id
            )
        except UserGroup.DoesNotExist:
            raise exceptions.NotFound(
                detail='Usergroup {}'.format(user_group_id)
            )

        # if pinned tag is detected, use a different filtering
        if pinned_tag_id is not None:
            return self.filter_by_pinned_tag(pinned_tag_id, request.authenticated_user.id, user_group.id)

        if feed_id:
            queryset = queryset.filter(
                id=feed_id
            ).exclude_expired_contents(user_group.timezone)
            return queryset

        if request and not hasattr(request, 'authenticated_user'):
            raise exceptions.NotAuthenticated()

        # We should be doing queryset chain but `get_general`
        # is defined inside the manager.
        # Supported feed types
        #     COMPLETE_DAILY_CHALLENGE_TYPE = 1
        #     TIPS_OF_THE_DAY_TYPE = 2
        #     NEW_CONTENT_AVAILABLE_TYPE = 5
        #     NEW_POSTED_MEDIA_TYPE = 8
        queryset = Feed.objects.get_general(
            request.authenticated_user.id,
            user_group.id,
            user_group.timezone,
            excluded_types=[
                Feed.COLLEAGUE_LEVEL_UP_TYPE,
                Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                Feed.UPDATED_RANKING_AVAILABLE_TYPE,
                Feed.NEW_POSTED_VIDEO_TYPE,
                Feed.EVALUATION_REMINDER_TYPE
            ],
        ).filter_evaluation_reminders(
            request.authenticated_user
        )
        if int(oldest_feed_id) != 0:
            queryset = queryset.filter(id__lt=oldest_feed_id)

        # hide pinned feed except when category is unread
        if category != CategoryType.UNREAD:
            queryset = queryset.exclude(
                # exclude pinned in normal feed
                is_pinned=True
            )

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
                    type=Feed.NEW_POSTED_MEDIA_TYPE
                )

        # excluding the content without expiry date
        return queryset.exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
                (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).distinct()

    def filter_by_pinned_tag(self, tag_id, user_id, group_id):
        queryset = Feed.objects.filter(pinned_tags__id=tag_id).filter(
            Q(user_group_id__id=group_id) | Q(user_id__id=user_id)
        )
        queryset = queryset.annotate(
            readfeed_count=Count(
                Case(
                    When(readfeed__user__id=user_id, then=1),
                    output_field=IntegerField(),
                )
            ),
            publish_date=Coalesce(
                'knowledge_id__publish_date',
                'luxury_culture_id__publish_date',
            )
        )
        queryset = queryset.order_by('readfeed_count', 'publish_date', 'id')
        return queryset

    def get_schema_fields(self, view):
        if view.action == 'legacy':
            return LEGACY_SCHEMA_FIELDS
        return SCHEMA_FIELDS
