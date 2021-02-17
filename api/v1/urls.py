from django.conf.urls import include, url

from .views.feed import FeedViewSet

from rest_framework.routers import DefaultRouter

apiRouter = DefaultRouter()
apiRouter.register(r'feeds', FeedViewSet)

urlpatterns = [
    url(r'^login$', auth.login, name='login'),
    url(r'^logout$', auth.logout, name='logout'),
    url(r'^forgot_password$', auth.forgot_password, name='forgot_password'),

    # Routes for viewsets
    url(r'^', include(apiRouter.urls)),
]

