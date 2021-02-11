import requests_mock
import random

from datetime import datetime, timedelta
from django.conf import settings

import requests_mock

from PoleLuxe.tests.base import BaseTestCase
from PoleLuxe.models import (
    Feed,
    Media,
    ReadFeed
)
from PoleLuxe.factories import (
    FeedFactory,
    KnowledgeFactory,
    LuxuryCultureFactory,
    MediaFactory,
    MediaResourceFactory,
    TagFactory,
    TipsOfTheDayFactory,
    UserGroupFactory,
    UserFactory,
    ReadFeedFactory,
    DailyChallengeFactory,
    DailyChallengeResultFactory,
)


class TestFeedQuerySet(BaseTestCase):
    def setUp(self):
        super(TestFeedQuerySet, self).setUp()

        self.queryset = Feed.objects.all()

        self.utc_date = datetime.utcnow()
        self.expiry_diff = timedelta(hours=24)

        def expired(timezone, expiry_diff=self.expiry_diff):
            local_date = self.utc_date + timedelta(hours=timezone)
            expiry_date = self.utc_date - expiry_diff
            return local_date.date() > expiry_date.date()

        self.timezone_expiry = (
            (14, lambda: expired(14)),
            (13, lambda: expired(13)),
            (12, lambda: expired(12)),
            (11, lambda: expired(11)),
            (10, lambda: expired(10)),
            (9, lambda: expired(9)),
            (8, lambda: expired(8)),
            (7, lambda: expired(7)),
            (6, lambda: expired(6)),
            (5, lambda: expired(5)),
            (4, lambda: expired(4)),
            (3, lambda: expired(3)),
            (2, lambda: expired(2)),
            (1, lambda: expired(1)),
            (0, lambda: expired(0)),
            (-1, lambda: expired(-1)),
            (-2, lambda: expired(-2)),
            (-3, lambda: expired(-3)),
            (-4, lambda: expired(-4)),
            (-5, lambda: expired(-5)),
            (-6, lambda: expired(-6)),
            (-7, lambda: expired(-7)),
            (-8, lambda: expired(-8)),
            (-9, lambda: expired(-9)),
            (-10, lambda: expired(-10)),
            (-11, lambda: expired(-11)),
            (-12, lambda: expired(-12))
        )

    def testExcludeExpiredTipsOfTheDay(self):
        active_tips = []
        expired_tips = []

        for _ in range(5):
            active_tips.append(
                TipsOfTheDayFactory(
                    publish_date=self.utc_date,
                    expiry_date=self.utc_date + self.expiry_diff
                )
            )

        for _ in range(3):
            expired_tips.append(
                TipsOfTheDayFactory(
                    publish_date=self.utc_date - self.expiry_diff,
                    expiry_date=self.utc_date - self.expiry_diff
                )
            )

        all_tips = active_tips + expired_tips
        for tip in all_tips:
            FeedFactory(
                type=Feed.TIPS_OF_THE_DAY_TYPE,
                tips_of_the_day_id=tip
            )

        queryset = self.queryset.all()
        self.assertEqual(queryset.count(), len(all_tips))

        for tz, expiry_check in self.timezone_expiry:
            queryset = self.queryset.exclude_expired_tips_of_the_day(
                self.utc_date,
                tz
            )
            actual = queryset.count() == len(active_tips)
            expired = expiry_check()
            self.assertEqual(
                actual,
                expired,
                msg='Timezone: {} - Expected {}, got {}'.format(
                    tz,
                    expired,
                    actual
                )
            )

    def testExcludeExpiredTipsKnowledge(self):
        active_knowledges = []
        expired_knowledges = []

        for _ in range(5):
            active_knowledges.append(
                KnowledgeFactory(
                    publish_date=self.utc_date,
                    expiry_date=self.utc_date + self.expiry_diff
                )
            )

        for _ in range(3):
            expired_knowledges.append(
                KnowledgeFactory(
                    publish_date=self.utc_date - self.expiry_diff,
                    expiry_date=self.utc_date - self.expiry_diff
                )
            )

        all_knowledges = active_knowledges + expired_knowledges
        for knowledge in all_knowledges:
            FeedFactory(
                type=Feed.TIPS_OF_THE_DAY_TYPE,
                tips_of_the_day_id=TipsOfTheDayFactory(
                    publish_date=self.utc_date,
                    expiry_date=self.utc_date + self.expiry_diff,
                    knowledge_id=knowledge,
                )
            )

        queryset = self.queryset.all()

        # Every knowledge is attach to a tip, there tips count should be equal
        # to knowledges count.
        self.assertEqual(queryset.count(), len(all_knowledges))

        for tz, expiry_check in self.timezone_expiry:
            queryset = self.queryset.exclude_expired_tips_knowledge(
                self.utc_date,
                tz
            )

            # Every knowledge is attach to a tip, therefore active tips count
            # should be equal to active knowledges count.
            actual = queryset.count() == len(active_knowledges)
            expired = expiry_check()

            self.assertEqual(
                actual,
                expired,
                msg='Timezone: {} - Expected {}, got {}'.format(
                    tz,
                    expired,
                    actual
                )
            )

    def testExcludeExpiredTipsLuxuryCulture(self):
        active_luxury_cultures = []
        expired_luxury_cultures = []

        for _ in range(5):
            active_luxury_cultures.append(
                LuxuryCultureFactory(
                    publish_date=self.utc_date,
                    expiry_date=self.utc_date + self.expiry_diff
                )
            )

        for _ in range(3):
            expired_luxury_cultures.append(
                LuxuryCultureFactory(
                    publish_date=self.utc_date - self.expiry_diff,
                    expiry_date=self.utc_date - self.expiry_diff
                )
            )

        all_luxury_cultures = active_luxury_cultures + expired_luxury_cultures
        for luxury_culture in all_luxury_cultures:
            FeedFactory(
                type=Feed.TIPS_OF_THE_DAY_TYPE,
                tips_of_the_day_id=TipsOfTheDayFactory(
                    publish_date=self.utc_date,
                    expiry_date=self.utc_date + self.expiry_diff,
                    luxury_culture_id=luxury_culture,
                )
            )

        queryset = self.queryset.all()

        # Every luxury culture is attach to a tip, there tips count should
        # be equal to luxury cultures count.
        self.assertEqual(queryset.count(), len(all_luxury_cultures))

        for tz, expiry_check in self.timezone_expiry:
            queryset = self.queryset.exclude_expired_tips_luxury_culture(
                self.utc_date,
                tz
            )

            # Every luxury culture is attach to a tip, therefore active
            # tips count should be equal to active luxury cultures count.
            actual = queryset.count() == len(active_luxury_cultures)
            expired = expiry_check()

            self.assertEqual(
                actual,
                expired,
                msg='Timezone: {} - Expected {}, got {}'.format(
                    tz,
                    expired,
                    actual
                )
            )

    @requests_mock.mock()
    def test_expired_completed_daily_challenge(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        dc = DailyChallengeFactory(publish_date=self.utc_date - self.expiry_diff)
        dcr = DailyChallengeResultFactory(daily_challenge_id=dc)

        user = UserFactory()

        feed = FeedFactory(
            type=Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
            daily_challenge_result_id=dcr,
            user_id=user
        )
        # check if feed in db
        self.assertEqual(1, self.queryset.filter(id=feed.id).count())

        for tz, expiry_check in self.timezone_expiry:
            queryset = self.queryset.filter(id=feed.id).exclude_expired_daily_challenge(
                self.utc_date,
                tz
            )

            # if expired query should not return anything
            actual = queryset.count() == 0
            expired = expiry_check()
            self.assertEqual(
                actual,
                expired,
                msg='Timezone: {} - Expected {}, got {}'.format(
                    tz,
                    expired,
                    actual
                )
            )
            # test in `get_general` filter
            actual = Feed.objects\
                         .get_general(user, user.user_group_id, tz) \
                         .filter(id=feed.id) \
                         .count() == 0
            self.assertEqual(
                actual,
                expired,
                msg='Timezone: {} - Expected {}, got {}'.format(
                    tz,
                    expired,
                    actual
                )
            )

    def test_filter_knowledge_with_tags(self):
        tags = [
            TagFactory(text='tag1'),
            TagFactory(text='tag2')
        ]

        for _ in range(5):
            index = random.randint(0, len(tags) - 1)
            knowledge = KnowledgeFactory()
            knowledge.tags.add(tags[index])

            FeedFactory(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
                knowledge_id=knowledge
            )

        tag_cases = [
            ['tag1'], ['TAG1'],
            ['tag2'], ['TAG2'],
            ['tag1', 'tag2'], ['TAG1', 'TAG2']
        ]
        for tag in tag_cases:
            lower_case_tags = map(lambda i: i.lower(), tag)
            expected_data = self.queryset.all().filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
                knowledge_id__tags__text__in=lower_case_tags
            ).values('id').order_by('-id')

            queryset = self.queryset.order_by('-id').filter_contents_with_tags(tag).values('id')

            self.assertEqual(len(expected_data), queryset.count())
            for index, item in enumerate(queryset):
                self.assertEqual(
                    expected_data[index]['id'],
                    queryset[index]['id']
                )

    def test_filter_luxury_culture_with_tags(self):
        tags = [
            TagFactory(text='tag1'),
            TagFactory(text='tag2')
        ]

        for _ in range(5):
            index = random.randint(0, len(tags) - 1)
            luxury_culture = LuxuryCultureFactory()
            luxury_culture.tags.add(tags[index])

            FeedFactory(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
                luxury_culture_id=luxury_culture
            )

        tag_cases = [
            ['tag1'], ['TAG1'],
            ['tag2'], ['TAG2'],
            ['tag1', 'tag2'], ['TAG1', 'TAG2']
        ]
        for tag in tag_cases:
            lower_case_tags = map(lambda i: i.lower(), tag)
            expected_data = self.queryset.all().filter(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
                luxury_culture_id__tags__text__in=lower_case_tags
            ).values('id').order_by('-id')

            queryset = self.queryset.order_by('-id').filter_contents_with_tags(tag).values('id')
            self.assertEqual(len(expected_data), queryset.count(), tag)
            for index, item in enumerate(queryset):
                self.assertEqual(
                    expected_data[index]['id'],
                    queryset[index]['id']
                )

    @requests_mock.mock()
    def test_exclude_read_contents(self, m):
        m.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)

        for _ in range(5):
            luxury_culture = LuxuryCultureFactory()
            FeedFactory(
                type=Feed.NEW_CONTENT_AVAILABLE_TYPE,
                luxury_culture_id=luxury_culture
            )

        feeds = Feed.objects.all().order_by('-id')
        ReadFeedFactory(
            feed=feeds[0],
            user=self.user
        )
        ReadFeedFactory(
            feed=feeds[1],
            user=self.user
        )
        ReadFeedFactory(
            feed=feeds[2],
            user=self.user
        )

        user_1 = UserFactory()
        ReadFeedFactory(
            feed=feeds[3],
            user=user_1
        )
        ReadFeedFactory(
            feed=feeds[4],
            user=user_1
        )

        user_2 = UserFactory()

        user_cases = [self.user, user_1, user_2]
        for user in user_cases:
            read_feed_ids = ReadFeed.objects.filter(
                user=user
            ).values_list('feed', flat=True)
            expected_data = self.queryset.all().exclude(
                id__in=list(read_feed_ids)
            ).values('id').order_by('-id')

            queryset = self.queryset.order_by('-id').exclude_read_contents(
                user=user
            ).values('id')

            self.assertEqual(len(expected_data), queryset.count())
            for index, item in enumerate(queryset):
                self.assertEqual(
                    expected_data[index]['id'],
                    queryset[index]['id']
                )

    def test_exclude_incomplete_media(self):
        media_1 = MediaFactory(
            user=self.user
        )
        MediaResourceFactory(
            media=media_1
        )
        self.feed_1 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=media_1.id,
            user_id=self.user
        )

        self.media_text_type = MediaFactory(
            user=self.user,
            type=Media.TEXT_TYPE,
            is_active=True
        )
        self.feed_2 = FeedFactory(
            type=Feed.NEW_POSTED_MEDIA_TYPE,
            model_id=self.media_text_type.id,
            user_id=self.user
        )

        queryset = self.queryset.exclude_incomplete_media()
        self.assertTrue(queryset.filter(id=self.feed_1.id).exists())
        self.assertTrue(queryset.filter(id=self.feed_2.id).exists())


class ExpiredContentsTestCase(BaseTestCase):
    @requests_mock.mock()
    def test_expired_contents(self, req_mock):
        req_mock.post(settings.UNIQUE_VALIDATOR_ENDPOINT, json=True)
        publish_date = datetime.today()
        expiry_date = (publish_date - timedelta(days=10)).date()

        user_group = UserGroupFactory()

        content_dataset = [
            {
                'factory': KnowledgeFactory,
                'feed_accessor_name': 'knowledge_id'
            },
            {
                'factory': LuxuryCultureFactory,
                'feed_accessor_name': 'luxury_culture_id'
            }
        ]

        active_contents = []
        for content_data in content_dataset:
            factory = content_data.pop('factory')
            feed_accessor_name = content_data.pop('feed_accessor_name')
            feed_data = {
                'type': Feed.NEW_CONTENT_AVAILABLE_TYPE,
                'user_group_id': user_group,
            }
            content_data['publish_date'] = publish_date

            content = factory(**content_data)
            feed_data[feed_accessor_name] = content
            FeedFactory(**feed_data)
            active_contents.append(content.pk)

            # create expired content
            content = factory(expiry_date=expiry_date, **content_data)
            feed_data[feed_accessor_name] = content
            FeedFactory(**feed_data)

        feeds = Feed.objects.get_general(
            UserFactory(),
            user_group.pk,
            user_group.timezone,
        )

        # The returned feeds should only be half of the created ones,
        # but note that the number of feeds created are twice as many
        # as the dataset, so we don't need to divide the latter.
        self.assertEqual(len(content_dataset), feeds.count())

        # make sure expired dates are not included in the feeds
        self.assertTrue(feeds.filter(
            knowledge_id__isnull=False,     # knowledge feed
            knowledge_id__in=active_contents
        ))
        self.assertTrue(feeds.filter(
            luxury_culture_id__isnull=False,     # luxury culture feed
            luxury_culture_id__in=active_contents
        ))
