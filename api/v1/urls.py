from django.conf.urls import include, url

from .views import legacy
from .views import rq_status
from .views import auth

from .views.memsource import memsource_events
from .views.unlike import unlike
from .views.theme import (
    ThemeViewSet,
    ThemeImageViewSet,
    ThemeUploadSignatureView
)
from .views.app import (
    AppUploadSignatureView,
    AppViewSet,
    check_version
)
from .views.media import (
    MediaUploadSignatureView,
    MediaCommentViewSet,
    MediaResourceViewSet,
    MediaViewSet,
)
from .views.luxuryculture import LuxuryCultureUploadSignatureView
from .views.users import (
    UserViewSet,
    UserOwnDetailsViewSet,
    UserRolesViewSet,
    BatchUserCreateTaskViewSet,
    BatchUserCreateTaskUploadSignatureView,
    BatchUserCreateItemViewSet
)
from .views.productgroup import ProductGroupViewSet
from .views.usergroup import UserGroupViewSet
from .views.userjobposition import UserJobPositionViewSet
from .views.userdepartment import UserDepartmentViewSet
from .views.permission import PermissionViewSet
from .views.company import CompanyViewSet, company_analytics_permission
from .views.companyowner import CompanyOwnerViewSet
from .views.companymanager import CompanyManagerViewSet
from .views.userknowledgequizanswer import UserKnowledgeQuizAnswerViewSet
from .views.userluxuryculturequizanswer import UserLuxuryCultureQuizAnswerViewSet
from .views.userdailychallengequizanswer import UserDailyChallengeQuizAnswerViewSet
from .views.readfeed import ReadFeedViewSet
from .views.monthlyquizpoint import MonthlyQuizPointViewSet
from .views.cheerupmessage import CheerUpMessageViewSet
from .views.luxuryculture import (
    LuxuryCultureViewSet,
    LuxuryCultureTranslationViewSet,
)
from .views.luxuryculturequiz import (
    LuxuryCultureQuizViewSet,
    LuxuryCultureQuizTranslationViewSet,
    LuxuryCultureQuizAnswerViewSet,
    LuxuryCultureQuizAnswerTranslationViewSet,
    UserLuxuryCultureQuizResultViewSet,
)
from .views.knowledge import (
    KnowledgeViewSet,
    UserKnowledgeQuizResultViewSet,
    UserKnowledgeResultViewSet,
)
from .views.knowledgetranslation import KnowledgeTranslationViewSet
from .views.knowledgequiz import (
    KnowledgeQuizTranslationViewSet,
    KnowledgeQuizViewSet,
)
from .views.knowledgequizanswer import (
    KnowledgeQuizAnswerViewSet,
    KnowledgeQuizAnswerTranslationViewSet,
)
from .views.knowledgecard import (
    KnowledgeCardViewSet,
    KnowledgeCardUploadSignatureView,
)
from .views.knowledgecardtranslation import KnowledgeCardTranslationViewSet
from .views.tipsoftheday import TipsOfTheDayViewSet, TipsOfTheDayTranslationViewSet
from .views.dailychallenge import DailyChallengeViewSet, DailyChallengeTranslationViewSet
from .views.dailychallengequiz import (
    DailyChallengeQuizViewSet,
    DailyChallengeQuizTranslationViewSet,
)
from .views.dailychallengequizanswer import (
    DailyChallengeQuizAnswerViewSet,
    DailyChallengeQuizAnswerTranslationViewSet,
)
from .views.evaluation import EvaluationViewSet
from .views.rating import KnowledgeRatingViewSet, LuxuryCultureRatingViewSet
from .views.role import RoleViewSet, RolePermissionViewSet
from .views.tag import TagViewSet
from .views.bizcoach import BizCoachUserViewSet
from .views.analytics import ActivityViewSet, SessionViewSet
from .views.bizcoach import BizCoachTagViewSet
from .views.logentry import LogEntryViewSet
from .views.feed import FeedViewSet
from .views.country import CountryViewSet
from .views.zone import ZoneViewSet
from .views import access_levels
from .views.user_region import UserCountriesViewSet, UserCitiesViewSet

from .views.notifications import (
    notification,
    push_notifications,
    read_notification,
    open_notification,
    unread_notification_count,
    unopen_notification_count,
)
from .views.pinned import PinnedTagViewSet, PinnedTagTranslationViewSet

from rest_framework.routers import DefaultRouter
from .views.sentry_dummy_view import trigger_error

from .views.usergroup_members import UserGroupMembersViewSet

apiRouter = DefaultRouter()
apiRouter.register(r'apps', AppViewSet)
apiRouter.register(r'company', CompanyViewSet)
apiRouter.register(r'media/comments', MediaCommentViewSet)
apiRouter.register(r'media/resources', MediaResourceViewSet)
apiRouter.register(r'media', MediaViewSet)
apiRouter.register(
    r'luxury_culture_ratings',
    LuxuryCultureRatingViewSet
)
apiRouter.register(
    r'knowledge_ratings',
    KnowledgeRatingViewSet
)
apiRouter.register(
    r'luxurycultures/ratings',
    LuxuryCultureRatingViewSet
)
apiRouter.register(
    r'knowledges/ratings',
    KnowledgeRatingViewSet
)
apiRouter.register(r'themes/images', ThemeImageViewSet)
apiRouter.register(r'themes', ThemeViewSet)
apiRouter.register(r'users/countries', UserCountriesViewSet, base_name='usercountries')
apiRouter.register(r'users/cities', UserCitiesViewSet, base_name='usercities')
apiRouter.register(r'users', UserViewSet)
apiRouter.register(r'batchusercreatetasks', BatchUserCreateTaskViewSet)
apiRouter.register(r'batchusercreateitems', BatchUserCreateItemViewSet)
apiRouter.register(r'productgroups', ProductGroupViewSet)
apiRouter.register(r'usergroups', UserGroupViewSet)
apiRouter.register(r'userjobpositions', UserJobPositionViewSet)
apiRouter.register(r'userdepartments', UserDepartmentViewSet)
apiRouter.register(r'evaluations', EvaluationViewSet)
apiRouter.register(r'permissions', PermissionViewSet)
apiRouter.register(r'monthlyquizpoints', MonthlyQuizPointViewSet)
apiRouter.register(r'cheerupmessages', CheerUpMessageViewSet)
apiRouter.register(r'roles', RoleViewSet)
apiRouter.register(r'tags', TagViewSet)
apiRouter.register(r'luxurycultures', LuxuryCultureViewSet)

apiRouter.register(r'luxuryculturequiz', LuxuryCultureQuizViewSet)
apiRouter.register(r'luxuryculturequiztranslations',
                   LuxuryCultureQuizTranslationViewSet)
apiRouter.register(r'luxuryculturequizanswers', LuxuryCultureQuizAnswerViewSet)
apiRouter.register(r'luxuryculturequizanswertranslations',
                   LuxuryCultureQuizAnswerTranslationViewSet)

apiRouter.register(r'userknowledgequizresults', UserKnowledgeQuizResultViewSet)
apiRouter.register(r'userluxuryculturequizresults', UserLuxuryCultureQuizResultViewSet)
apiRouter.register(r'userknowledgeresults', UserKnowledgeResultViewSet)
apiRouter.register(r'knowledgestranslations', KnowledgeTranslationViewSet)
apiRouter.register(r'knowledgecards', KnowledgeCardViewSet)
apiRouter.register(r'knowledgecardstranslations',
                   KnowledgeCardTranslationViewSet)
apiRouter.register(r'luxuryculturetranslations',
                   LuxuryCultureTranslationViewSet)
apiRouter.register(r'activities', ActivityViewSet)
apiRouter.register(r'sessions', SessionViewSet)
apiRouter.register(r'tipsofthedays', TipsOfTheDayViewSet)
apiRouter.register(r'tipsofthedaytranslations', TipsOfTheDayTranslationViewSet)

apiRouter.register(r'knowledges', KnowledgeViewSet)
apiRouter.register(r'knowledgecards', KnowledgeCardViewSet)
apiRouter.register(r'knowledgequiz', KnowledgeQuizViewSet)
apiRouter.register(r'knowledgequiztranslations',
                   KnowledgeQuizTranslationViewSet)
apiRouter.register(r'knowledgequizanswers', KnowledgeQuizAnswerViewSet)
apiRouter.register(r'knowledgequizanswertranslations',
                   KnowledgeQuizAnswerTranslationViewSet)

apiRouter.register(r'dailychallenges', DailyChallengeViewSet)
apiRouter.register(r'dailychallengetranslations',
                   DailyChallengeTranslationViewSet)
apiRouter.register(r'dailychallengequiz', DailyChallengeQuizViewSet)
apiRouter.register(r'dailychallengequiztranslations',
                   DailyChallengeQuizTranslationViewSet)
apiRouter.register(r'dailychallengequizanswers',
                   DailyChallengeQuizAnswerViewSet)
apiRouter.register(r'dailychallengequizanswertranslations',
                   DailyChallengeQuizAnswerTranslationViewSet)
apiRouter.register(r'logentry', LogEntryViewSet)
apiRouter.register(r'logentries', LogEntryViewSet)
apiRouter.register(r'feeds', FeedViewSet)

apiRouter.register(r'countries', CountryViewSet)
apiRouter.register(r'zones', ZoneViewSet)
apiRouter.register(r'companyowners', CompanyOwnerViewSet)
apiRouter.register(r'companymanagers', CompanyManagerViewSet)
apiRouter.register(r'readfeeds', ReadFeedViewSet)
apiRouter.register(r'userknowledgequizanswers', UserKnowledgeQuizAnswerViewSet)
apiRouter.register(r'userdailychallengequizanswers', UserDailyChallengeQuizAnswerViewSet)
apiRouter.register(r'userluxuryculturequizanswers', UserLuxuryCultureQuizAnswerViewSet)
apiRouter.register(r'pinnedtags', PinnedTagViewSet)
apiRouter.register(r'pinnedtagtranslations', PinnedTagTranslationViewSet)
apiRouter.register(r'usergroupmembers', UserGroupMembersViewSet, base_name='usergroupmembers')

# access levels
apiRouter.register(r'contentmanagers', access_levels.ContentManagerViewSet)
apiRouter.register(r'usermanagers', access_levels.UserManagerViewSet)
apiRouter.register(r'productgroupmanagers', access_levels.ProductGroupManagerViewSet)
apiRouter.register(r'translators', access_levels.TranslatorViewSet)
apiRouter.register(r'coaches', access_levels.CoachViewSet)

urlpatterns = [
    url(r'^login$', auth.login, name='login'),
    url(r'^logout$', auth.logout, name='logout'),
    url(r'^forgot_password$', auth.forgot_password, name='forgot_password'),

    url(r'^user$', legacy.user, name='user'),
    url(r'^user_profile$', legacy.user_profile, name='user_profile'),
    url(r'^user_histories$', legacy.user_histories, name='user_histories'),

    url(r'^rqstatus', rq_status.get_rq_status, name='rqstatus'),

    url(r'^batchusercreatetasks/upload-signature$',
        BatchUserCreateTaskUploadSignatureView.as_view(),
        name='batchusercreate-upload-signature'),

    url(r'^knowledges$', legacy.knowledges, name='knowledges'),
    url(r'^knowledge_cards$', legacy.knowledge_cards, name='knowledge_cards'),
    url(r'^quiz$', legacy.quiz, name='quiz'),
    url(r'^daily_challenge$', legacy.daily_challenge, name='daily_challenge'),
    url(r'^luxury_cultures$', legacy.luxury_cultures, name='luxury_cultures'),

    url(r'^feeds$', legacy.feeds, name='feeds'),
    url(r'^ranking$', legacy.ranking, name='ranking'),
    url(r'^comment$', legacy.comment, name='comment'),
    url(r'^like$', legacy.like, name='like'),
    url(r'^change_password$', legacy.change_password, name='change_password'),
    url(r'^profile_picture$', legacy.profile_picture, name='profile_picture'),
    url(r'^new_feed$', legacy.new_feed, name='new_feed'),
    url(r'^change_language$', legacy.change_language, name='change_language'),
    url(r'^menu$', legacy.menu, name='menu'),

    # notifications
    url(r'^notification$', notification, name='notification'),
    url(r'^push_notifications$', push_notifications, name='push_notifications'),
    url(r'^read_notification$', read_notification, name='read_notification'),
    url(r'^open_notification$', open_notification, name='open_notification'),
    url(r'^unopen_notification_count$',
        unopen_notification_count,
        name='unopen_notification_count'),
    url(r'^unread_notification_count$',
        unread_notification_count,
        name='unread_notification_count'),

    url(r'^check_version$', check_version, name='check_version'),

    # upload signature
    url(r'^themes/upload-signature$',
        ThemeUploadSignatureView.as_view(),
        name='theme-upload-signature'),
    url(r'^apps/upload-signature$',
        AppUploadSignatureView.as_view(),
        name='app-upload-signature'),
    url(r'^media/upload-signature$',
        MediaUploadSignatureView.as_view(),
        name='media-upload-signature'),
    url(r'^luxurycultures/upload-signature$',
        LuxuryCultureUploadSignatureView.as_view(),
        name='luxuryculture-upload-signature'),
    url(r'^knowledgecards/upload-signature$',
        KnowledgeCardUploadSignatureView.as_view(),
        name='knowledgecard-upload-signature'),

    url(r'^memsource-events/(?P<token>[\w\s]+)?/$',
        memsource_events,
        name='memsource_events'),
    url(r'^company/analytics-permission/$',
        company_analytics_permission,
        name='company-analytics-permission'),
    url(r'^unlike/$',
        unlike,
        name='unlike'),

    # group permissions
    url(r'^roles/(?P<role_id>\d+)/permissions/(?P<content_type_id>\d+)/(?P<codename>.+)$',
        RolePermissionViewSet.as_view(actions={
            'post': 'add_permission',
            'delete': 'remove_permission'
        }),
        name='role-permissions'),

    # users permission
    url(r'^users/(?P<user_id>\d+)/roles$',
        UserRolesViewSet.as_view(actions={
            'get': 'get_roles',
        }),
        name='user-roles-list'),

    url(r'^users/(?P<user_id>\d+)/roles/(?P<role_id>\d+)$',
        UserRolesViewSet.as_view(actions={
            'post': 'add_role',
            'delete': 'remove_role',
        }),
        name='user-roles'),

    url(r'^user/permissions',
        UserOwnDetailsViewSet.as_view(actions={'get': 'get_user_permissions'}),
        name='user-permissions'),

    # bizcoach
    url(r'^bizcoach/users/$', BizCoachUserViewSet.as_view()),
    url(r'^bizcoach/tags/$', BizCoachTagViewSet.as_view()),

    url(r'^sentry-test/$', trigger_error, name='sentry-test'),

    # Routes for viewsets
    url(r'^', include(apiRouter.urls)),
]

