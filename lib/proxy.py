import urlparse
import urllib
import lxml
import gzip
import io
from lxml import html
from lxml.etree import tounicode

def should_bypass(url):

    spliturl = url.split("?")

    if len(spliturl) > 1:
        
        querystring = spliturl[1]
        query = dict([tuple(pair.split("=")) for pair in querystring.split("&") if len(pair.split("=")) == 2])
        return query.has_key("bypass"), query.has_key("loggit")
    
    else:
        return False, False


def get_bypass_urls(url):
    
    bypassq = {"bypass" : "true"}
    loggitq = {"bypass" : "true",
               "loggit" : "true"}
    
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    
    query.update(bypassq)
    url_parts[4] = urllib.urlencode(query)
    bypass = urlparse.urlunparse(url_parts)
    
    query.update(loggitq)
    url_parts[4] = urllib.urlencode(query)
    loggit = urlparse.urlunparse(url_parts)

    return bypass, loggit


def styled_markup(orig, bypass, loggit):

    with open("styles.css") as styles:
        css = styles.read()
        
    with open("nav.html") as nhtml:
        nav = nhtml.read()
        
    e = lxml.html.document_fromstring(orig)
    e.body.insert(0, lxml.html.fragment_fromstring('<div class="clear"></div>'))
    e.body.insert(0, lxml.html.fragment_fromstring(nav % (bypass, loggit)))
    e.body.insert(0, lxml.html.fragment_fromstring('<style>%s</style>' % css))
    
    markup = tounicode(e)
    return markup


def is_gzipped(headers):
    """
    Takes a twisted response header object.
    """
    return headers.hasHeader("content-encoding") and \
        headers.getRawHeaders("content-encoding")[0] == "gzip"


def gunzip(buffer):
    bi = io.BytesIO(buffer)
    gf = gzip.GzipFile(fileobj=bi, mode="rb")
    return gf.read()

