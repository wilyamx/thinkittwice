from django.conf import settings
from rest_framework import serializers

from PoleLuxe.models import (
    DailyChallengeResult,
    KnowledgeComment,
    KnowledgeLikeLog,
    LuxuryCultureComment,
    LuxuryCultureLikeLog,
    Feed,
    Media,
)

from api.v2.serializers.daily_challenge import DailyChallengeResultForFeedSerializer
from api.v1.serializers.feed import (
    CompletedQuizForFeedSerializer,
    EvaluationReminderForFeedSerializer,
    FeedSerializer as FeedSerializerV1,
    LevelUpForFeedSerializer,
    MediaForFeedSerializer,
    NewContentForFeedSerializer,
    NewRankingForFeedSerializer,
    TipsOfTheDayForFeedSerializer,
)
import re


class ActualCompletedQuizForFeedSerializer(CompletedQuizForFeedSerializer):
    user_id = serializers.IntegerField(source='user_id.id')
    name = serializers.CharField(source='user_id.name')
    avatar_url = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    position = serializers.CharField(source='user_id.user_position_id')

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'name',
            'avatar_url',
            'content',
            'order',
            'position'
        ]


class ActualLevelUpForFeedSerializer(LevelUpForFeedSerializer):
    user_id = serializers.IntegerField(source='user_id.id')
    name = serializers.CharField(source='user_id.name')
    avatar_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()
    position = serializers.CharField(source='user_id.user_position_id')

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'name',
            'avatar_url',
            'title',
            'rank',
            'trend',
            'position'
        ]


class ActualNewContentForFeedSerializer(NewContentForFeedSerializer):
    user_id = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    order = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    featured_image_url = serializers.SerializerMethodField()
    featured_image_width = serializers.SerializerMethodField()
    featured_image_height = serializers.SerializerMethodField()
    publish_date = serializers.SerializerMethodField()

    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    commented = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'content',
            'name',
            'avatar_url',
            'like_count',
            'comment_count',
            'liked',
            'commented',
            'order',
            'images',
            'featured_image_url',
            'featured_image_width',
            'featured_image_height',
            'publish_date'
        ]

    def get_like_count(self, obj):
        like_params = {
            self.get_content_key(obj): self.get_likable_object(obj),
            'user_id__user_group_id__id': self.context.get('user_group_id')
        }
        return self.get_like_model_class(obj).objects.filter(
            **like_params
        ).count()

    def get_liked(self, obj):
        like_params = {
            self.get_content_key(obj): self.get_likable_object(obj),
            'user_id__id': self.context.get('user_id')
        }
        return self.get_like_model_class(obj).objects.filter(
            **like_params
        ).exists()

    def get_comment_count(self, obj):
        comment_params = {
            self.get_content_key(obj): self.get_likable_object(obj),
            'user_group_id': self.context.get('user_group_id')
        }
        return self.get_comment_model_class(obj).objects.filter(
            **comment_params
        ).count()

    def get_commented(self, obj):
        comment_params = {
            self.get_content_key(obj): self.get_likable_object(obj),
            'user_id__id': self.context.get('user_id')
        }
        return self.get_comment_model_class(obj).objects.filter(
            **comment_params
        ).exists()

    def get_likable_object(self, obj):
        if obj.knowledge_id:
            return obj.knowledge_id
        elif obj.luxury_culture_id:
            return obj.luxury_culture_id
        return None

    def get_content_key(self, obj):
        if obj.knowledge_id:
            return 'knowledge_id'
        elif obj.luxury_culture_id:
            return 'luxury_culture_id'
        return None

    def get_publish_date(self, obj):
        if obj.knowledge_id:
            return str(obj.knowledge_id.publish_date)
        elif obj.luxury_culture_id:
            return str(obj.luxury_culture_id.publish_date)
        return None

    def get_like_model_class(self, obj):
        if obj.knowledge_id:
            return KnowledgeLikeLog
        elif obj.luxury_culture_id:
            return LuxuryCultureLikeLog
        return None

    def get_comment_model_class(self, obj):
        if obj.knowledge_id:
            return KnowledgeComment
        elif obj.luxury_culture_id:
            return LuxuryCultureComment
        return None

    def to_representation(self, obj):
        data = super(ActualNewContentForFeedSerializer, self).to_representation(obj)

        if data['featured_image_url'] is not None:

            domain = re.match('https?://(.*[^/])/?', settings.AWS_S3_DOMAIN).group(1)
            if re.match('https?://{}(:[0-9]+)?/.*'.format(domain),
                        data['featured_image_url']) is None:
                data['featured_image_url'] = '{}{}'.format(
                    settings.AWS_S3_DOMAIN,
                    str(data['featured_image_url']).strip("/")
                )

        return data


class ActualNewRankingForFeedSerializer(NewRankingForFeedSerializer):
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'name',
            'avatar_url'
        ]


class ActualMediaForFeedSerializer(MediaForFeedSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'title',
            'content',
            'user',
            'type',
            'resources',
            'like_count',
            'comment_count',
            'liked',
            'commented',
            'created_at',
        ]

    def get_like_count(self, obj):
        return obj.likes.count()

    def has_liked(self, obj):
        return obj.likes.filter(
            id=self.context.get('user_id')
        ).exists()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def has_commented(self, obj):
        return obj.comments.filter(
            id=self.context.get('user_id')
        ).exists()


class FeedSerializer(FeedSerializerV1):

    read = serializers.BooleanField(
        source='readfeed_set.count',
        read_only=True
    )

    class Meta:
        model = Feed
        fields = [
            'id',
            'type',
            'like_count',
            'created_at',
            'model',
            'model_id',
            'tips_of_the_day_id',
            'user_group_id',
            'user_id',
            'knowledge_id',
            'luxury_culture_id',
            'daily_challenge_result_id',
            'user_level_up_log_id',
            'video_id',
            'video_title',
            'read'
        ]

    def get_more_details(self, obj):
        if (obj.type == Feed.COMPLETE_DAILY_CHALLENGE_TYPE and
                obj.daily_challenge_result_id):
            return DailyChallengeResultForFeedSerializer(
                DailyChallengeResult.objects.get(
                    pk=obj.daily_challenge_result_id.id
                ),
                context={
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.TIPS_OF_THE_DAY_TYPE:
            return TipsOfTheDayForFeedSerializer(
                obj,
                context={
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.COLLEAGUE_LEVEL_UP_TYPE:
            return ActualLevelUpForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        if obj.type == Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE:
            return ActualCompletedQuizForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        # has like_count
        if obj.type == Feed.NEW_CONTENT_AVAILABLE_TYPE:
            return ActualNewContentForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        # has like_count
        if obj.type == Feed.UPDATED_RANKING_AVAILABLE_TYPE:
            return ActualNewRankingForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        # has like_count
        if obj.type == Feed.EVALUATION_REMINDER_TYPE:
            return EvaluationReminderForFeedSerializer(obj).data

        # has like_count
        try:
            if obj.type == Feed.NEW_POSTED_MEDIA_TYPE:
                return ActualMediaForFeedSerializer(
                    Media.objects.get(pk=obj.model_id),
                    context={
                        'user_id': self.context.get('user_id'),
                        'user_group_id': self.context.get('user_group_id'),
                        'feed': obj,
                    }
                ).data
        except Media.DoesNotExist:
            return {}
