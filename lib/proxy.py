import urlparse
import urllib
import lxml
import gzip
import io
from lxml import html
from lxml.etree import tounicode


def should_bypass(url):

    query = get_query_values(url)
    return query.has_key("bypass"), query.has_key("loggit")


def get_query_values(url):

    parsed = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(parsed.query))
    return { key: query[key] for key in ["loggit", "bypass", "boilerpipe"] if query.has_key(key)}


def get_helper_urls(url):
    
    bypassq = {"bypass" : "true"}
    loggitq = {"bypass" : "true",
               "loggit" : "true"}
    boilerq = {"boilerpipe" : "true"}
    url_parts = list(urlparse.urlparse(url))
    
    query = get_query_values(url)
    query.update(bypassq)
    url_parts[4] = urllib.urlencode(query)
    bypass = urlparse.urlunparse(url_parts)
    
    query.update(loggitq)
    url_parts[4] = urllib.urlencode(query)
    loggit = urlparse.urlunparse(url_parts)

    query = get_query_values(url)
    query.update(boilerq)
    url_parts[4] = urllib.urlencode(query)
    boiler = urlparse.urlunparse(url_parts)
    return bypass, loggit, boiler


def styled_markup(orig, bypass, loggit, boiler):

    with open("styles.css") as styles:
        css = styles.read()
        
    with open("nav.html") as nhtml:
        nav = nhtml.read()
        
    e = lxml.html.document_fromstring(orig)
    e.body.insert(0, lxml.html.fragment_fromstring('<div class="clear"></div>'))
    e.body.insert(0, lxml.html.fragment_fromstring(nav % (bypass, loggit, boiler)))
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

