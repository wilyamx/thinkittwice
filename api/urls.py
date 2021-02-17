from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('api.v1.urls', namespace='api-v1')),
    url(r'^v2/', include('api.v2.urls', namespace='api-v2')),

    url(r'', include('api.v1.urls', namespace=''))
]
