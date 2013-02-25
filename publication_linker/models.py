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
        print "%s - %s" % (datetime.now().ctime(), "START")

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

            print "%s - Depth: %d" % (datetime.now().ctime(), i)

        del(temp_list)

        print "%s - %s" % (datetime.now().ctime(), "FIND ARTICLES")

        if len(total_list) > 0:

            # get a list of pubmed IDs already in the Article model
            existing_pubmed_id_list = Article.objects.filter(pubmed_id__in=total_list).values_list('pubmed_id', flat=True)

            # only find articles we haven't already got
            # this avoids using get_or_create, which takes too long in bulk operations
            # IMPORTANT: the existing_pubmed_id_list contains integers, not strings,
            # so we map to str here
            new_pubmed_id_list = list(set(total_list) - set(map(str, existing_pubmed_id_list)))

            # If there are no new PubMed IDs, then stop
            if len(new_pubmed_id_list) == 0:
                return

            # find all the new articles' summaries (and authors)
            # this could take a while
            articles_to_save = find_articles(new_pubmed_id_list)

            print "%s - %s" % (datetime.now().ctime(), "ARTICLES FOUND, ARTICLES TO DB")

            # for storing our new Article model instances
            new_art_instance_list = set()

            # And a set to catch all the authors we'll collect in the article for loop
            # We'll do a similar bulk_create for the new authors
            author_set = set()

            # find_articles returned a list of dictionaries, each dict is an article to save
            for new_art in articles_to_save:

                new_art_instance_list.add(Article(pubmed_id=new_art['pubmed_id'], title=new_art['title']))

                # Catch the authors here
                author_set.update(new_art['authors'])

            # save the new articles in bulk
            # TODO: maybe catch any exceptions here...look into Exceptions thrown by bulk_create
            Article.objects.bulk_create(list(new_art_instance_list))

            print "%s - %s" % (datetime.now().ctime(), "ARTICLES SAVED")

            # for all the new articles created, we need to add the authors and article relationships
            print "%s - %s" % (datetime.now().ctime(), "ARTICLE RELATIONSHIPS TO DB")

            # get all the Articles corresponding to the reference dict keys which have non-empty values
            referenced_article_list = []
            for k in total_reference_dict.keys():
                if len(total_reference_dict[k]) > 0:
                    referenced_article_list.append(k)

            # now get the Article model instances just for the ones with references to add
            articles_with_refs = Article.objects.filter(pubmed_id__in=referenced_article_list)

            for article in articles_with_refs:
                references = Article.objects.filter(pubmed_id__in=total_reference_dict[str(article.pubmed_id)])

                article.referenced_articles.add(*references)

#                for name in new_art['authors']:
#                    author, created = Author.objects.get_or_create(name=name)
#                    new_art_instance.authors.add(author)

        print "%s - %s" % (datetime.now().ctime(), "END")


