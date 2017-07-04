from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^synset/(?P<synsetid>\w+)$', views.get_synset, name='synset'),
    url(r'^search/(?P<query>.+)$', views.search, name='search'),
    url(r'^version/?$', views.version, name='version')
]
