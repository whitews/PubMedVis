from django.db import models
from django.db import IntegrityError
from publication_linker.query_pubmed import find_articles, find_article_references

from datetime import datetime

class Journal(models.Model):
    name = models.CharField(max_length=256, unique=True, null=False, blank=False)

class Author(models.Model):
    name = models.CharField(max_length=128, unique=True, null=False, blank=False)

class Article(models.Model):
    # making pubmed_id the primary key, since they must be unique
    # and we'll nee to rely on the do identify Article objects
    # for bulk operations...like adding authors for a new article w/o
    # querying the database to get the article first
    pubmed_id = models.IntegerField(primary_key=True)

    # the title as PubMed string
    title     = models.CharField(max_length=512, null=False, blank=False)
    authors   = models.ManyToManyField(Author)
    referenced_articles = models.ManyToManyField('self', symmetrical=False)

    def add_references(self, depth):
        # TODO: some articles genuinely have no references in PubMed, maybe flag whether articles have been checked???

        temp_list = [self.pubmed_id]
        total_list = []
        total_reference_dict = {}

        for i in range(depth):
            referenced_dict = find_article_references(temp_list)

            temp_list = []

            for key in referenced_dict.keys():
                temp_list.extend(referenced_dict[key])
                total_list.extend(referenced_dict[key])
                total_reference_dict[key] = referenced_dict[key]

        del(temp_list)

        if len(total_list) > 0:

            # get a list of pubmed IDs already in the Article model
            existing_pubmed_id_list = Article.objects.filter(pubmed_id__in=total_list).values_list('pubmed_id', flat=True)

            # only find articles we haven't already got
            # this avoids using get_or_create, which takes too long in bulk operations
            new_pubmed_id_list = list(set(total_list) - set(existing_pubmed_id_list))
            articles_to_save = find_articles(new_pubmed_id_list)

            print "%s - %s" % (datetime.now().ctime(), "ARTICLES FOUND, ARTICLES TO DB")

            # for storing our new Article model instances
            new_art_instance_list = []

            # find_articles returned a list of dictionaries, each dict is an article to save
            for new_art in articles_to_save:

                new_art_instance_list.append(Article(pubmed_id=new_art['pubmed_id'], title=new_art['title']))

            Article.objects.bulk_create(new_art_instance_list)

            pass

#                for name in new_art['authors']:
#                    author, created = Author.objects.get_or_create(name=name)
#                    new_art_instance.authors.add(author)

#
#            print "%s - %s" % (datetime.now().ctime(), "ARTICLE RELATIONSHIPS TO DB")
#
#            # need to add article relationships
#            for key in total_reference_dict.keys():
#                try:
#                    article = Article.objects.get(pubmed_id=key)
#                    for value in total_reference_dict[key]:
#                        try:
#                            related_articles = Article.objects.get(pubmed_id=value)
#                        except:
#                            continue
#                        article.referenced_articles.add(related_articles)
#                except:
#                    continue

        print "%s - %s" % (datetime.now().ctime(), "END")


