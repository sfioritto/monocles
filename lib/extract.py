import urlparse
import urllib
import lxml
from readability.readability import Document
from lxml import html
from lxml.etree import tounicode


def styled_markup(orig, uri):

    with open("styles.css") as styles:
        css = styles.read()
        
    with open("nav.html") as nhtml:
        nav = nhtml.read()

    bypass = get_helper_urls(uri)
    e = lxml.html.document_fromstring(orig)
    e.body.insert(0, lxml.html.fragment_fromstring('<div class="clear"></div>'))
    e.body.insert(0, lxml.html.fragment_fromstring(nav % bypass))
    e.body.insert(0, lxml.html.fragment_fromstring('<style>%s</style>' % css))
    
    markup = tounicode(e)
    return markup


def get_helper_urls(url):
    
    bypassq = {"bypass" : "true"}
    url_parts = list(urlparse.urlparse(url))
    
    query = get_query_values(url)
    query.update(bypassq)
    url_parts[4] = urllib.urlencode(query)
    bypass = urlparse.urlunparse(url_parts)

    return bypass


def get_query_values(url):
    parsed = urlparse.urlparse(url)
    return dict(urlparse.parse_qsl(parsed.query))


def helper_options(url):

    query = get_query_values(url)
    keys = {}
    for key, value in query.items():
        if key in ["loggit", "bypass", "boilerpipe"]:
            keys[key] = value

    return keys.has_key("bypass"), keys.has_key("loggit"), keys.has_key("boilerpipe")


class Resource(object):

    def __init__(self, content, uri):
        self.content = content
        self.uri = uri
        self.bypass, self.loggit, self.boiler = helper_options(uri)


    def set_content(self, content):
        self.content = content


    @property
    def markup(self):

        try:
            markup = Document(self.content).summary()
        except:
            markup = self.content


        return markup


    @property
    def article(self):

        markup = styled_markup(self.markup, self.uri)
        
        #todo: write an "encode" function, pass it the charset header (so content-type)
        markup = markup.encode("utf-8")
        return markup
    

    def should_bypass(self):
        #skip urls with a special query string
        bypass, loggit, boiler = helper_options(self.uri)
        return bypass
 

    
