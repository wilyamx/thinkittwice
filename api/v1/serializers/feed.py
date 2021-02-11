from django.conf import settings
from django.core.cache import cache

from rest_framework import serializers
from rest_framework.settings import api_settings

from PoleLuxe.models import (
    DailyChallengeResult,
    Feed,
    FeedComment,
    FeedLikeLog,
    KnowledgeTranslation,
    LuxuryCultureTranslation,
    Media,
    ReadFeed,
    UserKnowledgeQuizResult,
)
from api import translations
from PoleLuxe.translations import (
    TRANS_EVALUATION_REMINDER
)
from PoleLuxe.constants import FeedReferenceModelType

from api.v1.mixins import serializers as serializer_mixins
from .media import MediaForFeedSerializer
from .daily_challenge import DailyChallengeResultForFeedSerializer


class ForFeedSerializer(serializers.Serializer):
    """
    Common fields for feed serializers.
    """
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()

    def get_title(self, obj):
        raise NotImplementedError()

    def get_content(self, obj):
        raise NotImplementedError()

    def get_order(self, obj):
        raise NotImplementedError()


class EvaluationReminderForFeedSerializer(ForFeedSerializer):
    def get_title(self, obj):
        return 'Evaluation Reminder'

    def get_content(self, obj):
        return TRANS_EVALUATION_REMINDER[
            settings.DEFAULT_LANGUAGE_CODE
        ]

    def get_order(self, obj):
        return -1


class FeedSerializer(serializers.ModelSerializer):
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
            'video_title'
        ]

    def get_more_details(self, obj):
        """
        Source code logic from DetailFeedSerializer.get_others()
        """
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
            return LevelUpForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        if obj.type == Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE:
            return CompletedQuizForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.NEW_CONTENT_AVAILABLE_TYPE:
            return NewContentForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.UPDATED_RANKING_AVAILABLE_TYPE:
            return NewRankingForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        if obj.type == Feed.EVALUATION_REMINDER_TYPE:
            return EvaluationReminderForFeedSerializer(obj).data

        try:
            if obj.type == Feed.NEW_POSTED_MEDIA_TYPE:
                return MediaForFeedSerializer(
                    Media.objects.get(pk=obj.model_id),
                    context={
                        'user_id': self.context.get('user_id'),
                        'user_group_id': self.context.get('user_group_id'),
                        'feed': obj,
                    }
                ).data
        except Media.DoesNotExist:
            return {}

    def to_representation(self, obj):
        data = super(FeedSerializer, self).to_representation(obj)
        include = self.context.get('include')
        if include:
            include_keys = include.split(',')
            if 'more_details' in include_keys:
                data['more_details'] = self.get_more_details(obj)
            if 'model_type' in include_keys:
                data['model_type'] = obj.get_reference_type()
            if 'is_read' in include_keys:
                data['is_read'] = ReadFeed.objects.filter(
                    user=self.context['request'].authenticated_user,
                    feed=obj
                ).exists()
            if 'tags' in include_keys:
                tags_info = {}
                if obj.knowledge_id and obj.knowledge_id.tags.count():
                    tags_info['knowledge'] = map(
                        lambda i: i.text,
                        obj.knowledge_id.tags.all()
                    )
                elif obj.luxury_culture_id and obj.luxury_culture_id.tags.count():
                    tags_info['luxury_culture'] = map(
                        lambda i: i.text,
                        obj.luxury_culture_id.tags.all()
                    )

                if len(tags_info.keys()) == 0:
                    tags_info = None

                data['tags'] = tags_info
            if 'quiz_result' in include_keys:
                request = self.context.get('request')
                if request and hasattr(request, 'authenticated_user'):
                    user = request.authenticated_user
                    if obj.knowledge_id:
                        quiz_results = UserKnowledgeQuizResult.objects.filter(
                            user_id=user,
                            knowledge_id=obj.knowledge_id
                        ).order_by('-created_at')
                        if quiz_results.exists():
                            data['quiz_result'] = {
                                'points': quiz_results.first().points,
                                'result': round(quiz_results.first().result, 2)
                            }

        return data


class LegacyFeedSerializer(FeedSerializer):
    feed_id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()
    time_stamp = serializers.SerializerMethodField()

    def get_feed_id(self, obj):
        return obj.id

    def get_title(self, obj):
        language_code = self.context.get('language_id')

        if obj.type == 3:
            return translations.TRANS_LEVEL[language_code] % (
                obj.user_level_up_log_id.level,
            )

        knowledge = obj.knowledge_id
        knowledge_title = knowledge.title
        knowledge_order = knowledge.order

        if language_code != 'EN':
            knowledge_translation = KnowledgeTranslation.objects.filter(
                language_id=language_code,
                knowledge_id=knowledge.id
            ).first()

            if knowledge_translation:
                knowledge_title = knowledge_translation.title

        return translations.TRANS_KNOWLEDGE_QUIZ[language_code] % (
            knowledge_order,
            knowledge_title
        )

    def get_feed_type(self, obj):
        return obj.type

    def get_time_stamp(self, obj):
        return obj.created_at

    class Meta:
        model = Feed
        fields = ['feed_id', 'title', 'feed_type', 'time_stamp']


class TipsOfTheDayForFeedSerializer(
    serializers.ModelSerializer,
    serializer_mixins.TranslatableMixin
):
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    publish_date = serializers.SerializerMethodField()

    def get_title(self, obj):
        """
        Return the tips of the day title for this feed.
        """
        return super(TipsOfTheDayForFeedSerializer, self).get_title(
            obj.tips_of_the_day_id
        )

    def get_content(self, obj):
        return self.get_translated_available_content(obj.tips_of_the_day_id)

    def get_message(self, obj):
        return super(TipsOfTheDayForFeedSerializer, self).get_message(obj.tips_of_the_day_id)

    def get_order(self, obj):
        if obj.tips_of_the_day_id.knowledge_id:
            return obj.tips_of_the_day_id.knowledge_id.order

        return -1

    def get_publish_date(self, obj):
        return obj.tips_of_the_day_id.publish_date

    class Meta:
        model = Feed
        fields = [
            'tips_of_the_day_id',
            'title',
            'content',
            'order',
            'message',
            'publish_date',
        ]


class LevelUpForFeedSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user_id.id')
    name = serializers.CharField(source='user_id.name')
    avatar_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    commented = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()
    position = serializers.CharField(source='user_id.user_position_id')

    def get_title(self, obj):
        try:
            return obj.user_level_up_log_id.level
        except AttributeError:
            pass

        return None

    def get_rank(self, obj):
        try:
            return obj.user_level_up_log_id.rank
        except AttributeError:
            pass

        return 0

    def get_avatar_url(self, obj):
        return settings.AWS_CLOUDFRONT_DOMAIN + str(obj.user_id.avatar_url)

    def get_like_count(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id__user_group_id=self.context.get('user_group_id')
        ).count()

    def get_comment_count(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_group_id=self.context.get('user_group_id')
        ).count()

    def get_liked(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_commented(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_trend(self, obj):
        if cache.get('trend_user_%s' % obj.user_id.id) is not None:
            return int(cache.get('trend_user_%s' % obj.user_id.id))

        return -2

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'name',
            'avatar_url',
            'title',
            'like_count',
            'comment_count',
            'liked',
            'commented',
            'rank',
            'trend',
            'position',
        ]


class CompletedQuizForFeedSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user_id.id')
    name = serializers.CharField(source='user_id.name')
    avatar_url = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    commented = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    position = serializers.CharField(source='user_id.user_position_id')

    def get_avatar_url(self, obj):
        return settings.AWS_CLOUDFRONT_DOMAIN + str(obj.user_id.avatar_url)

    def get_order(self, obj):
        return obj.knowledge_id.order

    def get_content(self, obj):
        language_code = self.context.get('language_code')

        if language_code == 'EN':
            return obj.knowledge_id.title

        translation = KnowledgeTranslation.objects.filter(
            language_id=language_code,
            knowledge_id=obj.knowledge_id_id
        ).first()

        return translation.title if translation else obj.knowledge_id.title

    def get_like_count(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id__user_group_id=self.context.get('user_group_id')
        ).count()

    def get_comment_count(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_group_id=self.context.get('user_group_id')
        ).count()

    def get_liked(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_commented(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    class Meta:
        model = Feed
        fields = [
            'user_id',
            'name',
            'avatar_url',
            'content',
            'like_count',
            'comment_count',
            'liked',
            'commented',
            'order',
            'position',
        ]


class NewContentForFeedSerializer(
    serializer_mixins.WithExtractedImagePaths,
    serializers.ModelSerializer,
):
    user_id = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    commented = serializers.SerializerMethodField()

    order = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    featured_image_url = serializers.SerializerMethodField()
    featured_image_width = serializers.SerializerMethodField()
    featured_image_height = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return 0

    def get_content(self, obj):
        language_code = self.context.get('language_code')

        # knowledge content
        if obj.knowledge_id:
            if language_code == 'EN':
                return obj.knowledge_id.title

            knowledge_translation = KnowledgeTranslation.objects.filter(
                language_id=language_code,
                knowledge_id=obj.knowledge_id
            ).first()
            if knowledge_translation:
                return knowledge_translation.title
            return obj.knowledge_id.title

        # luxury culture content
        if language_code == 'EN':
            return obj.luxury_culture_id.title

        luxury_culture_translation = LuxuryCultureTranslation.objects.filter(
            language_id=language_code,
            luxury_culture_id=obj.luxury_culture_id
        ).first()
        if luxury_culture_translation:
            return luxury_culture_translation.title
        return obj.luxury_culture_id.title

    def get_company(self, obj):
        if not obj.user_id:
            return obj.user_group_id.company_id
        return obj.user_id.company_id

    def get_name(self, obj):
        return self.get_company(obj).app.name

    def get_avatar_url(self, obj):
        return u'%s%s' % (
            settings.AWS_CLOUDFRONT_DOMAIN,
            self.get_company(obj).app.avatar
        )

    def get_like_count(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id__user_group_id=self.context.get('user_group_id')
        ).count()

    def get_comment_count(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_group_id=self.context.get('user_group_id')
        ).count()

    def get_liked(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_commented(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_order(self, obj):
        if obj.knowledge_id:
            return obj.knowledge_id.order
        else:
            return -1

    def get_images(self, obj):
        field_content = None

        if obj.knowledge_id:
            field_content = obj.knowledge_id.description
        elif obj.luxury_culture_id:
            field_content = obj.luxury_culture_id.content

        if field_content is None:
            return []

        return self.extract_images(field_content)

    def get_featured_image_url(self, obj):
        content_featured_image_url = None
        if obj.knowledge_id:
            content_featured_image_url = obj.knowledge_id.featured_image_url
        elif obj.luxury_culture_id and obj.luxury_culture_id.image_url.name:
            content_featured_image_url = obj.luxury_culture_id.image_url.url
        return content_featured_image_url

    def get_featured_image_width(self, obj):
        content_featured_image_width = None
        if obj.knowledge_id:
            content_featured_image_width = obj.knowledge_id.featured_image_width
        elif obj.luxury_culture_id:
            content_featured_image_width = obj.luxury_culture_id.image_width
        return content_featured_image_width

    def get_featured_image_height(self, obj):
        content_featured_image_height = None
        if obj.knowledge_id:
            content_featured_image_height = obj.knowledge_id.featured_image_height
        elif obj.luxury_culture_id:
            content_featured_image_height = obj.luxury_culture_id.image_height
        return content_featured_image_height

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
            'featured_image_height'
        ]


class NewRankingForFeedSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    commented = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return 0

    def get_company(self, obj):
        if not obj.user_id:
            return obj.user_group_id.company_id
        return obj.user_id.company_id

    def get_name(self, obj):
        return self.get_company(obj).app.name

    def get_avatar_url(self, obj):
        return u'%s%s' % (
            settings.AWS_CLOUDFRONT_DOMAIN,
            self.get_company(obj).app.avatar
        )

    def get_like_count(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id__user_group_id=self.context.get('user_group_id')
        ).count()

    def get_comment_count(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_group_id=self.context.get('user_group_id')
        ).count()

    def get_liked(self, obj):
        return FeedLikeLog.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    def get_commented(self, obj):
        return FeedComment.objects.filter(
            feed_id=obj.id,
            user_id=self.context.get('user_id')
        ).count() > 0

    class Meta:
        model = Feed
        fields = ['user_id',
                  'name',
                  'avatar_url',
                  'like_count',
                  'comment_count',
                  'liked',
                  'commented']


class DetailFeedSerializer(LegacyFeedSerializer):
    others = serializers.SerializerMethodField()
    ref = serializers.SerializerMethodField()

    def get_time_stamp(self, obj):
        return obj.created_at.strftime(api_settings.DATETIME_FORMAT)

    def get_others(self, obj):
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
            return LevelUpForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        if obj.type == Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE:
            return CompletedQuizForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.NEW_CONTENT_AVAILABLE_TYPE:
            return NewContentForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id'),
                    'language_code': self.context.get('language_code')
                }
            ).data

        if obj.type == Feed.UPDATED_RANKING_AVAILABLE_TYPE:
            return NewRankingForFeedSerializer(
                obj,
                context={
                    'user_id': self.context.get('user_id'),
                    'user_group_id': self.context.get('user_group_id')
                }
            ).data

        if obj.type == Feed.EVALUATION_REMINDER_TYPE:
            return EvaluationReminderForFeedSerializer(obj).data

        try:
            if obj.type == Feed.NEW_POSTED_MEDIA_TYPE:
                return MediaForFeedSerializer(
                    Media.objects.get(pk=obj.model_id),
                    context={
                        'user_id': self.context.get('user_id'),
                        'user_group_id': self.context.get('user_group_id'),
                        'feed': obj,
                    }
                ).data
        except Media.DoesNotExist:
            return {}

    def get_ref(self, obj):
        """
        Get reference.
        """
        if obj.type == Feed.COMPLETE_DAILY_CHALLENGE_TYPE:
            challenge = obj.daily_challenge_result_id.daily_challenge_id
            if challenge.knowledge_id:
                return {
                    'type': FeedReferenceModelType.KNOWLEDGE,
                    'ref_id': challenge.knowledge_id_id
                }
            return {
                'type': FeedReferenceModelType.LUXURY_CULTURE,
                'ref_id': challenge.luxury_culture_id_id
            }

        if obj.type == Feed.TIPS_OF_THE_DAY_TYPE:
            if obj.tips_of_the_day_id.knowledge_id:
                return {
                    'type': FeedReferenceModelType.KNOWLEDGE,
                    'ref_id': obj.tips_of_the_day_id.knowledge_id.id,
                }
            elif obj.tips_of_the_day_id.luxury_culture_id:
                return {
                    'type': FeedReferenceModelType.LUXURY_CULTURE,
                    'ref_id': obj.tips_of_the_day_id.luxury_culture_id.id,
                }
            else:
                # allow no linked content
                return None

        if obj.type == Feed.COLLEAGUE_LEVEL_UP_TYPE:
            return {
                'type': FeedReferenceModelType.USER,
                'ref_id': obj.id
            }

        if obj.type == Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE:
            return {
                'type': FeedReferenceModelType.KNOWLEDGE,
                'ref_id': obj.knowledge_id.id
            }

        if obj.type == Feed.NEW_CONTENT_AVAILABLE_TYPE:
            if obj.knowledge_id:
                return {
                    'type': FeedReferenceModelType.KNOWLEDGE,
                    'ref_id': obj.knowledge_id.id
                }
            return {
                'type': FeedReferenceModelType.LUXURY_CULTURE,
                'ref_id': obj.luxury_culture_id.id
            }

        if obj.type == Feed.UPDATED_RANKING_AVAILABLE_TYPE:
            return None

        if obj.type == Feed.NEW_POSTED_MEDIA_TYPE:
            return {
                'type': FeedReferenceModelType.MEDIA,
                'ref_id': obj.model_id
            }

        # TODO: Why is the reference type = 5 (Media)
        if obj.type == Feed.EVALUATION_REMINDER_TYPE:
            return {'type': 5, 'ref_id': None}

    class Meta:
        model = Feed
        fields = ['id', 'type', 'time_stamp', 'others', 'ref']
