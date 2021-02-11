from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from ..v2.views.feed import FeedViewSet
from ..v2.views.knowledge import (
    KnowledgeViewSet,
    UserKnowledgeQuizResultViewSet,
)
from ..v2.views.knowledgequiz import KnowledgeQuizViewSet
from ..v2.views.media import (
    MediaResourceViewSet,
    MediaViewSet,
)
from ..v2.views.menu import menu
from ..v2.views.users import UserViewSet
from ..v1.views.auth import login

apiRouter = DefaultRouter()
apiRouter.register(r'feeds', FeedViewSet)
apiRouter.register(r'knowledges', KnowledgeViewSet)
apiRouter.register(r'knowledgequiz', KnowledgeQuizViewSet)
apiRouter.register(r'media/resources', MediaResourceViewSet)
apiRouter.register(r'media', MediaViewSet)
apiRouter.register(r'userknowledgequizresults', UserKnowledgeQuizResultViewSet)
apiRouter.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^login$', login, name='login', kwargs={'app_version': 2}),
    url(r'^', include(apiRouter.urls)),
    url(r'^menu/', menu, name='menu'),
]
