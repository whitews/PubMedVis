from publication_linker.models import *

from django.forms import ModelForm

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        exclude = ('title', 'authors', 'referenced_articles')