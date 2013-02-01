from django.conf.urls import patterns, url

urlpatterns = patterns('publication_linker.views',
    url(r'^$', 'home', name='home'),
    url(r'^article/(?P<article_id>\d+)$', 'view_article', name='view_article')
)