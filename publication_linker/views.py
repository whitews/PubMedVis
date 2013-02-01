from publication_linker.models import *
from publication_linker.forms import *
from publication_linker.query_pubmed import find_articles

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

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

                    return HttpResponseRedirect(reverse('view_article', args=(article.id,)))

            if article is not None:
                return HttpResponseRedirect(reverse('view_article', args=(article.id,)))
            else:
                return HttpResponseRedirect(reverse('home',))

        else:
            return HttpResponseRedirect(reverse('home',))
    else:
        form = ArticleForm()

    return render_to_response(
        'home.html',
        {
            'form': form,
        },
        context_instance=RequestContext(request)
    )

def view_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    #if article.referenced_articles.all().count() == 0:
    #    article.add_references(depth=2)

    return render_to_response(
        'view_article.html',
        {
            'article': article,
        },
        RequestContext(request),
    )