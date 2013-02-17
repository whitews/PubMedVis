from publication_linker.models import *
from publication_linker.forms import *
from publication_linker.query_pubmed import find_articles

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

import json

def home(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)

        if 'pubmed_id' in request.POST:
            pubmed_id = request.POST['pubmed_id']
            article = None
            try:
                article = Article.objects.get(pubmed_id=pubmed_id)
            except ObjectDoesNotExist:
                article_list = find_articles([pubmed_id])
                if len(article_list) == 1:
                    article_dict = article_list[0]
                    article = Article(
                        pubmed_id=article_dict['pubmed_id'],
                        title=article_dict['title'])
                    article.save()

                    # now add the author relationships, adding the author if necessary
                    for name in article_dict['authors']:
                        author, created = Author.objects.get_or_create(name=name)
                        article.authors.add(author)

                    # now add the references at some depth
                    article.add_references(depth=2)

                    return HttpResponseRedirect(reverse('view_article', args=(article.pubmed_id,)))

            if article is not None:
                return HttpResponseRedirect(reverse('view_article', args=(article.pubmed_id,)))
            else:
                return HttpResponseRedirect(reverse('home',))

        else:
            return HttpResponseRedirect(reverse('home',))
    else:
        form = ArticleForm()

    most_referenced_articles = Article.objects.annotate(Count('article')).order_by('-article__count')[0:5]

    return render_to_response(
        'home.html',
        {
            'form': form,
            'most_referenced_articles': most_referenced_articles,
        },
        context_instance=RequestContext(request)
    )


def view_article(request, pubmed_id):
    article = get_object_or_404(Article, pubmed_id=pubmed_id)

    if request.method == 'POST':

        if 'refresh' in request.POST:
            article.add_references(depth=2)

        return HttpResponseRedirect(reverse('view_article', args=(article.pubmed_id,)))

    return render_to_response(
        'view_article.html',
        {
            'article': article,
        },
        RequestContext(request),
    )


def article_relations(request, pubmed_id):
    article = get_object_or_404(Article, pubmed_id=pubmed_id)
    group_0 = [{'group': 0, 'pubmed_id': article.pubmed_id, 'title': article.title},]

    # need a set of pubmed ids to prevent duplicate nodes
    pubmed_id_set = set([article.pubmed_id])

    # We're gonna do 2 things here
    #   1: get the distinct list of referenced articles 2 levels deep, and these are the 'nodes'
    #   2: get all the relationships between all the nodes, and these are the 'links'
    group_1_articles = article.referenced_articles.all()
    pubmed_id_set.update(group_1_articles.values_list('pubmed_id', flat=True))
    group_1 = list(group_1_articles.values('pubmed_id', 'title'))
    group_2 = []

    links = []

    for g in group_1:
        links.append({'source':article.pubmed_id,'target':g['pubmed_id']})
        g['group'] = 1
        pubmed_id_set.add(g['pubmed_id'])
        g_1_article = group_1_articles.get(pubmed_id=g['pubmed_id'])
        g_1_references = g_1_article.referenced_articles.values('pubmed_id', 'title')
        for g_1_ref in g_1_references:
            if g_1_ref['pubmed_id'] not in pubmed_id_set:
                pubmed_id_set.add(g_1_ref['pubmed_id'])
                g_1_ref['group'] = 2
                group_2.append(g_1_ref)
            links.append({'source':g['pubmed_id'],'target':g_1_ref['pubmed_id']})

    # need to iterate over group_2 to get any references matching any pubmed IDs we already have
    for g in group_2:
        g_2_article = Article.objects.get(pubmed_id=g['pubmed_id'])
        g_2_references = g_2_article.referenced_articles.values('pubmed_id')
        for g_2_ref in g_2_references:
            if g_2_ref['pubmed_id'] in pubmed_id_set:
                links.append({'source':g['pubmed_id'],'target':g_2_ref['pubmed_id']})

    groups = group_0 + group_1 + group_2

    json_data = json.dumps(dict({'nodes':groups,'links':links}), indent=4)

    return HttpResponse(json_data, content_type='text/json')

