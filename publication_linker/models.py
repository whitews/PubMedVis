from django.db import models
from publication_linker.query_pubmed import find_articles, find_article_references

class Journal(models.Model):
    name = models.CharField(max_length=256, unique=True, null=False, blank=False)

class Author(models.Model):
    name = models.CharField(max_length=128, unique=True, null=False, blank=False)

# To keep track of PubMed reference relationships prior to getting their summaries
# and prior to saving to the DB
class ArticleNode(object):
    def __init__(self, id, parent=None):
        self.id = id
        self.parent = parent
        self.children = []
        if parent is None:  # root node
            pass
        else:  # non-root nodes
            self.parent.children.append(self)

class Article(models.Model):
    pubmed_id = models.IntegerField(unique=True, null=False, blank=False)
    title     = models.CharField(max_length=512, null=False, blank=False)
    authors   = models.ManyToManyField(Author)
    referenced_articles = models.ManyToManyField('self', symmetrical=False)

    def add_references(self, depth):
        # TODO: some articles genuinely have no references in PubMed, maybe flag whether articles have been checked???

        list = [self.pubmed_id]
        total_list = []
        total_reference_dict = {}

        for i in range(depth):
            referenced_dict = find_article_references(list)

            list = []

            for key in referenced_dict.keys():
                list.extend(referenced_dict[key])
                total_list.extend(referenced_dict[key])
                total_reference_dict[key] = referenced_dict[key]

        if len(total_list) > 0:
            reference_articles = find_articles(total_list)

            # find_articles returned a list of dictionaries, each dict is an article to save
            for ref in reference_articles:
                article, created = Article.objects.get_or_create(pubmed_id=ref['pubmed_id'], title=ref['title'])
                if created:
                    for name in ref['authors']:
                        author, created = Author.objects.get_or_create(name=name)
                        article.authors.add(author)

            # need to add article relationships
            for key in total_reference_dict.keys():
                try:
                    article = Article.objects.get(pubmed_id=key)
                    for value in total_reference_dict[key]:
                        try:
                            related_articles = Article.objects.get(pubmed_id=value)
                        except:
                            continue
                        article.referenced_articles.add(related_articles)
                except:
                    continue


