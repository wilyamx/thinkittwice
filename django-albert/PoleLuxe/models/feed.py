import datetime

from django.db import models
from django.conf import settings

from .dailychallenge import (
    DailyChallengeResult,
)
from django.db.models import Q

from PoleLuxe.helpers.date import date_helper
from PoleLuxe.datetimeutil import TimezonedDateTime
from PoleLuxe.constants import FeedReferenceModelType


class FeedQuerySet(models.query.QuerySet):
    def user_group(self, user_group_id):
        return self.filter(Q(user_group_id=user_group_id)
                           | Q(user_group_id__isnull=True))

    def exclude_other_user_daily_challenge(self, user_id):
        return self.exclude(Q(type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE),
                            ~Q(user_id=user_id))

    def exclude_invisible_tips_of_the_day(self, user_group_id):
        return self.exclude(
            Q(type=Feed.TIPS_OF_THE_DAY_TYPE),
            Q(tips_of_the_day_id__product_group__isnull=False)
            | Q(tips_of_the_day_id__white_list_user_group__isnull=False),
            ~Q(tips_of_the_day_id__product_group__user_group=user_group_id),
            ~Q(tips_of_the_day_id__white_list_user_group=user_group_id)
        ).exclude(tips_of_the_day_id__black_list_user_group=user_group_id)

    def exclude_expired_contents(self, timezone):
        """
        Exclude expired tips, tips' knowledges and tips' luxury cultures.

        :param int timezone

        :return QuerySet
        """
        date = date_helper.get_current_datetime()

        return self.exclude_expired_tips_of_the_day(
            date,
            timezone
        ).exclude_expired_tips_knowledge(
            date,
            timezone
        ).exclude_expired_tips_luxury_culture(
            date,
            timezone
        ).exclude_expired_knowledge(
            date,
            timezone
        ).exclude_expired_luxury_culture(
            date,
            timezone
        ).exclude_expired_daily_challenge(
            date,
            timezone
        ).exclude_expired_media()

    def exclude_expired_tips_of_the_day(self, utc_datetime, timezone):
        """
        Exclude expired tips from the Feed.

        :param datetime utc_datetime
        :param integer timezone

        :return QuerySet
        """
        date = TimezonedDateTime(utc_datetime, timezone).to_local().date()

        return self.exclude(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id__expiry_date__lt=date
        )

    def exclude_expired_daily_challenge(self, utc_datetime, timezone):
        """
        Exclude expired daily challenge results

        :param datetime utc_datetime
        :param integer timezone

        :return QuerySet
        """
        date = TimezonedDateTime(utc_datetime, timezone).to_local().date()
        return self.exclude(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id__daily_challenge_id__publish_date__lt=date
        )

    def exclude_expired_knowledge(self, current_date, timezone):
        net_date = TimezonedDateTime(current_date, timezone).to_local().date()
        return self.exclude(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id__expiry_date__lt=net_date,
        )

    def exclude_expired_luxury_culture(self, current_date, timezone):
        net_date = TimezonedDateTime(current_date, timezone).to_local().date()
        return self.exclude(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id__expiry_date__lt=net_date,
        )

    def exclude_unpublished_knowledge(self, timezone):
        return self.exclude(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id__knowledge_id__isnull=False,
            tips_of_the_day_id__knowledge_id__publish_date__gt=(
                datetime.datetime.now() + datetime.timedelta(hours=timezone)
            ).date()
        )

    def exclude_expired_tips_knowledge(self, utc_datetime, timezone):
        """
        Exclude expired tips' knowledges from the Feed.

        :param datetime utc_datetime
        :param integer timezone

        :return QuerySet
        """
        date = TimezonedDateTime(utc_datetime, timezone).to_local().date()

        return self.exclude(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id__knowledge_id__expiry_date__lt=date
        )

    def exclude_expired_tips_luxury_culture(self, utc_datetime, timezone):
        """
        Exclude expired tips' luxury cultures from the Feed.

        :param datetime utc_datetime
        :param timezone

        :return QuerySet
        """
        date = TimezonedDateTime(utc_datetime, timezone).to_local().date()

        return self.exclude(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id__luxury_culture_id__expiry_date__lt=date
        )

    def exclude_invisible_knowledge(self, user_group_id):
        return self.exclude(
            Q(type=Feed.TIPS_OF_THE_DAY_TYPE),
            Q(tips_of_the_day_id__knowledge_id__isnull=False),
            Q(tips_of_the_day_id__knowledge_id__product_group__isnull=False)
            | Q(tips_of_the_day_id__knowledge_id__white_list_user_group__isnull=False),
            ~Q(tips_of_the_day_id__knowledge_id__product_group__user_group=user_group_id),
            ~Q(tips_of_the_day_id__knowledge_id__white_list_user_group=user_group_id)
        ).exclude(tips_of_the_day_id__knowledge_id__black_list_user_group=user_group_id)

    def exclude_unpublished_luxury_cultures(self, timezone):
        return self.exclude(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id__luxury_culture_id__isnull=False,
            tips_of_the_day_id__luxury_culture_id__publish_date__gt=(
                datetime.datetime.now() + datetime.timedelta(hours=timezone)
            ).date()
        )

    def exclude_invisible_luxury_culture(self, user_group_id):
        return self.exclude(
            Q(type=Feed.TIPS_OF_THE_DAY_TYPE),
            Q(tips_of_the_day_id__luxury_culture_id__isnull=False),
            Q(tips_of_the_day_id__luxury_culture_id__product_group__isnull=False)
            | Q(tips_of_the_day_id__luxury_culture_id__white_list_user_group__isnull=False),
            ~Q(tips_of_the_day_id__luxury_culture_id__product_group__user_group=user_group_id),
            ~Q(tips_of_the_day_id__luxury_culture_id__white_list_user_group=user_group_id)
        ).exclude(tips_of_the_day_id__luxury_culture_id__black_list_user_group=user_group_id)

    def exclude_incomplete_media(self):
        """
        Exclude media that don't have resources in the feed.
        """
        from PoleLuxe.models.media import Media

        return self.filter(
            ~Q(type=Feed.NEW_POSTED_MEDIA_TYPE)
            | Q(model_id__in=Media.objects.get_completed())
            | Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        )

    def exclude_expired_media(self):
        """
        Exclude the expired media.
        We could have just added a new `media` field to the Feed model,
        but it would not be compatible with the existing data.
        """
        from PoleLuxe.models.media import Media

        active_media = Media.objects.get_active().values_list(
            'id', flat=True
        )

        return self.filter(
            ~Q(type=Feed.NEW_POSTED_MEDIA_TYPE)
            | Q(model_id__in=active_media)
        )

    def exclude_types(self, types):
        return self.exclude(type__in=types)

    def ordered(self):
        return self.order_by('-created_at', '-id')

    def get_knowledges(self):
        return self.filter(
            knowledge_id__isnull=False,
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
        )

    def get_luxury_cultures(self):
        return self.filter(
            luxury_culture_id__isnull=False,
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
        )

    def has_knowledges(self, **filter_options):
        return self.get_knowledges().filter(**filter_options).count() > 0

    def has_luxury_cultures(self, **filter_options):
        return self.get_luxury_cultures().filter(**filter_options).count() > 0

    def has_new_knowledges(self, server_time):
        return self.has_knowledges(
            knowledge_id__publish_date__day=server_time.day,
        )

    def has_new_luxury_cultures(self, server_time):
        return self.has_luxury_cultures(
            luxury_culture_id__publish_date__day=server_time.day,
        )

    def filter_evaluation_reminders(
        self,
        user,
        permission='PoleLuxe.add_evaluation'
    ):
        """
        Exclude evaluation reminders to users who have no permissions to add
        evaluation.

        :param User user: User instance
        :param string permission

        :return QuerySet
        """
        # By default, remove all the reminders,
        # assuming the user has no permission.
        black_list_options = {
            'type': Feed.EVALUATION_REMINDER_TYPE
        }

        # If the user has permission, remove only the expired reminders.
        if user.django_user and user.django_user.has_perm(permission):
            black_list_options['created_at__lte'] = (
                datetime.datetime.now() -
                datetime.timedelta(days=settings.EVALUATION_REMINDER_DAYS_GAP)
            )

        return self.exclude(**black_list_options)

    def filter_contents_with_tags(self, tags):
        lower_case_tags = list(map(lambda i: i.lower(), tags))
        return self.filter(
            (Q(knowledge_id__isnull=False) &
             Q(knowledge_id__tags__text__in=lower_case_tags))
            | (Q(luxury_culture_id__isnull=False) &
               Q(luxury_culture_id__tags__text__in=lower_case_tags))
        )

    def exclude_read_contents(self, user):
        """
        Exclude feeds that are already read
        """
        from PoleLuxe.models.user import ReadFeed

        read_feed_ids = ReadFeed.objects.filter(
            user=user
        ).values_list('feed', flat=True)

        return self.exclude(
            id__in=list(read_feed_ids)
        )


class FeedManager(models.Manager):
    def get_queryset(self):
        return FeedQuerySet(self.model, using=self._db)

    def get_general(self,
                    user_id,
                    user_group_id,
                    timezone,
                    excluded_types=[]):
        """
        This is the query used to display user feed. All filter chaining is inside this function

        :param User user_id: User object
        :param UserGroup user_group_id: UserGroup object
        :param string timezone: User's UserGroup timezone
        :param list exclude_types: Excluded feed types

        :return QuerySet
        """
        return self.get_queryset().user_group(
            user_group_id
        ).exclude_other_user_daily_challenge(
            user_id
        ).exclude_invisible_tips_of_the_day(
            user_group_id
        ).exclude_unpublished_knowledge(
            timezone
        ).exclude_invisible_knowledge(
            user_group_id
        ).exclude_unpublished_luxury_cultures(
            timezone
        ).exclude_incomplete_media().exclude_invisible_luxury_culture(
            user_group_id
        ).exclude_types(
            excluded_types
        ).exclude_expired_contents(
            timezone
        ).ordered().distinct()

    def get_knowledges(self):
        return self.get_queryset().get_knowledges()

    def get_luxury_cultures(self):
        return self.get_queryset().get_luxury_cultures()

    def has_knowledges(self, **filter_options):
        return self.get_queryset().has_knowledges(**filter_options)

    def has_luxury_cultures(self, **filter_options):
        return self.get_queryset().has_luxury_cultures(**filter_options)

    def has_new_knowledges(self, server_time):
        return self.get_queryset().has_new_knowledges(server_time)

    def has_new_luxury_cultures(self, server_time):
        return self.get_queryset().has_new_luxury_cultures(server_time)


class Feed(models.Model):
    COMPLETE_DAILY_CHALLENGE_TYPE = 1
    TIPS_OF_THE_DAY_TYPE = 2
    COLLEAGUE_LEVEL_UP_TYPE = 3
    COLLEAGUE_COMPLETED_QUIZ_TYPE = 4
    NEW_CONTENT_AVAILABLE_TYPE = 5
    UPDATED_RANKING_AVAILABLE_TYPE = 6
    NEW_POSTED_VIDEO_TYPE = 7
    NEW_POSTED_MEDIA_TYPE = 8
    EVALUATION_REMINDER_TYPE = 9

    TYPE_CHOICES = (
        (COMPLETE_DAILY_CHALLENGE_TYPE, 'Complete Daily Challenge'),
        (TIPS_OF_THE_DAY_TYPE, 'Tips of the day'),
        (COLLEAGUE_LEVEL_UP_TYPE, 'Colleague level up'),
        (COLLEAGUE_COMPLETED_QUIZ_TYPE, 'Colleague completed quiz type'),
        (NEW_CONTENT_AVAILABLE_TYPE, 'New content available'),
        (UPDATED_RANKING_AVAILABLE_TYPE, 'Updated ranking available'),
        (NEW_POSTED_VIDEO_TYPE, 'New posted video'),
        (NEW_POSTED_MEDIA_TYPE, 'New posted media'),
        (EVALUATION_REMINDER_TYPE, 'Evaluation Reminder')
    )

    id = models.AutoField(primary_key=True)
    type = models.IntegerField(choices=TYPE_CHOICES)
    tips_of_the_day_id = models.ForeignKey(
        'PoleLuxe.TipsOfTheDay',
        null=True,
        blank=True,
        default=None
    )
    user_group_id = models.ForeignKey(
        'PoleLuxe.UserGroup',
        null=True,
        blank=True)
    user_id = models.ForeignKey(
        'PoleLuxe.User',
        null=True,
        blank=True,
        default=None)
    knowledge_id = models.ForeignKey(
        'PoleLuxe.Knowledge',
        null=True,
        blank=True,
        default=None
    )
    luxury_culture_id = models.ForeignKey(
        'PoleLuxe.LuxuryCulture',
        null=True,
        blank=True,
        default=None
    )
    daily_challenge_result_id = models.ForeignKey(
        DailyChallengeResult,
        null=True,
        blank=True,
        default=None
    )
    user_level_up_log_id = models.ForeignKey(
        "PoleLuxe.UserLevelUpLog",
        null=True,
        blank=True,
        default=None
    )
    video_id = models.ForeignKey(
        "PoleLuxe.Video", null=True, blank=True, default=None)
    video_title = models.CharField(
        null=True,
        blank=True,
        default=None,
        max_length=32
    )
    like_count = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    model = models.CharField(max_length=100, default='')
    model_id = models.PositiveIntegerField(default=0)

    # pinned content will only show if filtered by it's PinnedTag
    # This value should be modified dynamically when connecting Feed with PinnedTag
    is_pinned = models.BooleanField(default=False)
    pinned_tags = models.ManyToManyField('PoleLuxe.PinnedTag', blank=True)

    objects = FeedManager()

    def get_reference_type(self):
        """
        Source logic from DetailFeedSerializer.get_ref()
        """
        if self.type == Feed.COMPLETE_DAILY_CHALLENGE_TYPE:
            if (self.daily_challenge_result_id and
                    self.daily_challenge_result_id.daily_challenge_id and
                    self.daily_challenge_result_id.daily_challenge_id.knowledge_id):
                return FeedReferenceModelType.KNOWLEDGE
            return FeedReferenceModelType.LUXURY_CULTURE

        if self.type == Feed.TIPS_OF_THE_DAY_TYPE:
            if (self.tips_of_the_day_id and
                    self.tips_of_the_day_id.knowledge_id):
                return FeedReferenceModelType.KNOWLEDGE
            return FeedReferenceModelType.LUXURY_CULTURE

        if self.type == Feed.COLLEAGUE_LEVEL_UP_TYPE:
            return FeedReferenceModelType.USER

        if self.type == Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE:
            return FeedReferenceModelType.KNOWLEDGE

        if self.type == Feed.NEW_CONTENT_AVAILABLE_TYPE:
            if self.knowledge_id:
                return FeedReferenceModelType.KNOWLEDGE
            return FeedReferenceModelType.LUXURY_CULTURE

        if self.type == Feed.UPDATED_RANKING_AVAILABLE_TYPE:
            return None

        if self.type == Feed.NEW_POSTED_MEDIA_TYPE:
            return FeedReferenceModelType.MEDIA

        # TODO: Why is the reference type = 5 (Media)
        if self.type == Feed.EVALUATION_REMINDER_TYPE:
            return 5

        return FeedReferenceModelType.UNKNOWN


class FeedComment(models.Model):
    id = models.AutoField(primary_key=True)
    feed_id = models.ForeignKey(Feed)
    user_group_id = models.ForeignKey('PoleLuxe.UserGroup')
    user_id = models.ForeignKey('PoleLuxe.User')
    content = models.TextField(max_length=1000)
    like_count = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class FeedLikeLog(models.Model):
    id = models.AutoField(primary_key=True)
    feed_id = models.ForeignKey(Feed)
    user_id = models.ForeignKey('PoleLuxe.User')
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class FeedCommentLikeLog(models.Model):
    id = models.AutoField(primary_key=True)
    feed_comment_id = models.ForeignKey(FeedComment)
    user_id = models.ForeignKey('PoleLuxe.User')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
