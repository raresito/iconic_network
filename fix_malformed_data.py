from requests import Request, Session
from client import ElsClient, ElsSearch, ElsAuthor, AbsDoc
from models import *
import pprint as pp
import peewee as pw
import logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

class Colour:
    OKGREEN = '\033[92m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Load configuration
con_file = open("config.json")
config = json.load(con_file)
con_file.close()

# Initialize elsclient client
client = ElsClient(config['apikey'])

req = Session()
req.get('https://www.scopus.com/author/highchart.uri')

print(Colour.UNDERLINE + 'Initial request to SCOPUS ' + Colour.END)


def get_author_citations():
    authors_list = Author.select(Author.id).where(Author.citations.is_null(True)).order_by(Author.cited_by_count.desc())

    for author in authors_list:
        print(Colour.BOLD + 'Request for "' + str(author.id) + '"' + Colour.END)

        params = {
            'authorId': author.id
        }
        citations = req.get('https://www.scopus.com/author/highchart.uri', params=params)
        # Handle empty response
        if citations.text == '':
            obj = {}
            nr_of_years = 0
        else:
            obj = citations.json()
            data = obj.get('citeObj') or obj.get('docObj')
            nr_of_years = str(len(data))
        
        # Store fetched citations
        saved = author.update(citations=obj).where(Author.id == author.id)
        saved.execute()

        print(Colour.OKGREEN + 'Got ' + str(nr_of_years) + ' years of citations for "' + str(author.id) + '"' + Colour.END)
        print(' --- in ' + str(citations.elapsed.total_seconds()) + 's')

def fix_malformed_date():
    invalid_date = Collaboration.select().where(pw.fn.DATE(Collaboration.published).is_null())

    for row in invalid_date:
        article = AbsDoc(scp_id=row.abs_id)
        article.read(client)

        date = article.data['coredata'].get('prism:coverDate')

        saved = row.update(published=date).where(Collaboration.abs_id == row.abs_id)
        saved.execute()
        
        print(Colour.OKGREEN + 'Fixed date for ' + str(row.abs_id) + ', from ' + str(row.published) + ' to ' + str(date) + Colour.END)

def fullfil_collaboration_authors():
    collaborations = Collaboration.select(Collaboration.abs_id).where(Collaboration.message.is_null(True)).limit(100)

    for row in collaborations:
        article = AbsDoc(scp_id=row.abs_id)
        if article.read(client):
            pp.pprint(pp.pformat(article.data))
        else:
            pp.pprint('Insuccess for article ' + str(row.abs_id))

def update_category():
    saved_phys = Coauthors.select()

    for author in saved_phys:
        db_author = Author.get(Author.id == author.id)
        db_author.cat = ['PHYS']
        db_author.save()

        print(Colour.OKGREEN + str(db_author.id) + " now has cat set to " + ','.join(db_author.cat) + Colour.END)

#get_author_citations()

#fix_malformed_date()

# update_category()

fullfil_collaboration_authors()