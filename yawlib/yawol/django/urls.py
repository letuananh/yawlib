# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^synset/(?P<synsetid>\w+)$', views.get_synset, name='synset'),
    url(r'^search/(?P<query>.+)$', views.search, name='search'),
    url(r'^version/?$', views.version, name='version')
]
