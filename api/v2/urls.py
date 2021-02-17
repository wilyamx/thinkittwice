from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from ..v2.views.feed import FeedViewSet

from ..v2.views.menu import menu
from ..v2.views.users import UserViewSet
from ..v1.views.auth import login

apiRouter = DefaultRouter()
apiRouter.register(r'feeds', FeedViewSet)

urlpatterns = [
    url(r'^login$', login, name='login', kwargs={'app_version': 2}),
    url(r'^', include(apiRouter.urls))
]
