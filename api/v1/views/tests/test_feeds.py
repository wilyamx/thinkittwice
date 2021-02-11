import requests_mock
import datetime
import random
import tempfile

from boto.s3.key import Key
from moto import mock_s3_deprecated
from PIL import Image

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.db.models import Q

from rest_framework.settings import api_settings
from rest_framework import status

from PoleLuxe.factories import (
    AppLanguageFactory,
    DailyChallengeFactory,
    DailyChallengeResultFactory,
    FeedFactory,
    KnowledgeFactory,
    LuxuryCultureFactory,
    MediaFactory,
    MediaResourceFactory,
    QuizFeedFactory,
    TagFactory,
    TipsOfTheDayFactory,
    TipsOfTheDayTranslationFactory,
    UserAchievementGroupFactory,
    UserFactory,
    UserKnowledgeQuizResultFactory,
    UserLevelUpLogFactory,
    VideoFactory,
)
from PoleLuxe.factories.pinned import PinnedTagFactory

from PoleLuxe.models import (
    Feed,
    Media,
    Tag,
    UserGroup,
    UserKnowledgeQuizResult,
)

from PoleLuxe.constants import CategoryType
from PoleLuxe import translations

from .. import (
    DetailFeedSerializer,
    MediaForFeedSerializer,
)
from api.tests.base import BaseAPITestCase
from api.tests.mixins import APIInactiveAuthenticatedTest


class TestLegacyFeeds(APIInactiveAuthenticatedTest, BaseAPITestCase):
    """
    Test api endpoint /api/v1/feeds
    """
    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v1:feeds')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestLegacyFeeds, self).setUp()

        self.server_time = datetime.datetime.utcnow()

    @mock_s3_deprecated
    def tearDown(self):
        super(TestLegacyFeeds, self).tearDown()

    @mock_s3_deprecated
    def test_get_single_feed_types(self):
        """
        Test get single feed depending on Feed.type.
        """
        self.create_s3_buckets()
        # - - - - - - -
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user,
            daily_challenge_id=DailyChallengeFactory(
                publish_date=self.server_time
            )
        )
        self.feed_1 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result
        )
        self.feed_10 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        )
        # - - - - - - -
        self.tips_of_the_day = TipsOfTheDayFactory(
            luxury_culture_id=None,
            knowledge_id=None
        )
        self.feed_2 = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=self.tips_of_the_day
        )
        self.feed_20 = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE
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
        self.knowledge = KnowledgeFactory()
        self.feed_4 = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user
        )
        self.feed_40 = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.luxury_culture = LuxuryCultureFactory()
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
        self.feed_50 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
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
        # - - - - - - -
        self.media = MediaFactory(
            user=self.user
        )
        self.feed_8 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=self.media.id,
            user_id=self.user
        )
        self.feed_81 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            user_id=self.user
        )
        # - - - - - - -
        self.feed_9 = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.user
        )
        # - - - - - - -
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
                'type': Feed.TIPS_OF_THE_DAY_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_20,
                'valid': False,
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
                'type': Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_40,
                'valid': False,
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
                'type': Feed.NEW_CONTENT_AVAILABLE_TYPE,
                'user_group_id': self.user.user_group_id.id,
                'feed': self.feed_50,
                'valid': False,
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

            if item['valid']:
                self.assertDictEqualRecursive(
                    {'success': True},
                    response.data,
                )

                if item['allow_empty_results']:
                    self.assertEqual(0, len(response.data['feeds']))
                else:
                    self.assertEqual(status.HTTP_200_OK,
                                     response.status_code,
                                     msg='Response error status {} from case index {}.'.format(
                                         response.status_code,
                                         index))
                    self.assertTrue('feeds' in response.data)
                    self.assertEqual(1, len(response.data['feeds']),
                                     msg='Expected 1 result but got {} from case index {}.'.format(
                                         len(response.data['feeds']), index))
                    self.assertDictEqualRecursive(
                        {
                            'id': item['feed'].id,
                            'type': item['feed'].type,
                        },
                        response.data['feeds'][0])
            else:
                self.assertDictEqualRecursive(
                    {'success': False}, response.data)
                self.assertEqual(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    response.status_code,
                    msg='Expect error status from case index {} but got {} status.'.format(
                        index, response.status_code)
                )

    @mock_s3_deprecated
    @requests_mock.mock()
    def test_get_feeds_filter_exclude_contents(self, m):
        """
        Test get feeds except expired contents.
        """
        self.create_s3_buckets()
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)

        self.other_user = UserFactory(language=self.user.language)
        # - - - - - - -
        self.daily_challenge = DailyChallengeFactory(
            publish_date=self.server_time
        )
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user,
            daily_challenge_id=self.daily_challenge
        )
        self.feed_1 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result,
            user_id=self.user,
        )
        # - - - - - - - - - - - - - - - - - - - - - - - - - -
        # EXCLUDED BY::exclude_other_user_daily_challenge
        # - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.daily_challenge = DailyChallengeFactory(
            publish_date=self.server_time
        )
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.other_user,
            daily_challenge_id=self.daily_challenge
        )
        self.feed_1_exclude = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result,
            user_id=self.other_user,
        )
        # - - - - - - -
        # no knowledge_id
        self.feed_2 = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=TipsOfTheDayFactory(
                knowledge_id=None,
            ),
        )

        # already published
        published_date = datetime.datetime.utcnow() + datetime.timedelta(
            hours=self.user.user_group_id.timezone)
        self.feed_21 = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=TipsOfTheDayFactory(
                knowledge_id__publish_date=published_date -
                datetime.timedelta(days=5),
                luxury_culture_id=None
            ),
        )
        # - - - - - - - - - - - - - - - - - - - - - - -
        # EXCLUDED BY::exclude_unpublished_knowledge
        # - - - - - - - - - - - - - - - - - - - - - - -
        self.tips_of_the_day_exclude = TipsOfTheDayFactory(
            # make it explicit that the knowledge is
            # yet to be published
            knowledge_id=KnowledgeFactory(
                publish_date=published_date + datetime.timedelta(days=5)
            ),
            luxury_culture_id=None
        )
        self.feed_2_exclude = FeedFactory(
            type=Feed.TIPS_OF_THE_DAY_TYPE,
            tips_of_the_day_id=self.tips_of_the_day_exclude,
        )
        # - - - - - - -
        self.user_level_up_log = UserLevelUpLogFactory(
            user_id=self.user
        )
        self.feed_3 = FeedFactory(
            type=Feed.COLLEAGUE_LEVEL_UP_TYPE,
            user_level_up_log_id=self.user_level_up_log,
            user_id=self.user,
        )
        # - - - - - - - - - - - - - - - - - - - - - - - - - -
        # EXCLUDED BY::added content type to excluded_types
        # - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.knowledge = KnowledgeFactory()
        self.feed_4_exclude = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user,
        )
        # - - - - - - -
        self.luxury_culture = LuxuryCultureFactory()
        self.feed_5 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user,
        )
        self.feed_51 = FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=self.luxury_culture,
            user_id=self.user
        )
        # - - - - - - -
        self.user_achievement_group = UserAchievementGroupFactory(
            user_group_id=self.user.user_group_id
        )
        self.feed_6 = FeedFactory(
            type=Feed.UPDATED_RANKING_AVAILABLE_TYPE,
            user_id=self.user,
        )
        # - - - - - - -
        self.video = VideoFactory(
            title='video-title',
            image_url='video-image.jpg',
            user_id=self.user,
            user_group_id=self.user.user_group_id
        )
        # - - - - - - -
        self.media = MediaFactory(
            user=self.user
        )
        MediaResourceFactory(media=self.media)
        self.feed_8 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=self.media.id,
            user_id=self.user,
        )
        # - - - - - - -
        self.user.django_user.user_permissions.add(
            Permission.objects.get(codename='add_evaluation')
        )
        self.feed_9 = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.user,
        )
        # - - - - - - - - - - - - - - - - - - - - - -
        # EXCLUDED BY::filter_evaluation_reminders
        # - - - - - - - - - - - - - - - - - - - - - -
        self.other_user.django_user.user_permissions.add(
            Permission.objects.get(codename='add_evaluation')
        )
        self.feed9_created_at = (datetime.datetime.utcnow() -
                                 datetime.timedelta(days=settings.EVALUATION_REMINDER_DAYS_GAP))
        self.feed_9_exclude = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.other_user,
        )
        self.feed_9_exclude.created_at = self.feed9_created_at - \
            datetime.timedelta(days=5)
        self.feed_9_exclude.save()
        # - - - - - - -
        expected_filtered_feeds_queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
        ).filter_evaluation_reminders(self.user)

        expected_filtered_feeds = list(map(lambda i: int(i.id),
                                           expected_filtered_feeds_queryset))
        # exclude assertions
        excluded_feeds = [self.feed_1_exclude,
                          self.feed_2_exclude,
                          self.feed_4_exclude,
                          self.feed_9_exclude]
        for index, item in enumerate(excluded_feeds):
            self.assertFalse(
                int(item.id) in expected_filtered_feeds,
                msg='Feed type [{}] should be excluded at index {}.'.format(item.type, index))

        # include assertions
        included_feeds = [self.feed_1,
                          self.feed_2,
                          self.feed_21,
                          self.feed_3,
                          self.feed_5,
                          self.feed_51,
                          self.feed_6,
                          self.feed_9]
        for index, item in enumerate(included_feeds):
            self.assertTrue(
                int(item.id) in expected_filtered_feeds,
                msg='Feed type [{}] should be included at index {}.'.format(item.type, index))
        # - - - - - - -
        response = self.client.get(
            self.url,
            data={
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertDictEqualRecursive(
            {'success': True}, response.data)

        actual_filtered_feeds = list(map(
            lambda i: int(i['id']), response.data['feeds']))

        self.assertEqual(len(expected_filtered_feeds),
                         len(actual_filtered_feeds))
        self.assertDictEqualRecursive(sorted(expected_filtered_feeds),
                                      sorted(actual_filtered_feeds))

    @mock_s3_deprecated
    def test_single_media_feed(self):
        """
        Test get single media feed.
        """

        self.create_s3_buckets()

        media = MediaFactory(
            user=self.user
        )
        MediaResourceFactory(media=media)
        feeds = Feed.objects.filter(
            model=Media.__name__,
            model_id=media.id
        )

        response = self.client.get(
            self.url,
            {
                'feed_id': feeds[0].id,
                'user_group_id': self.user.user_group_id.id
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )

        self.assertEqual(
            {
                'success': True,
                'feeds': [
                    {
                        'id': feeds[0].id,
                        'type': Feed.NEW_POSTED_MEDIA_TYPE,
                        'time_stamp': feeds[0].created_at.strftime(
                            api_settings.DATETIME_FORMAT
                        ),
                        'others': MediaForFeedSerializer(
                            media,
                            context={'user_id': self.user.id}
                        ).data,
                        'ref': {
                            'type': 5,
                            'ref_id': media.id
                        }
                    }
                ]
            },
            dict(response.data)
        )

    @mock_s3_deprecated
    def test_media_feed(self):
        """
        Test get media feed.
        """

        self.create_s3_buckets()

        for _ in range(0, 2):
            media = MediaFactory(
                user=self.user
            )
            MediaResourceFactory(media=media)

        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )

        self.assertEqual(True, response.data['success'])
        self.assertEqual(2, len(response.data['feeds']))

    @mock_s3_deprecated
    def test_media_feeds_with_no_resources(self):
        """
        Check if a media with no resources is not
        included in the results
        """

        self.create_s3_buckets()

        media_set = [
            MediaFactory(user=self.user),
            MediaFactory(user=self.user),
        ]

        # the first one does not have a resource
        MediaResourceFactory(media=media_set[1])

        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token,
        )
        media_with_resources = media_set[1:]
        self.assertTrue(response.data['success'])
        self.assertEqual(
            len(media_with_resources),
            len(response.data['feeds']))

    @mock_s3_deprecated
    def test_no_feeds_for_evaluation_reminders(self):
        """
        Expected no evaluation reminder feed because user has no permission to
        add evaluation.
        """
        self.create_s3_buckets()

        FeedFactory(
            user_group_id=self.user.user_group_id,
            type=Feed.EVALUATION_REMINDER_TYPE
        )

        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token,
        )

        self.assertDictEqualRecursive(
            {
                'success': True,
                'feeds': []
            },
            response.data
        )

    @mock_s3_deprecated
    def test_feeds_for_evaluation_reminders(self):
        """
        Expected to have evaluation reminder feed because user have the
        permission to add evaluation.
        """
        self.create_s3_buckets()

        # Let's add permission to user
        permission = Permission.objects.get(codename='add_evaluation')
        self.user.django_user.user_permissions.add(permission)

        now = datetime.datetime.utcnow()
        days_gap = settings.EVALUATION_REMINDER_DAYS_GAP

        # create feeds with different dates
        feeds = []
        for created_at in [
            now - datetime.timedelta(days=days_gap),
            now,
            now - datetime.timedelta(days=days_gap + 1),
        ]:
            feed = FeedFactory(
                user_group_id=self.user.user_group_id,
                type=Feed.EVALUATION_REMINDER_TYPE,
            )

            feed.created_at = created_at
            feed.save()

            feeds.append(feed)

        feeds.sort(key=lambda feed: feed.created_at, reverse=True)

        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token,
        )

        # make sure there is only one feed for evaluation reminder
        self.assertEqual(
            1,
            len(list(filter(
                lambda feed: feed['type'] == Feed.EVALUATION_REMINDER_TYPE,
                response.data['feeds'],
            )))
        )

        self.assertDictEqualRecursive(
            {
                'success': True,
                'feeds': [
                    {
                        'type': Feed.EVALUATION_REMINDER_TYPE,
                        'others': {
                            'title': 'Evaluation Reminder',
                            'content': translations.TRANS_EVALUATION_REMINDER[
                                settings.DEFAULT_LANGUAGE_CODE
                            ]
                        },
                        'ref': {
                            'type': 5,
                            'ref_id': None,
                        },
                        'time_stamp': now.strftime(api_settings.DATETIME_FORMAT)
                    }
                ]
            },
            response.data
        )


class FilteredQuizLegacyFeedsTestCase(BaseAPITestCase):
    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(FilteredQuizLegacyFeedsTestCase, self).setUp()
        self.url = reverse('api-v1:feeds')

        self.feeds = []
        for i in range(0, 2):
            feed = self.create_feed(type=Feed.NEW_CONTENT_AVAILABLE_TYPE)
            self.feeds.append(feed)

        self.excluded_feeds = []
        for i in range(0, 2):
            feed = self.create_feed(type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE)
            self.excluded_feeds.append(feed)

    def test_feeds_total_count(self):
        self.assertEqual(
            len(self.feeds) + len(self.excluded_feeds),
            Feed.objects.count()
        )

    def test_included_feeds(self):
        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )

        expected_data = DetailFeedSerializer(self.feeds, many=True, context={
            'user_id': self.user.id,
            'user_group_id': self.user.user_group_id.id,
            'language_code': self.user.language_id,
        }).data

        # Sort feeds by ID
        response.data['feeds'] = sorted(
            response.data['feeds'],
            key=lambda x: x['id']
        )

        expected_data = sorted(
            expected_data,
            key=lambda x: x['id']
        )

        self.assertEqual(
            {
                'success': True,
                'feeds': expected_data
            },
            response.data
        )

    def create_feed(self, **kwargs):
        kwargs['user_id'] = self.user
        return QuizFeedFactory(**kwargs)


class FilteredMediaLegacyFeedsTestCase(BaseAPITestCase):
    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(FilteredMediaLegacyFeedsTestCase, self).setUp()
        self.url = reverse('api-v1:feeds')

        # initially no feeds
        self.assertEqual(0, Feed.objects.count())

        uploader = self.user
        another_uploader = UserFactory(
            language=self.language,
            user_group_id=self.user.user_group_id
        )

        self.active_media = [
            MediaFactory(user=uploader, is_active=True),
            MediaFactory(user=another_uploader, is_active=True)
        ]
        self.inactive_media = [
            MediaFactory(user=uploader, is_active=False),
            MediaFactory(user=another_uploader, is_active=False),
        ]

        for media in self.active_media:
            MediaResourceFactory(media=media)
        for media in self.active_media:
            MediaResourceFactory(media=media)

        # media feed to uploader for each create of media content
        self.assertEqual(4, Feed.objects.count())

    def test_feeds_total_count(self):
        self.assertEqual(
            len(self.active_media) + len(self.inactive_media),
            Feed.objects.count()
        )

    def test_included_feeds(self):
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

        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )

        # media feed will get context intended for the request user's group
        feeds = Feed.objects.filter(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id__in=[media.id for media in self.active_media],
            user_group_id=self.user.user_group_id
        )

        expected_data = DetailFeedSerializer(
            feeds, many=True, context={
                'user_id': self.user.id,
                'user_group_id': self.user.user_group_id.id,
                'language_code': self.user.language_id,
            }).data

        # Sort feeds by ID
        response.data['feeds'] = sorted(
            response.data['feeds'],
            key=lambda x: x['id']
        )

        self.assertEqual(
            feeds.count(),
            len(response.data['feeds'])
        )
        self.assertEqual(
            {
                'success': True,
                'feeds': expected_data
            },
            response.data
        )


class NewContentLegacyFeedWithImagesFieldTestCase(BaseAPITestCase):
    """
    Test if `images` field is included in the response.
    """
    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(NewContentLegacyFeedWithImagesFieldTestCase, self).setUp()
        self.url = reverse('api-v1:feeds')

        # We only test with knowledge. It doesn't matter if it is knowledge or
        # luxury culture anyway.
        FeedFactory(
            knowledge_id=KnowledgeFactory(),
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            user_id=self.user
        )

    def test_images_field_included(self):
        """
        The `images` field will is in `others` field.
        """
        response = self.client.get(
            self.url,
            {
                'user_group_id': self.user.user_group_id.id,
            },
            format='json',
            HTTP_X_AUTH_TOKEN=self.user.token
        )
        self.assertTrue('images' in response.data['feeds'][0]['others'])


class TestFeeds(BaseAPITestCase):
    """
    Test api endpoint /api/v1/feeds/
    """
    fixtures = ['tags']

    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v1:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestFeeds, self).setUp()

        self.brand_tag = Tag.objects.get(text='brand')
        self.news_tag = Tag.objects.get(text='news')
        self.market_tag = Tag.objects.get(text='market')

        self.server_time = datetime.datetime.utcnow()
        self._feed_types()

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

    @requests_mock.mock()
    def _feed_types(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        self.create_s3_buckets()
        # - - - - - - -
        self.daily_challenge_result = DailyChallengeResultFactory(
            user_id=self.user,
            daily_challenge_id=DailyChallengeFactory(
                publish_date=self.server_time
            )
        )
        self.feed_1 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=self.daily_challenge_result,
        )
        self.feed_10 = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        )
        # - - - - - - -
        self.tips_of_the_day = TipsOfTheDayFactory()
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
        self.knowledge = KnowledgeFactory()
        self.knowledge.tags.add(self.brand_tag)
        self.knowledge.tags.add(self.news_tag)
        self.feed_4 = FeedFactory(
            type=Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            knowledge_id=self.knowledge,
            user_id=self.user
        )
        # - - - - - - -
        self.luxury_culture = LuxuryCultureFactory()
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
        # - - - - - - -
        uploader = UserFactory()
        self.media = MediaFactory(
            user=uploader
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
        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
        ).filter_evaluation_reminders(
            self.user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
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

        # exclude feeds from media text type content
        self.assertFalse(queryset.filter(id=self.feed_82.id).exists())

    def test_list_include_count(self):
        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
        ).filter_evaluation_reminders(
            self.user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
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
                excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
            ).filter_evaluation_reminders(
                self.user
            ).exclude(
                Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
                Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
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

            # exclude feeds from media text type content
            self.assertFalse(queryset.filter(id=self.feed_82.id).exists())

    @requests_mock.mock()
    def test_list_filter_by_new_posted_media_type(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)

        same_group_user = UserFactory(
            user_group_id=self.user.user_group_id
        )

        user = same_group_user
        user_group = user.user_group_id

        queryset = Feed.objects.get_general(
            self.user.id,
            user_group.id,
            user_group.timezone,
            excluded_types=[Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE],
        ).filter_evaluation_reminders(
            self.user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
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
            'api-v1:feed-detail',
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
            'api-v1:feed-detail',
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
            'api-v1:feed-detail',
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
                    index
                )
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


class TestTipsOfTheDayFeedFilterByLanguageCode(BaseAPITestCase):
    """
    Test api endpoint /api/v1/feeds/
    """
    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v1:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestTipsOfTheDayFeedFilterByLanguageCode, self).setUp()

        self.app_languages = [
            AppLanguageFactory(code='CN', name='Simplified Chinese'),
            AppLanguageFactory(code='FR', name='French'),
            AppLanguageFactory(code='JP', name='Japanese'),
            AppLanguageFactory(code='KR', name='Korean'),
            AppLanguageFactory(code='TC', name='Traditional Chinese')
        ]

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

        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
        expected_data = list(
            queryset.values('id', 'type', 'tips_of_the_day_id')
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

        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
        expected_data = list(
            queryset.values('id', 'type', 'tips_of_the_day_id')
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

        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
        expected_data = list(
            queryset.values('id', 'type', 'tips_of_the_day_id')
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

        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).order_by('-id')
        expected_data = list(
            queryset.values('id', 'type', 'tips_of_the_day_id')
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
    Test api endpoint /api/v1/feeds/
    """
    fixtures = ['tags']

    @mock_s3_deprecated
    @requests_mock.mock()
    def setUp(self, m):
        self.url = reverse('api-v1:feed-list')
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        super(TestFeedsFilterByCategory, self).setUp()

        self.server_time = datetime.datetime.utcnow()

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

        # tagged as 'Brand'
        knowledge_1 = KnowledgeFactory()
        knowledge_1.tags.add(brand_tag)
        FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_1,
            user_id=self.user
        )

        # tagged as 'Unbranded'
        knowledge_2 = KnowledgeFactory()
        knowledge_2.tags.add(other_tag)
        FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_2,
            user_id=self.user
        )

        # tagged as 'Market'
        knowledge_3 = KnowledgeFactory()
        knowledge_3.tags.add(market_tag)
        FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            knowledge_id=knowledge_3,
            user_id=self.user
        )

        # tagged as 'Brand'
        luxury_culture_1 = LuxuryCultureFactory()
        luxury_culture_1.tags.add(brand_tag)
        FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=luxury_culture_1,
            user_id=self.user
        )

        # tagged as 'Unbranded'
        luxury_culture_2 = LuxuryCultureFactory()
        luxury_culture_2.tags.add(other_tag)
        FeedFactory(
            type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
            luxury_culture_id=luxury_culture_2,
            user_id=self.user
        )

        # tagged as 'Market'
        luxury_culture_3 = LuxuryCultureFactory()
        luxury_culture_3.tags.add(market_tag)
        FeedFactory(
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
        # feed is pre-generated after created the model
        for _ in range(5):
            media = MediaFactory(
                user=self.user
            )
            MediaResourceFactory(
                media=media
            )
        # - - - - - - -
        self.feed_9 = FeedFactory(
            type=Feed.EVALUATION_REMINDER_TYPE,
            user_id=self.user
        )

    def test_list_filter_by_community(self):
        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[
                Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            ],
        ).filter_evaluation_reminders(
            self.user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).filter(
            type__in=[
                Feed.NEW_POSTED_MEDIA_TYPE
            ]
        ).order_by('-id')
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

        self.assertEqual(
            5,
            len(list(filter(lambda i: i['type'] == Feed.NEW_POSTED_MEDIA_TYPE, response_sorted)))
        )

    def test_list_filter_by_brand(self):
        tag_cases = ['brand', 'BRAND', 'Brand']

        for tag_name in tag_cases:
            queryset = Feed.objects.get_general(
                self.user.id,
                self.user.user_group_id.id,
                self.user.user_group_id.timezone,
                excluded_types=[
                    Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                ],
            ).filter_evaluation_reminders(
                self.user
            ).exclude(
                Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
                Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
            ).filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE
            ).filter_contents_with_tags([tag_name]).order_by('-id')
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
        tag_cases = ['market', 'MARKET', 'Market']

        for tag_name in tag_cases:
            queryset = Feed.objects.get_general(
                self.user.id,
                self.user.user_group_id.id,
                self.user.user_group_id.timezone,
                excluded_types=[
                    Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
                ],
            ).filter_evaluation_reminders(
                self.user
            ).exclude(
                Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
                Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
            ).filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE
            ).filter_contents_with_tags([tag_name]).order_by('-id')
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
        queryset = Feed.objects.get_general(
            self.user.id,
            self.user.user_group_id.id,
            self.user.user_group_id.timezone,
            excluded_types=[
                Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
            ],
        ).filter_evaluation_reminders(
            self.user
        ).exclude(
            Q(type=Feed.NEW_POSTED_MEDIA_TYPE) &
            Q(model_id__in=Media.objects.filter(type=Media.TEXT_TYPE))
        ).filter(
            type__in=[
                Feed.NEW_CONTENT_AVAILABLE_TYPE,
                Feed.NEW_POSTED_MEDIA_TYPE,
                Feed.TIPS_OF_THE_DAY_TYPE
            ]
        ).exclude_read_contents(self.user).order_by('-id')
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
