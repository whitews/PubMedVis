import urllib
import urllib2
from xml.etree import ElementTree

DB = 'pubmed'
ESUMMARY_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
ELINK_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi'

def find_articles(pubmed_id_list):

    articles = []

    args = {
        'db': DB,
        'id': ','.join(pubmed_id_list)
    }

    encoded_args = urllib.urlencode(args)
    response = urllib2.urlopen(ESUMMARY_URL, encoded_args)

    xml = ElementTree.fromstring(response.read())

    summaries_xml = xml.findall("DocSum")

    for summary_el in summaries_xml:

        # Reset all the elements we expect to find for each summary element
        pubmed_id_element = None
        title_element = None
        authorlist_elements = None

        # Find the article's pubmed id
        pubmed_id_element = summary_el.find("Id")

        if pubmed_id_element is not None:
            pubmed_id = pubmed_id_element.text
        else:
            continue

        # Find the article's title
        title_element = summary_el.find("Item[@Name='Title']")

        if title_element is not None:
            title_text = title_element.text
        else:
            continue
            #raise TypeError("title_text should be type str, but NoneType was found.")

        # Find article's authors
#        authorlist_elements = summary_el.findall("Item[@Name='AuthorList']")
#        authors = []
#
#        for el in authorlist_elements:
#            for author_el in el.findall("Item[@Name='Author']"):
#                authors.append(author_el.text)

        # Great, we got a good article, add it to the list
        articles.append(
            {
                'pubmed_id': pubmed_id,
                'title': title_text,
                #'authors': authors,
            }
        )

    return articles


def find_article_references(pubmed_id_list):
    # ELINK script will accept multiple IDs for one id field, but the
    # returned list of referenced IDs won't show which ID referenced it.
    # A work-around is to add multiple id fields in the same request.
    #
    # Because of this, we need to use a sequence of tuples rather than a
    # dictionary for the args to encode
    args = [
        ('db', DB),
        ('cmd', 'neighbor'),
        ('linkname', 'pubmed_pubmed_refs'),
    ]

    if len(pubmed_id_list) > 500:
        pass

    for pm_id in pubmed_id_list:
        args.append(('id', pm_id))

    encoded_args = urllib.urlencode(args)
    response = urllib2.urlopen(ELINK_URL, encoded_args)

    xml = ElementTree.fromstring(response.read())

    # will be a dictionary whose keys are the pubmed IDs requested
    # and the values will be a list of the key's referenced pubmed IDs
    reference_dict = {}

    for link_set in xml.findall("LinkSet"):

        # should be just one parent Id in IdList
        parent_ids = link_set.findall("IdList/Id")

        # if we got more than one, we can't tell who referencing who, so we'll skip it
        if len(parent_ids) != 1:
            continue

        parent_id = parent_ids[0].text

        # good, we can add this article
        reference_dict[parent_id] = []

        ref_elements = link_set.findall("LinkSetDb/Link/Id")
        for el in ref_elements:
            reference_dict[parent_id].append(el.text)

    return reference_dict
