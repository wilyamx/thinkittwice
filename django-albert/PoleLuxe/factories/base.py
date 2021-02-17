import os
import factory
import random
import tempfile

from django.conf import settings
from factory.django import DjangoModelFactory

from faker import Faker
from PoleLuxe import models
from PoleLuxe.constants import UiApiVersion
from PoleLuxe.helpers.faker import image_faker


class AppLanguageFactory(DjangoModelFactory):
    code = 'EN'
    name = 'English'

    class Meta:
        model = models.AppLanguage
        django_get_or_create = ('code',)


class AppFactory(DjangoModelFactory):
    class Meta:
        model = models.App
        django_get_or_create = ('name',)

    name = factory.Faker('name')
    code = factory.Sequence(lambda n: 'app%d' % n)
    avatar = tempfile.NamedTemporaryFile(
        suffix='.jpg',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)).name
    ios_min_version = '0.0.1'
    android_min_version = '0.0.1'
    ios_last_version = '0.0.1'
    android_last_version = '0.0.1'
    ios_download_url = factory.Faker('url')
    android_download_url = factory.Faker('url')
    alt_android_download_url = factory.Faker('url')
    ios_policy_url = factory.Faker('url')
    android_policy_url = factory.Faker('url')
    apns_cert_file = tempfile.NamedTemporaryFile(
        suffix='.pem',
        dir=os.path.join(settings.BASE_DIR, settings.TEMP_DIR),
        delete=False,
    ).name


class CompanyFactory(DjangoModelFactory):
    name = factory.Faker('company')
    app = factory.SubFactory(AppFactory)

    class Meta:
        model = models.Company
        django_get_or_create = ('name',)


class UserGroupFactory(DjangoModelFactory):
    class Meta:
        model = models.UserGroup

    company_id = factory.SubFactory(CompanyFactory)
    name = factory.Faker('name')
    timezone = 8

    @factory.post_generation
    def reporters(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.reporters.add(user)


class UserJobPositionFactory(DjangoModelFactory):
    name = factory.Faker('job')
    company_id = factory.SubFactory(CompanyFactory)

    class Meta:
        model = models.UserJobPosition
        django_get_or_create = ('name', 'company_id')


class UserDepartmentFactory(DjangoModelFactory):
    name = factory.Faker('word')
    company_id = factory.SubFactory(CompanyFactory)

    class Meta:
        model = models.UserDepartment
        django_get_or_create = ('name', 'company_id')


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Sequence(lambda n: '{}{}'.format(Faker().user_name(), n))
    email = factory.Sequence(lambda n: 'email{}@{}'.format(n, Faker().free_email_domain()))
    password = factory.Faker('password')
    language = factory.SubFactory(AppLanguageFactory)
    token = factory.Faker('sha256')
    active = True
    name = factory.Sequence(lambda n: '{}{}'.format(Faker().name(), n))
    avatar_url = tempfile.NamedTemporaryFile(
        suffix='.jpg',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)).name
    company_id = factory.SubFactory(CompanyFactory)
    user_department_id = factory.SubFactory(UserDepartmentFactory)
    user_position_id = factory.SubFactory(UserJobPositionFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    employment_date = factory.Faker('past_date')
    app_version = UiApiVersion.OLD_UI_API_VERSION
    address_city = factory.Faker('city')
    address_country_code = factory.Faker('country_code', representation='alpha-3')


class CompanyManagerFactory(DjangoModelFactory):
    class Meta:
        model = models.CompanyManager

    company = factory.SubFactory(CompanyFactory)
    manager = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class CompanyOwnerFactory(DjangoModelFactory):
    class Meta:
        model = models.CompanyOwner

    company = factory.SubFactory(CompanyFactory)
    owner = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class ContentManagerFactory(DjangoModelFactory):
    class Meta:
        model = models.company.ContentManager

    company = factory.SubFactory(CompanyFactory)
    manager = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class UserManagerFactory(DjangoModelFactory):
    class Meta:
        model = models.company.UserManager

    company = factory.SubFactory(CompanyFactory)
    manager = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class ProductGroupManagerFactory(DjangoModelFactory):
    class Meta:
        model = models.company.ProductGroupManager

    company = factory.SubFactory(CompanyFactory)
    manager = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class TranslatorFactory(DjangoModelFactory):
    class Meta:
        model = models.company.Translator

    company = factory.SubFactory(CompanyFactory)
    translator = factory.SubFactory(UserFactory)
    language = factory.SubFactory(models.AppLanguage)
    created_at = factory.Faker('date')


class CoachFactory(DjangoModelFactory):
    class Meta:
        model = models.company.Coach

    company = factory.SubFactory(CompanyFactory)
    coach = factory.SubFactory(UserFactory)
    user_group = factory.SubFactory(UserGroupFactory)
    created_at = factory.Faker('date')


class ProductGroupFactory(DjangoModelFactory):
    class Meta:
        model = models.ProductGroup

    name = factory.Sequence(lambda n: '{}{}'.format(Faker().name(), n))
    is_active = True


class KnowledgeFactory(DjangoModelFactory):
    class Meta:
        model = models.Knowledge

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    order = 1
    like_count = 0


class KnowledgeQuizFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeQuiz

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    question = factory.Faker('text')
    image = image_faker(os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR))


class KnowledgeQuizTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeQuizTranslation

    knowledge_quiz = factory.SubFactory(KnowledgeQuizFactory)
    question = factory.Faker('text')
    language = factory.SubFactory(AppLanguageFactory)


class UserKnowledgeQuizResultFactory(DjangoModelFactory):
    class Meta:
        model = models.UserKnowledgeQuizResult

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    user_id = factory.SubFactory(UserFactory)
    result = factory.LazyFunction(lambda: random.random())
    points = factory.Faker('pyint')
    created_at = factory.Faker('date')


class UserKnowledgeResultFactory(DjangoModelFactory):
    class Meta:
        model = models.UserKnowledgeResult

    knowledge = factory.SubFactory(KnowledgeFactory)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class KnowledgeQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeQuizAnswer

    knowledge_quiz_id = factory.SubFactory(KnowledgeFactory)
    answer = factory.Faker('text')
    correct = False


class KnowledgeQuizAnswerTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeQuizAnswerTranslation

    knowledge_quiz_answer = factory.SubFactory(KnowledgeQuizAnswerFactory)
    answer = factory.Faker('text')
    language = factory.SubFactory(AppLanguageFactory)


class KnowledgeCardFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeCard

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    title = factory.Faker('sentence')
    content = factory.Faker('text')
    image_url = image_faker(os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR))


class KnowledgeCardTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeCardTranslation

    knowledge_card = factory.SubFactory(KnowledgeCardFactory)
    language = factory.SubFactory(AppLanguageFactory)


class KnowledgeLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeLikeLog

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class KnowledgeCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeComment

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    knowledge_card_id = factory.SubFactory(KnowledgeCardFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    like_count = 1


class KnowledgeCommentLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeCommentLikeLog

    knowledge_comment_id = factory.SubFactory(KnowledgeCommentFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class LuxuryCultureFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCulture

    title = factory.Faker('sentence')
    image_url = image_faker(os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR))
    description = factory.Faker('text')
    content = factory.Faker('text')
    publish_date = factory.Faker('date_time')
    like_count = 0


class LuxuryCultureQuizFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureQuiz

    luxury_culture = factory.SubFactory(LuxuryCultureFactory)
    question = factory.Faker('text')
    image = image_faker(os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR))


class LuxuryCultureQuizTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureQuizTranslation

    luxury_culture_quiz = factory.SubFactory(LuxuryCultureQuizFactory)
    question = factory.Faker('text')
    language = factory.SubFactory(AppLanguageFactory)


class UserLuxuryCultureQuizResultFactory(DjangoModelFactory):
    class Meta:
        model = models.UserLuxuryCultureQuizResult

    luxury_culture = factory.SubFactory(LuxuryCultureFactory)
    user = factory.SubFactory(UserFactory)
    result = factory.LazyFunction(lambda: random.random())
    points = factory.Faker('pyint')
    created_at = factory.Faker('date')


class LuxuryCultureQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureQuizAnswer

    luxury_culture_quiz = factory.SubFactory(LuxuryCultureFactory)
    answer = factory.Faker('text')
    correct = False


class LuxuryCultureQuizAnswerTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureQuizAnswerTranslation

    luxury_culture_quiz_answer = factory.SubFactory(LuxuryCultureQuizAnswerFactory)
    answer = factory.Faker('text')
    language = factory.SubFactory(AppLanguageFactory)


class LuxuryCultureLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureLikeLog

    luxury_culture_id = factory.SubFactory(LuxuryCultureFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class LuxuryCultureCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureComment

    luxury_culture_id = factory.SubFactory(LuxuryCultureFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    like_count = 1
    created_at = factory.Faker('date')


class LuxuryCultureCommentLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureCommentLikeLog

    luxury_culture_comment_id = factory.SubFactory(LuxuryCultureCommentFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class TipsOfTheDayFactory(DjangoModelFactory):
    class Meta:
        model = models.TipsOfTheDay

    luxury_culture_id = factory.SubFactory(LuxuryCultureFactory)
    knowledge_id = factory.SubFactory(KnowledgeFactory)
    title = factory.Faker('sentence')
    publish_date = factory.Faker('date_time')


class TipsOfTheDayTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.TipsOfTheDayTranslation

    tips_of_the_day = factory.SubFactory(TipsOfTheDayFactory)
    language = factory.SubFactory(AppLanguageFactory)
    title = factory.Faker('sentence')


class DailyChallengeQuizFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeQuiz

    question = factory.Faker('sentence')
    image = tempfile.NamedTemporaryFile(
        suffix='.jpg',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)).name


class DailyChallengeQuizTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeQuizTranslation

    daily_challenge_quiz = factory.SubFactory(DailyChallengeQuizFactory)
    language = factory.SubFactory(AppLanguageFactory)
    question = factory.Faker('sentence')


class DailyChallengeQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeQuizAnswer

    answer = factory.Faker('sentence')
    daily_challenge_quiz_id = factory.SubFactory(DailyChallengeQuizFactory)


class DailyChallengeQuizAnswerTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeQuizAnswerTranslation

    daily_challenge_quiz_answer = factory.SubFactory(DailyChallengeQuizAnswerFactory)
    answer = factory.Faker('text')
    language = factory.SubFactory(AppLanguageFactory)


class DailyChallengeFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallenge

    knowledge_id = factory.SubFactory(KnowledgeFactory)
    luxury_culture_id = factory.SubFactory(LuxuryCultureFactory)
    daily_challenge_quiz_id = factory.SubFactory(DailyChallengeQuizFactory)
    title = factory.Faker('sentence')
    publish_date = factory.Faker('date_time')


class DailyChallengeResultFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeResult

    user_id = factory.SubFactory(UserFactory)
    daily_challenge_id = factory.SubFactory(DailyChallengeFactory)
    result = 0
    level = 0
    points = 0


class UserLevelUpLogFactory(DjangoModelFactory):
    class Meta:
        model = models.UserLevelUpLog

    user_id = factory.SubFactory(UserFactory)
    level = 1
    rank = 1
    trend = 1


class VideoFactory(DjangoModelFactory):
    class Meta:
        model = models.Video

    title = factory.Faker('sentence')
    content = factory.Faker('text')
    image_url = tempfile.NamedTemporaryFile(
        suffix='.jpg',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)).name
    video_url = tempfile.NamedTemporaryFile(
        suffix='.mp4',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)).name
    user_id = factory.SubFactory(UserFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    active_flag = True
    like_count = 0


class FeedFactory(DjangoModelFactory):
    class Meta:
        model = models.Feed

    type = factory.Iterator([
        models.Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        models.Feed.TIPS_OF_THE_DAY_TYPE,
        models.Feed.COLLEAGUE_LEVEL_UP_TYPE,
        models.Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
        models.Feed.NEW_CONTENT_AVAILABLE_TYPE,
        models.Feed.UPDATED_RANKING_AVAILABLE_TYPE,
        models.Feed.NEW_POSTED_VIDEO_TYPE,
        models.Feed.EVALUATION_REMINDER_TYPE,
    ])
    video_title = factory.Faker('text', max_nb_chars=32)
    like_count = 0
    created_at = factory.Faker('date')


class FeedCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.FeedComment

    feed_id = factory.SubFactory(FeedFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    like_count = 1
    created_at = factory.Faker('date')


class FeedCommentLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.FeedCommentLikeLog

    feed_comment_id = factory.SubFactory(FeedCommentFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class QuizFeedFactory(FeedFactory):
    knowledge_id = factory.SubFactory(KnowledgeFactory)


class CheerUpMessageFactory(DjangoModelFactory):
    class Meta:
        model = models.CheerUpMessage

    message = factory.Faker('sentence')
    star = factory.LazyFunction(lambda obj: random.randint(1, 5))
    type = factory.LazyFunction(lambda obj: random.choice([
        models.Feed.COMPLETE_DAILY_CHALLENGE_TYPE,
        models.Feed.TIPS_OF_THE_DAY_TYPE,
        models.Feed.COLLEAGUE_LEVEL_UP_TYPE,
        models.Feed.COLLEAGUE_COMPLETED_QUIZ_TYPE,
        models.Feed.NEW_CONTENT_AVAILABLE_TYPE,
        models.Feed.UPDATED_RANKING_AVAILABLE_TYPE,
        models.Feed.NEW_POSTED_VIDEO_TYPE
    ]))


class MediaFactory(DjangoModelFactory):
    class Meta:
        model = models.Media

    title = factory.Faker('sentence')
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def likes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for like in extracted:
                self.likes.add(like)

    @factory.post_generation
    def product_groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for product_group in extracted:
                self.product_groups.add(product_group)


class VideoCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.VideoComment

    video_id = factory.SubFactory(VideoFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    like_count = 1
    created_at = factory.Faker('date')


class VideoCommentLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.VideoCommentLikeLog

    video_comment_id = factory.SubFactory(VideoCommentFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class MediaCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.MediaComment

    user = factory.SubFactory(UserFactory)
    media = factory.SubFactory(MediaFactory)
    comment = factory.Faker('sentence')


class MediaResourceFactory(DjangoModelFactory):
    class Meta:
        model = models.MediaResource

    media = factory.SubFactory(MediaFactory)
    resource = tempfile.NamedTemporaryFile(
        suffix='.jpg',
        dir=os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)
    ).name
    content_type = 'image/jpeg'


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = models.Notification

    sender = factory.SubFactory(UserFactory)


class NotificationLogFactory(DjangoModelFactory):
    class Meta:
        model = models.NotificationLog

    notification = factory.SubFactory(NotificationFactory)
    user = factory.SubFactory(UserFactory)


class UserRankingFactory(DjangoModelFactory):
    class Meta:
        model = models.UserRanking

    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    rank_no = 1


class LevelPointFactory(DjangoModelFactory):
    class Meta:
        model = models.LevelPoints

    user_level = factory.Faker('pyint')
    point = factory.Faker('pyint')


class LuxuryCultureTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureTranslation

    language = factory.SubFactory(AppLanguageFactory)
    luxury_culture = factory.SubFactory(LuxuryCultureFactory)
    title = factory.Faker('sentence')
    content = factory.Faker('text')


class DailyChallengeTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyChallengeTranslation

    language = factory.SubFactory(AppLanguageFactory)
    daily_challenge_id = factory.SubFactory(DailyChallengeFactory)
    title = factory.Faker('sentence')


class KnowledgeTranslationFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeTranslation

    language = factory.SubFactory(AppLanguageFactory)
    knowledge = factory.SubFactory(KnowledgeFactory)
    title = factory.Faker('sentence')


class LuxuryCultureRatingFactory(DjangoModelFactory):
    class Meta:
        model = models.LuxuryCultureRating

    user = factory.SubFactory(UserFactory)
    luxury_culture = factory.SubFactory(LuxuryCultureFactory)
    star = factory.Faker('pyint')


class KnowledgeRatingFactory(DjangoModelFactory):
    class Meta:
        model = models.KnowledgeRating

    user = factory.SubFactory(UserFactory)
    knowledge = factory.SubFactory(KnowledgeFactory)
    star = factory.Faker('pyint')


class TagFactory(DjangoModelFactory):
    class Meta:
        model = models.Tag

    text = factory.Faker('sentence')


class UserAchievementGroupFactory(DjangoModelFactory):
    class Meta:
        model = models.UserAchievementGroup

    type = factory.Faker('pyint')
    user_group_id = factory.SubFactory(UserGroupFactory)
    company_id = factory.SubFactory(CompanyFactory)
    achievement_position = factory.Faker('pyint')


class UserAchievementFactory(DjangoModelFactory):
    class Meta:
        model = models.UserAchievement

    user_achievement_group = factory.SubFactory(UserAchievementGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    achievement_position = factory.Faker('pyint')
    trend = factory.Faker('pyint')


class UserAchievementGroupCommentFactory(DjangoModelFactory):
    class Meta:
        model = models.UserAchievementGroupComment

    user_achievement_group_id = factory.SubFactory(UserAchievementGroupFactory)
    user_group_id = factory.SubFactory(UserGroupFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    like_count = 1


class UserAchievementGroupCommentLikeLogFactory(DjangoModelFactory):
    class Meta:
        model = models.UserAchievementGroupCommentLikeLog

    user_achievement_group_comment_id = factory.SubFactory(
        UserAchievementGroupCommentFactory)
    user_id = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class ReadFeedFactory(DjangoModelFactory):
    class Meta:
        model = models.ReadFeed

    feed = factory.SubFactory(FeedFactory)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class UserKnowledgeQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.UserKnowledgeQuizAnswer

    answer = factory.SubFactory(KnowledgeQuizAnswerFactory)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class UserDailyChallengeQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.UserDailyChallengeQuizAnswer

    answer = factory.SubFactory(DailyChallengeQuizAnswerFactory)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')


class UserLuxuryCultureQuizAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.user.UserLuxuryCultureQuizAnswer

    answer = factory.SubFactory(LuxuryCultureQuizAnswerFactory)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker('date')
