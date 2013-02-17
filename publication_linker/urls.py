from django.conf.urls import patterns, url

urlpatterns = patterns('publication_linker.views',
    url(r'^$', 'home', name='home'),
    url(r'^article/(?P<pubmed_id>\d+)$', 'view_article', name='view_article'),
    url(r'^article/(?P<pubmed_id>\d+)/relations$', 'article_relations', name='article_relations'),
)