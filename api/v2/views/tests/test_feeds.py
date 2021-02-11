import requests_mock
import datetime
import random
import tempfile
import re

from boto.s3.key import Key
from moto import mock_s3_deprecated
from PIL import Image
from rest_framework import status

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.test.utils import override_settings

from PoleLuxe.factories import (
    AppLanguageFactory,
    DailyChallengeFactory,
    DailyChallengeResultFactory,
    DailyChallengeTranslationFactory,
    FeedFactory,
    KnowledgeCommentFactory,
    KnowledgeFactory,
    KnowledgeLikeLogFactory,
    KnowledgeTranslationFactory,
    LuxuryCultureCommentFactory,
    LuxuryCultureFactory,
    LuxuryCultureLikeLogFactory,
    LuxuryCultureTranslationFactory,
    MediaCommentFactory,
    MediaFactory,
    MediaResourceFactory,
    ProductGroupFactory,
    TagFactory,
    TipsOfTheDayFactory,
    TipsOfTheDayTranslationFactory,
    UserAchievementGroupFactory,
    UserFactory,
    UserKnowledgeQuizResultFactory,
    UserLevelUpLogFactory,
    VideoFactory,
    ReadFeedFactory
)

from PoleLuxe.models import (
    AppLanguage,
    DailyChallenge,
    DailyChallengeTranslation,
    Feed,
    Knowledge,
    KnowledgeComment,
    KnowledgeLikeLog,
    KnowledgeTranslation,
    LuxuryCulture,
    LuxuryCultureComment,
    LuxuryCultureLikeLog,
    LuxuryCultureTranslation,
    Media,
    Tag,
    UserGroup,
    UserKnowledgeQuizResult,
)
from PoleLuxe.constants import CategoryType

from api.tests.base import BaseAPITestCase
from PoleLuxe.factories.pinned import PinnedTagFactory


class TestFeeds(BaseAPITestCase):
    """
    Test api endpoint /api/v2/feeds/
    """
    fixtures = ['tags', 'app_language']

    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v2:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestFeeds, self).setUp()

        self.brand_tag = Tag.objects.get(text='brand')
        self.news_tag = Tag.objects.get(text='news')
        self.market_tag = Tag.objects.get(text='market')

        self.server_time = datetime.datetime.utcnow()
        self._feed_types()

        self.app_languages = AppLanguage.objects.exclude(code='EN')

        self.assertEqual(0, UserKnowledgeQuizResult.objects.count())

    @mock_s3_deprecated
    def tearDown(self):
        super(TestFeeds, self).tearDown()

    @mock_s3_deprecated
    def _upload_test_resources(self, resources):
        _, bucket = self.create_s3_buckets()
        for path, resource in resources.items():
            resource.seek(0)
            k = Key(bucket)
            k.key = path
            k.set_contents_from_file(resource)

    @override_settings(AWS_S3_DOMAIN='https://tit-test.s3.amazonaws.com/')
    @requests_mock.mock()
    def _feed_types(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        self.create_s3_buckets()

        # new image
        image = Image.new('RGB', (100, 100))
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(temp_file)

        self._upload_test_resources({
            temp_file.name: open(temp_file.name, 'rb')})

        self.knowledge = KnowledgeFactory(
            featured_image_url=temp_file.name
        )
        self.luxury_culture = LuxuryCultureFactory()
        # - - - - - - -
        self.product_group = ProductGroupFactory()
        self.product_group.user_group.add(
            self.user.user_group_id
        )
        self.product_group.save()

        self.knowledge_for_dc = KnowledgeFactory(
            publish_date=self.server_time
        )
        self.knowledge_for_dc.product_group = [self.product_group.id]
        self.knowledge_for_dc.save()

        self.daily_challenge = DailyChallengeFactory(
            publish_date=self.server_time + datetime.timedelta(days=1),
            knowledge_id=self.knowledge_for_dc,
            luxury_culture_id=None
        )
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user,
            daily_challenge_id=self.daily_challenge
        )
        self.feed_1 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        self.feed_10 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        )
        # - - - - - - - - - - - - -
        # TIPS_OF_THE_DAY_TYPE
        # - - - - - - - - - - - - -
        # feed is pre-generated via worker (checknewcontent)
        self.tips_of_the_day = TipsOfTheDayFactory(
            knowledge_id=KnowledgeFactory(
                publish_date=self.server_time - datetime.timedelta(
                    hours=self.user.user_group_id.timezone
                )
            ),
            luxury_culture_id=None
        )
        self.feed_2 = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=self.tips_of_the_day
        )
        # - - - - - - -
        self.user_level_up_log = UserLevelUpLogFactory(
            user_id=self.user
        )
        self.feed_3 = FeedFactory(
            type=Feed.COLLEAGUE_LEVEL_UP_TYPE,
            user_level_up_log_id=self.user_level_up_log,
            user_id=self.user
        )
        self.feed_30 = FeedFactory(
            type=Feed.COLLEAGUE_LEVEL_UP_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.knowledge.tags.add(self.brand_tag)
        self.knowledge.tags.add(self.news_tag)
        self.feed_4 = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user
        )
        # - - - - - - -
        self.luxury_culture.tags.add(self.market_tag)
        self.luxury_culture.tags.add(self.news_tag)
        self.feed_5 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user
        )
        self.feed_51 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=self.luxury_culture,
            user_id=self.user
        )
        # - - - - - - -
        self.user_achievement_group = UserAchievementGroupFactory()
        self.feed_6 = FeedFactory(
            type=Feed.UPDATED_RANKING_AVAILABLE_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.video = VideoFactory(
            title='video-title',
            image_url='video-image.jpg',
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        # - - - - - - - - - - - - -
        # NEW_POSTED_MEDIA_TYPE
        # - - - - - - - - - - - - -
        # a feed is generated for uploader after created the model
        uploader = UserFactory()
        self.media = MediaFactory(
            user=uploader
        )
        MediaResourceFactory(
            media=self.media
        )
        self.feed_8 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=self.media.id,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        self.feed_81 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )

        # a feed is generated for uploader after created the model
        self.media_text_type = MediaFactory(
            user=self.user,
            type=Media.TEXT_TYPE,
            is_active=True
        )
        self.feed_82 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=self.media_text_type.id,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        # - - - - - - -
        self.feed_9 = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.user
        )

        self.feed_pinned = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=KnowledgeFactory(),
            user_group_id=self.user.user_group_id,
            is_pinned=True,
        )

    def _create_translations(self):
        for content in DailyChallenge.objects.all():
            for language in AppLanguage.objects.exclude(code='EN'):
                DailyChallengeTranslationFactory(
                    language=language,
                    daily_challenge_id=content
                )

    def _excluded_filter_types(self):
        """
        Supported feed types
            COMPLETE_DAILY_CHALLENGE_TYPE = 1
            TIPS_OF_THE_DAY_TYPE = 2
            NEW_CONTENT_AVAILABLE_TYPE = 5
            NEW_POSTED_MEDIA_TYPE = 8
        """
        return [
            Feed.COLLEAGUE_LEVEL_UP_TYPE,
            Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            Feed.UPDATED_RANKING_AVAILABLE_TYPE,
            Feed.NEW_POSTED_VIDEO_TYPE,
            Feed.EVALUATION_REMINDER_TYPE
        ]

    def _default_filter_queryset(self):
        return Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=self._excluded_filter_types(),
        ).filter_evaluation_reminders(
            self.user
        )

    def _assert_likes(
        self,
        response_data
    ):
        if 'more_details' in response_data:
            more_details = response_data['more_details']

            knowledge_id = response_data['knowledge_id']
            luxury_culture_id = response_data['luxury_culture_id']

            content = None
            like_model_class = None
            content_key = None

            if knowledge_id:
                content = Knowledge.objects.get(id=knowledge_id)
                content_key = 'knowledge_id'
                like_model_class = KnowledgeLikeLog

            elif luxury_culture_id:
                content = LuxuryCulture.objects.get(id=luxury_culture_id)
                content_key = 'luxury_culture_id'
                like_model_class = LuxuryCultureLikeLog

            if content and like_model_class and content_key:
                like_params = {
                    content_key: content,
                    'user_id__user_group_id': self.user.user_group_id,
                }
                queryset = like_model_class.objects.filter(**like_params)
                self.assertEqual(
                    queryset.count(),
                    int(more_details['like_count'])
                )
                self.assertEqual(
                    queryset.filter(
                        user_id=self.user
                    ).exists(),
                    bool(more_details['liked'])
                )

    def _assert_comments(self, response_data):
        if 'more_details' in response_data:
            more_details = response_data['more_details']

            knowledge_id = response_data['knowledge_id']
            luxury_culture_id = response_data['luxury_culture_id']

            content = None
            comment_model_class = None
            content_key = None

            if knowledge_id:
                content = Knowledge.objects.get(id=knowledge_id)
                content_key = 'knowledge_id'
                comment_model_class = KnowledgeComment

            elif luxury_culture_id:
                content = LuxuryCulture.objects.get(id=luxury_culture_id)
                content_key = 'luxury_culture_id'
                comment_model_class = LuxuryCultureComment

            if content and comment_model_class and content_key:
                comment_params = {
                    content_key: content,
                    'user_group_id': self.user.user_group_id,
                }

                queryset = comment_model_class.objects.filter(**comment_params)
                self.assertEqual(
                    queryset.count(),
                    int(more_details['comment_count'])
                )
                self.assertEqual(
                    queryset.filter(
                        user_id=self.user
                    ).exists(),
                    bool(more_details['commented'])
                )

    def _assert_more_details(self, response_data):
        if 'more_details' in response_data:
            more_details = response_data['more_details']

            if 'featured_image_url' in more_details and \
                    more_details['featured_image_url'] is not None:
                domain = re.match('https?://(.*[^/])/?', settings.AWS_S3_DOMAIN).group(1)
                self.assertRegex(more_details['featured_image_url'],
                                 'https?://{}(:[0-9]+)?/.*'.format(domain))

            if 'publish_date' in more_details:
                self.assertTrue(more_details['publish_date'])

            if 'user' in more_details and 'avatar_url' in more_details['user']:
                self.assertEqual(
                    settings.AWS_CLOUDFRONT_DOMAIN + str(self.user.avatar_url),
                    more_details['user']['avatar_url']
                )

    def _assert_quiz_result(self, response_data):
        if response_data['knowledge_id']:
            quiz_result = UserKnowledgeQuizResult.objects.filter(
                knowledge_id_id=response_data['knowledge_id'],
                user_id=self.user
            )
            if 'quiz_result' in response_data:
                quiz_result_info = response_data['quiz_result']

                self.assertEqual(1, quiz_result.count())
                self.assertEqual(
                    quiz_result.first().points,
                    quiz_result_info['points']
                )
                self.assertEqual(
                    quiz_result.first().result,
                    quiz_result_info['result']
                )
            if not quiz_result.exists():
                self.assertNotIn('quiz_result', response_data.keys())

    def _assert_daily_challenge_translated_content(
        self,
        response_data,
        language_code='EN'
    ):
        more_details = response_data['more_details']
        content = self.daily_challenge_result.daily_challenge_id
        if language_code == 'EN':
            self.assertEqual(content.title, more_details['title'])
        else:
            translation = DailyChallengeTranslation.objects.get(
                daily_challenge_id=content,
                language=AppLanguage.objects.get(code=language_code)
            )
            self.assertEqual(translation.title, more_details['title'])

    def test_invalid_user(self):
        invalid_token = 'invalid'
        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=invalid_token
        )
        self.assertEqual(
            status.HTTP_401_UNAUTHORIZED,
            response.status_code
        )

    def test_invalid_usergroup(self):
        invalid_usergroup_id = 100
        response = self.client.get(
            self.url,
            data={
                'user_group_id': invalid_usergroup_id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )
        self.assertEqual(
            status.HTTP_404_NOT_FOUND,
            response.status_code
        )

    def test_list(self):
        queryset = self._default_filter_queryset().exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).filter(is_pinned=False).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)

    def test_list_with_language_code(self):
        self._create_translations()

        for app_language in [
            AppLanguage.objects.get(code='JP'),
            AppLanguage.objects.get(code='FR'),
            AppLanguage.objects.get(code='EN')
        ]:
            queryset = self._default_filter_queryset().exclude(
                Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
                ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
                 (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
            ).filter(is_pinned=False).order_by('-id')
            expected_data = list(queryset.values('id'))

            response = self.client.get(
                self.url,
                data={
                    'user_group_id': self.user.user_group_id.id,
                    'language_code': app_language.code,
                    'include': 'more_details'
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )

            response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
            self.assertEqual(len(expected_data), len(response.data))
            self.assertDictEqualRecursive(expected_data, response_sorted)

            for response_data in response.data:
                if response_data['type'] == Feed.COMPLETE_DAILY_CHALLENGE_TYPE:
                    self._assert_daily_challenge_translated_content(
                        response_data,
                        app_language.code
                    )

    def test_list_include_count(self):
        queryset = self._default_filter_queryset().exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).filter(is_pinned=False).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'count',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        self.assertTrue('count' in response._headers)
        self.assertEqual(
            len(expected_data),
            int(response._headers['count'][1])
        )

    def test_list_include_quiz_result(self):
        # quiz result associated to knowledge content
        UserKnowledgeQuizResultFactory(
            knowledge_id=self.knowledge,
            user_id=self.user,
            result=1.0,
            points=200
        )

        # new image
        image = Image.new('RGB', (100, 100))
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(temp_file)

        self._upload_test_resources({
            temp_file.name: open(temp_file.name, 'rb')})

        self.another_knowledge = KnowledgeFactory(
            featured_image_url=temp_file.name
        )

        # feed without quiz result
        self.another_feed = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=self.another_knowledge,
            user_id=self.user
        )

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'quiz_result',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        for response_data in response.data:
            self._assert_quiz_result(response_data)

    @override_settings(
        AWS_CLOUDFRONT_DOMAIN='https://myapp.cloudfront.net'
    )
    def test_list_include(self):
        include_cases = [
            'model_type',
            'more_details',
            'is_read',
            'tags'
        ]
        for case in include_cases:
            response = self.client.get(
                self.url,
                data={
                    'user_group_id': self.user.user_group_id.id,
                    'include': case,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )
            self.assertTrue(case in response.data[0])

            for response_data in response.data:
                self._assert_more_details(response_data)

    def test_featured_image_url(self):
        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'more_details',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        data_list = list(
            filter(lambda x: x['luxury_culture_id'] or x['knowledge_id'], response.data)
        )

        for data_item in data_list:
            featured_image_sample = data_item['more_details']['featured_image_url']
            self.assertNotRegex(featured_image_sample, 'https?://.*https?://')
            self.assertIn('featured_image_width', data_item['more_details'])
            self.assertIn('featured_image_height', data_item['more_details'])

    @requests_mock.mock()
    def test_list_like_and_comment_count(self, m):
        """
        Count only likes or comments of the same user group
        """
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)

        # - - - - - - - - - - - - - - - - - - - - - - -
        # likes content (from different usergroup)
        # this won't include in the count
        # - - - - - - - - - - - - - - - - - - - - - - -

        for _ in range(10):
            # user with different usergroup
            user = UserFactory()
            KnowledgeLikeLogFactory(
                knowledge_id=self.feed_5.knowledge_id,
                user_id=user
            )

        for _ in range(10):
            # user with different usergroup
            user = UserFactory()
            LuxuryCultureLikeLogFactory(
                luxury_culture_id=self.feed_51.luxury_culture_id,
                user_id=user
            )

        # - - - - - - - - - - - - - - - - - - - - - - -
        # likes content (from same usergroup)
        # - - - - - - - - - - - - - - - - - - - - - - -

        for _ in range(2):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            KnowledgeLikeLogFactory(
                knowledge_id=self.feed_5.knowledge_id,
                user_id=user
            )

        for _ in range(4):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            LuxuryCultureLikeLogFactory(
                luxury_culture_id=self.feed_51.luxury_culture_id,
                user_id=user
            )

        for _ in range(6):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            self.media.likes.add(user)

        # - - - - - - - - - - - - - - - - - - - - - - -
        # comments content (from different usergroup)
        # this won't include in the count
        # - - - - - - - - - - - - - - - - - - - - - - -

        for _ in range(10):
            # user with different usergroup
            user = UserFactory()
            KnowledgeCommentFactory(
                knowledge_id=self.feed_5.knowledge_id,
                user_id=user,
                user_group_id=user.user_group_id
            )

        for _ in range(10):
            # user with different usergroup
            user = UserFactory()
            LuxuryCultureCommentFactory(
                luxury_culture_id=self.feed_51.luxury_culture_id,
                user_id=user,
                user_group_id=user.user_group_id
            )

        # - - - - - - - - - - - - - - - - - - - - - - -
        # comments (from same usergroup)
        # - - - - - - - - - - - - - - - - - - - - - - -

        for _ in range(3):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            KnowledgeCommentFactory(
                knowledge_id=self.feed_5.knowledge_id,
                user_id=user,
                user_group_id=user.user_group_id
            )

        for _ in range(5):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            LuxuryCultureCommentFactory(
                luxury_culture_id=self.feed_51.luxury_culture_id,
                user_id=user,
                user_group_id=user.user_group_id
            )

        for _ in range(7):
            # user with the same usergroup
            user = UserFactory(
                user_group_id=self.user.user_group_id
            )
            MediaCommentFactory(
                user=user,
                media=self.media
            )

        # - - - - - - -

        queryset = self._default_filter_queryset().exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).filter(is_pinned=False).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'more_details',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)

        for response_data in response.data:
            self._assert_likes(response_data)
            self._assert_comments(response_data)

        # - - - - - - -

        # removing all likes
        KnowledgeLikeLog.objects.all().delete()
        LuxuryCultureLikeLog.objects.all().delete()
        self.media.likes.all().delete()

        # removing all comments
        KnowledgeComment.objects.all().delete()
        LuxuryCultureComment.objects.all().delete()
        self.media.comments.all().delete()

        # liked by requested user only
        KnowledgeLikeLogFactory(
            knowledge_id=self.feed_5.knowledge_id,
            user_id=self.user
        )
        LuxuryCultureLikeLogFactory(
            luxury_culture_id=self.feed_51.luxury_culture_id,
            user_id=self.user
        )
        self.media.likes.add(self.user)

        # commented by requested user only
        KnowledgeCommentFactory(
            knowledge_id=self.feed_5.knowledge_id,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        LuxuryCultureCommentFactory(
            luxury_culture_id=self.feed_51.luxury_culture_id,
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        MediaCommentFactory(
            user=self.user,
            media=self.media
        )

        queryset = self._default_filter_queryset().exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).filter(is_pinned=False).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'more_details',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)

        for response_data in response.data:
            self._assert_likes(response_data)
            self._assert_comments(response_data)

    def test_list_filter_by_usergroup(self):
        user_groups = UserGroup.objects.all()
        for feed in Feed.objects.filter(user_group_id__isnull=True):
            random_index = random.randint(0, user_groups.count() - 1)
            feed.user_group_id = user_groups[random_index]
            feed.save()

        for user_group in user_groups:
            queryset = Feed.objects.get_general(
                self.user.id,
                user_group.id,
                user_group.timezone,
                excluded_types=self._excluded_filter_types(),
            ).filter_evaluation_reminders(
                self.user
            ).filter(is_pinned=False).exclude(
                Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
                ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
                 (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
            ).order_by('-id')
            expected_data = list(queryset.values('id'))

            response = self.client.get(
                self.url,
                data={
                    'user_group_id': user_group.id,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )
            response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
            self.assertEqual(len(expected_data), len(response.data))
            self.assertDictEqualRecursive(expected_data, response_sorted)

    @requests_mock.mock()
    def test_list_filter_by_new_posted_media_type(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)

        same_group_user = UserFactory(
            user_group_id=self.user.user_group_id
        )

        user = same_group_user
        user_group = user.user_group_id

        queryset = Feed.objects.get_general(
            user.id,
            user_group.id,
            user_group.timezone,
            excluded_types=self._excluded_filter_types(),
        ).filter_evaluation_reminders(
            user
        ).exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).filter(is_pinned=False).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': user_group.id,
            },
            HTTP_X_AUTH_TOKEN=user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)

        # all feed type Feed.NEW_POSTED_MEDIA_TYPE should specify the user group
        self.assertEqual(
            Feed.objects.filter(
                type=Feed.NEW_POSTED_MEDIA_TYPE
            ).count(),
            Feed.objects.filter(
                type=Feed.NEW_POSTED_MEDIA_TYPE,
                user_group_id__isnull=False
            ).count()
        )

        # create feed by user group
        # the uploader is from different user group
        self.assertEqual(
            1, Feed.objects.filter(
                type=Feed.NEW_POSTED_MEDIA_TYPE,
                model_id=self.media.id,
                user_group_id=user.user_group_id
            ).count())

        for feed in response.data:
            if feed['type'] == Feed.NEW_POSTED_MEDIA_TYPE:
                self.assertEqual(
                    user.user_group_id.id,
                    feed['user_group_id'],
                    msg='Feed from user group {} should be excluded in home feed'.format(
                        feed['user_group_id']
                    )
                )

    def test_list_filter_by_language_code_knowledge_content(self):
        self.assertEqual(0, KnowledgeTranslation.objects.count())

        for language in self.app_languages:
            KnowledgeTranslationFactory(
                knowledge=self.knowledge,
                language=language
            )

        for language in self.app_languages:
            language_code = language.code
            response = self.client.get(
                self.url,
                data={
                    'include': 'more_details',
                    'user_group_id': self.user.user_group_id.id,
                    'language_code': language_code,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )

            for response_data in response.data:
                if response_data['knowledge_id'] == self.knowledge.id:
                    more_details = response_data['more_details']
                    expected_translation = KnowledgeTranslation.objects.get(
                        knowledge=self.knowledge,
                        language=language
                    )
                    self.assertEqual(
                        expected_translation.title,
                        more_details['content']
                    )

    def test_list_filter_by_language_code_luxury_culture_content(self):
        self.assertEqual(0, LuxuryCultureTranslation.objects.count())

        for language in self.app_languages:
            LuxuryCultureTranslationFactory(
                luxury_culture=self.luxury_culture,
                language=language
            )

        for language in self.app_languages:
            language_code = language.code
            response = self.client.get(
                self.url,
                data={
                    'include': 'more_details',
                    'user_group_id': self.user.user_group_id.id,
                    'language_code': language_code,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )

            for response_data in response.data:
                if response_data['luxury_culture_id'] == self.luxury_culture.id:
                    more_details = response_data['more_details']
                    expected_translation = LuxuryCultureTranslation.objects.get(
                        luxury_culture=self.luxury_culture,
                        language=language
                    )
                    self.assertEqual(
                        expected_translation.title,
                        more_details['content']
                    )

    def test_create_with_permission(self):
        new_daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user
        )
        self.modelPermissionsSetup(Feed, 'add')
        self.modelPermissionsSetup(Feed, 'change')

        data = {
            'type': Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            'daily_challenge_result_id': new_daily_challenge_result.id
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_X_AUTH_TOKEN=self.user.token,
            format='json',
        )
        self.assertEqual(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            response.status_code
        )

    def test_update_with_permission(self):
        self.url = reverse(
            'api-v2:feed-detail',
            kwargs={'pk': self.feed_1.id}
        )
        self.modelPermissionsSetup(Feed, 'change')

        response = self.client.put(
            self.url,
            HTTP_X_AUTH_TOKEN=self.user.token,
            format='json',
        )
        self.assertEqual(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            response.status_code
        )

    def test_partial_update_with_permission(self):
        self._feed_types()
        self.url = reverse(
            'api-v2:feed-detail',
            kwargs={'pk': self.feed_1.id}
        )
        self.modelPermissionsSetup(Feed, 'change')

        response = self.client.patch(
            self.url,
            HTTP_X_AUTH_TOKEN=self.user.token,
            format='json',
        )
        self.assertEqual(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            response.status_code
        )

    def test_destroy_with_permission(self):
        self.url = reverse(
            'api-v2:feed-detail',
            kwargs={'pk': self.feed_1.id}
        )
        self.modelPermissionsSetup(Feed, 'delete')

        response = self.client.delete(
            self.url,
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            response.status_code
        )

    def test_get_single_feed_types(self):
        """
        Test get single feed depending on Feed.type.
        """
        request_param_cases = [
            {
                'type': Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_1,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_10,
                'valid': False,
                'allow_empty_results': False,
            },
            {
                'type': Feed.TIPS_OF_THE_DAY_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_2,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.COLLEAGUE_LEVEL_UP_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_3,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.COLLEAGUE_LEVEL_UP_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_30,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_4,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.NEW_CONTENT_AVAILABLE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_5,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.NEW_CONTENT_AVAILABLE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_51,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.UPDATED_RANKING_AVAILABLE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_6,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.NEW_POSTED_MEDIA_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_8,
                'valid': True,
                'allow_empty_results': False,
            },
            {
                'type': Feed.NEW_POSTED_MEDIA_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_81,
                'valid': True,
                'allow_empty_results': True,
            },
            {
                'type': Feed.EVALUATION_REMINDER_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_9,
                'valid': True,
                'allow_empty_results': False,
            }
        ]

        for index, item in enumerate(request_param_cases):
            data = {
                'feed_id': item['feed'].id,
                'user_group_id': item['user_group_id'],
                'user_id': self.user.id,
            }

            response = self.client.get(
                self.url,
                data=data,
                format='json',
                HTTP_X_AUTH_TOKEN=self.user.token
            )

            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code,
                msg='Response error status {} from case index {}.'.format(
                    response.status_code,
                    index)
            )

            if item['allow_empty_results']:
                self.assertEqual(0, len(response.data))
            else:
                self.assertEqual(
                    1, len(response.data),
                    msg='Expected 1 result but got {} from case index {}.'.format(
                        len(response.data), index
                    )
                )
                self.assertDictEqualRecursive(
                    {
                        'id': item['feed'].id,
                        'type': item['feed'].type,
                    },
                    response.data[0]
                )

    def test_pinned_should_not_show(self):
        tag = PinnedTagFactory(company=self.user.user_group_id.company_id)
        feed = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=self.luxury_culture,
            user_id=self.user,
        )
        feed.pinned_tags = [tag.id]
        feed.is_pinned = True
        feed.save()
        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(200, response.status_code)
        # pinned should not show up in normal feed
        self.assertEqual(0, len(list(filter(lambda i: i['id'] == feed.id, response.data))))

    def test_pinned_filter(self):
        tag = PinnedTagFactory(company=self.user.user_group_id.company_id)

        base_time = datetime.datetime(year=2020, month=10, day=27, hour=9, minute=0, second=0)

        date1 = base_time + datetime.timedelta(days=1)
        date2 = base_time + datetime.timedelta(days=2)
        date3 = base_time + datetime.timedelta(days=3)

        # scrambled the feed to force error

        # pinned and not read
        feed3 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=KnowledgeFactory(publish_date=date3, title="feed3"),
            user_group_id=self.user.user_group_id,
        )
        feed3.pinned_tags = [tag.id]
        feed3.is_pinned = True
        feed3.save()

        # pinned amd read
        feed1 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=LuxuryCultureFactory(publish_date=date1, title="feed1"),
            user_group_id=self.user.user_group_id,
        )
        feed1.pinned_tags = [tag.id]
        feed1.is_pinned = True
        feed1.save()
        ReadFeedFactory(user=self.user, feed=feed1)

        # pinned and not read
        feed2 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=LuxuryCultureFactory(publish_date=date2, title="feed2"),
            user_group_id=self.user.user_group_id,
        )
        feed2.pinned_tags = [tag.id]
        feed2.is_pinned = True
        feed2.save()

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'pinned_tag_id': tag.id
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(200, response.status_code)
        # unread should show up first
        self.assertEqual(feed2.id, response.data[0]['id'], "Wrong sorting")
        self.assertEqual(feed3.id, response.data[1]['id'], "Wrong sorting")
        self.assertEqual(feed1.id, response.data[2]['id'], "Wrong sorting")
        self.assertTrue(response.data[2]['read'])

    def test_tips(self):
        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'include': 'more_details',
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        # extract the tip from the feed
        tip = list(filter(lambda x: x['tips_of_the_day_id'] is not None, response.data))[0]
        self.assertIn('message', tip['more_details'].keys())
        self.assertIn('publish_date', tip['more_details'].keys())


class TestTipsOfTheDayFeedFilterByLanguageCode(BaseAPITestCase):
    """
    Test api endpoint /api/v2/feeds/
    """

    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v2:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestTipsOfTheDayFeedFilterByLanguageCode, self).setUp()

        self.app_languages = [
            AppLanguageFactory(code='CN', name='Simplified Chinese'),
            AppLanguageFactory(code='FR', name='French'),
            AppLanguageFactory(code='JP', name='Japanese'),
            AppLanguageFactory(code='KR', name='Korean'),
            AppLanguageFactory(code='TC', name='Traditional Chinese')
        ]

    def _excluded_filter_types(self):
        """
        Supported feed types
            COMPLETE_DAILY_CHALLENGE_TYPE = 1
            TIPS_OF_THE_DAY_TYPE = 2
            NEW_CONTENT_AVAILABLE_TYPE = 5
            NEW_POSTED_MEDIA_TYPE = 8
        """
        return [
            Feed.COLLEAGUE_LEVEL_UP_TYPE,
            Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            Feed.UPDATED_RANKING_AVAILABLE_TYPE,
            Feed.NEW_POSTED_VIDEO_TYPE,
            Feed.EVALUATION_REMINDER_TYPE
        ]

    def _default_filter_queryset(self):
        return Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=self._excluded_filter_types(),
        ).order_by('-id')

    def _assert_single_feed_list(self, expected_data, response_data):
        self.assertEqual(1, len(response_data), msg='Expect to return 1 feed.')
        self.assertEqual(len(expected_data), len(response_data))
        self.assertDictEqualRecursive(expected_data, response_data)

    def _assert_content_for_language_code(
        self,
        feed_content,
        linked_content,
        more_details,
        language_code=None
    ):
        feed_content_translated_objects = feed_content.get_translated_objects(language_code)

        if feed_content_translated_objects.count():
            self.assertEqual(
                feed_content_translated_objects.first().title,
                more_details['title']
            )
            self.assertEqual(
                linked_content.get_translated_title(language_code),
                more_details['content']
            )
        else:
            self.assertEqual(feed_content.title, more_details['title'])
            self.assertEqual(linked_content.title, more_details['content'])

    def test_no_filter_by_language_code_luxury_culture_linked_content(self):
        # assumed linked content was published already
        linked_content = LuxuryCultureFactory(
            publish_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        feed_content = TipsOfTheDayFactory(
            luxury_culture_id=linked_content,
            knowledge_id=None
        )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=feed_content,
            video_title=None,
        )

        expected_data = list(
            self._default_filter_queryset().values('id', 'type', 'tips_of_the_day_id')
        )

        response = self.client.get(
            self.url,
            data={
                'include': 'more_details',
                'user_group_id': self.user.user_group_id.id,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        self._assert_single_feed_list(
            expected_data, response.data
        )
        self._assert_content_for_language_code(
            feed_content,
            linked_content,
            response.data[0]['more_details'],
            self.user.language.code
        )

    def test_no_filter_by_language_code_knowledge_linked_content(self):
        # assumed linked content was published already
        linked_content = KnowledgeFactory(
            publish_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        feed_content = TipsOfTheDayFactory(
            luxury_culture_id=None,
            knowledge_id=linked_content
        )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=feed_content,
            video_title=None,
        )

        expected_data = list(
            self._default_filter_queryset().values('id', 'type', 'tips_of_the_day_id')
        )

        response = self.client.get(
            self.url,
            data={
                'include': 'more_details',
                'user_group_id': self.user.user_group_id.id,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )
        self._assert_single_feed_list(
            expected_data, response.data
        )
        self._assert_content_for_language_code(
            feed_content,
            linked_content,
            response.data[0]['more_details'],
            self.user.language.code
        )

    def test_filter_by_language_code_luxury_culture_linked_content(self):
        # assumed linked content was published already
        linked_content = LuxuryCultureFactory(
            publish_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        feed_content = TipsOfTheDayFactory(
            luxury_culture_id=linked_content,
            knowledge_id=None
        )

        for language in self.app_languages:
            TipsOfTheDayTranslationFactory(
                tips_of_the_day=feed_content,
                language=language
            )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=feed_content,
            video_title=None,
        )

        expected_data = list(
            self._default_filter_queryset().values('id', 'type', 'tips_of_the_day_id')
        )

        for language in self.app_languages:
            language_code = language.code
            response = self.client.get(
                self.url,
                data={
                    'include': 'more_details',
                    'user_group_id': self.user.user_group_id.id,
                    'language_code': language_code,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )
            self._assert_single_feed_list(
                expected_data, response.data
            )
            self._assert_content_for_language_code(
                feed_content,
                linked_content,
                response.data[0]['more_details'],
                language_code
            )

    def test_filter_by_language_code_knowledge_linked_content(self):
        # assumed linked content was published already
        linked_content = KnowledgeFactory(
            publish_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
        feed_content = TipsOfTheDayFactory(
            luxury_culture_id=None,
            knowledge_id=linked_content
        )

        for language in self.app_languages:
            TipsOfTheDayTranslationFactory(
                tips_of_the_day=feed_content,
                language=language
            )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=feed_content,
            video_title=None,
        )

        expected_data = list(
            self._default_filter_queryset().values('id', 'type', 'tips_of_the_day_id')
        )

        for language in self.app_languages:
            language_code = language.code
            response = self.client.get(
                self.url,
                data={
                    'include': 'more_details',
                    'user_group_id': self.user.user_group_id.id,
                    'language_code': language_code,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )
            self._assert_single_feed_list(
                expected_data, response.data
            )
            self._assert_content_for_language_code(
                feed_content,
                linked_content,
                response.data[0]['more_details'],
                language_code
            )


class TestFeedsFilterByCategory(BaseAPITestCase):
    """
    Test api endpoint /api/v2/feeds/
    """
    fixtures = ['tags']

    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v2:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestFeedsFilterByCategory, self).setUp()

        self.server_time = datetime.datetime.utcnow()

        self.assertEqual(0, Feed.objects.count())
        self._feed_types()

    @mock_s3_deprecated
    def tearDown(self):
        super(TestFeedsFilterByCategory, self).tearDown()

    def _feed_types(self):
        self.create_s3_buckets()

        self.knowledge = KnowledgeFactory()
        self.luxury_culture = LuxuryCultureFactory()
        # - - - - - - -
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user
        )
        self.feed_1 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result
        )
        self.feed_10 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        )
        self.feed_pinned = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=KnowledgeFactory(),
            user_group_id=self.user.user_group_id,
            is_pinned=True,
        )
        # - - - - - - - - - - - - -
        # TIPS_OF_THE_DAY_TYPE
        # - - - - - - - - - - - - -
        # feed is pre-generated via worker (checknewcontent)
        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            user_group_id=self.user.user_group_id,
            tips_of_the_day_id=TipsOfTheDayFactory(
                knowledge_id=None,
                luxury_culture_id=None
            ),
        )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            user_group_id=self.user.user_group_id,
            tips_of_the_day_id=TipsOfTheDayFactory(
                knowledge_id=KnowledgeFactory(
                    publish_date=self.server_time - datetime.timedelta(
                        hours=self.user.user_group_id.timezone
                    )
                ),
                luxury_culture_id=None
            ),
        )

        FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            user_group_id=self.user.user_group_id,
            tips_of_the_day_id=TipsOfTheDayFactory(
                luxury_culture_id=LuxuryCultureFactory(
                    publish_date=self.server_time - datetime.timedelta(
                        hours=self.user.user_group_id.timezone
                    )
                ),
                knowledge_id=None
            ),
        )

        # - - - - - - -
        self.user_level_up_log = UserLevelUpLogFactory(
            user_id=self.user
        )
        self.feed_3 = FeedFactory(
            type=Feed.COLLEAGUE_LEVEL_UP_TYPE,
            user_level_up_log_id=self.user_level_up_log,
            user_id=self.user
        )
        self.feed_30 = FeedFactory(
            type=Feed.COLLEAGUE_LEVEL_UP_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.feed_4 = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user
        )
        # - - - - - - - - - - - - -
        # NEW_CONTENT_AVAILABLE_TYPE
        # - - - - - - - - - - - - -
        # feed is pre-generated via worker (checknewcontent)
        brand_tag = Tag.objects.get(text='brand')
        market_tag = Tag.objects.get(text='market')
        other_tag = TagFactory(text='unbranded')

        # tagged as 'Brand' (for Knowledge)
        knowledge_1 = KnowledgeFactory(
            expiry_date=self.server_time + datetime.timedelta(
                days=5
            )
        )
        knowledge_1.tags.add(brand_tag)
        self.feed_knowledge_1 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_1,
            user_id=self.user
        )

        # tagged as 'Unbranded'
        knowledge_2 = KnowledgeFactory(
            expiry_date=self.server_time + datetime.timedelta(
                days=1
            )
        )
        knowledge_2.tags.add(other_tag)
        self.feed_knowledge_2 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_2,
            user_id=self.user
        )

        # tagged as 'Brand' (for Knowledge)
        knowledge_3 = KnowledgeFactory(
            expiry_date=self.server_time + datetime.timedelta(
                days=1
            )
        )
        knowledge_3.tags.add(brand_tag)
        self.feed_knowledge_3 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_3,
            user_id=self.user
        )

        # tagged as 'Market' (for Luxury Culture)
        luxury_culture_1 = LuxuryCultureFactory()
        luxury_culture_1.tags.add(market_tag)
        self.feed_luxury_culture_1 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=luxury_culture_1,
            user_id=self.user
        )

        # tagged as 'Unbranded'
        luxury_culture_2 = LuxuryCultureFactory()
        luxury_culture_2.tags.add(other_tag)
        self.feed_luxury_culture_2 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=luxury_culture_2,
            user_id=self.user
        )

        # tagged as 'Market' (for Luxury Culture)
        luxury_culture_3 = LuxuryCultureFactory()
        luxury_culture_3.tags.add(market_tag)
        self.feed_luxury_culture_3 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=luxury_culture_3,
            user_id=self.user
        )
        # - - - - - - -
        self.user_achievement_group = UserAchievementGroupFactory()
        self.feed_6 = FeedFactory(
            type=Feed.UPDATED_RANKING_AVAILABLE_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.video = VideoFactory(
            title='video-title',
            image_url='video-image.jpg',
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        # - - - - - - - - - - - - -
        # NEW_POSTED_MEDIA_TYPE
        # - - - - - - - - - - - - -
        # a feed is pre-generated for uploader after created the model
        self.media = MediaFactory(
            user=self.user
        )
        MediaResourceFactory(
            media=self.media
        )
        # more feeds
        for index in range(5):
            FeedFactory(
                type=Feed.NEW_POSTED_MEDIA_TYPE,
                model_id=self.media.id,
                user_id=self.user
            )
        # - - - - - - -
        self.feed_9 = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.user
        )

    def _default_filter_queryset(self):
        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[
                Feed.COLLEAGUE_LEVEL_UP_TYPE,
                Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                Feed.UPDATED_RANKING_AVAILABLE_TYPE,
                Feed.NEW_POSTED_VIDEO_TYPE,
                Feed.EVALUATION_REMINDER_TYPE
            ],
        ).filter_evaluation_reminders(
            self.user
        )

        for knowledge in [
            self.feed_knowledge_1,
            self.feed_knowledge_2,
            self.feed_knowledge_3
        ]:
            self.assertTrue(
                queryset.filter(id=knowledge.id).exists()
            )

        for luxury_culture in [
            self.feed_luxury_culture_1,
            self.feed_luxury_culture_2,
            self.feed_luxury_culture_3
        ]:
            self.assertTrue(
                queryset.filter(id=luxury_culture.id).exists()
            )

        return queryset

    def test_list_filter_by_community(self):
        queryset = self._default_filter_queryset().filter(
            type=Feed.NEW_POSTED_MEDIA_TYPE
        ).exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).distinct().order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'category': CategoryType.COMMUNITY,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)

    def test_list_filter_by_brand(self):
        """
        For Knowledge contents
        """
        tag_cases = ['brand', 'BRAND', 'Brand']

        for tag_name in tag_cases:
            queryset = self._default_filter_queryset().filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE
            ).filter_contents_with_tags(
                [tag_name]
            ).exclude(
                Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
                ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
                 (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
            ).order_by('-id')
            expected_data = list(queryset.values('id'))

            response = self.client.get(
                self.url,
                data={
                    'user_group_id': self.user.user_group_id.id,
                    'category': CategoryType.BRAND,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )

            response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
            self.assertEqual(len(expected_data), len(response.data))
            self.assertDictEqualRecursive(expected_data, response_sorted)

    def test_list_filter_by_market(self):
        """
        For Luxury Culture contents
        """
        tag_cases = ['market', 'MARKET', 'Market']

        for tag_name in tag_cases:
            queryset = self._default_filter_queryset().filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE
            ).filter_contents_with_tags(
                [tag_name]
            ).exclude(
                Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
                ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
                 (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
            ).order_by('-id')
            expected_data = list(queryset.values('id'))

            response = self.client.get(
                self.url,
                data={
                    'user_group_id': self.user.user_group_id.id,
                    'category': CategoryType.MARKET,
                },
                HTTP_X_AUTH_TOKEN=self.user.token,
            )
            self.assertEqual(
                status.HTTP_200_OK,
                response.status_code
            )

            response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
            self.assertEqual(len(expected_data), len(response.data))
            self.assertDictEqualRecursive(expected_data, response_sorted)

    def test_list_filter_by_unread(self):
        queryset = self._default_filter_queryset().filter(
            type__in=[
                Feed.NEW_CONTENT_AVAILABLE_TYPE,
                Feed.NEW_POSTED_MEDIA_TYPE,
                Feed.TIPS_OF_THE_DAY_TYPE
            ]
        ).exclude_read_contents(
            self.user
        ).exclude(
            Q(type=Feed.NEW_CONTENT_AVAILABLE_TYPE) &
            ((Q(knowledge_id__expiry_date__isnull=True) & Q(luxury_culture_id__isnull=True)) |
             (Q(luxury_culture_id__expiry_date__isnull=True) & Q(knowledge_id__isnull=True)))
        ).order_by('-id')
        expected_data = list(queryset.values('id'))

        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
                'category': CategoryType.UNREAD,
            },
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code
        )

        response_sorted = sorted(response.data, key=lambda k: k['id'], reverse=True)
        self.assertEqual(len(expected_data), len(response.data))
        self.assertDictEqualRecursive(expected_data, response_sorted)
