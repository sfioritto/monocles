import io
import urlparse
import gzip as gziplib
from StringIO import StringIO

"""
This is a bag of helper functions for the proxy. It does stuff like parse headers,
gzip and gunzip, etc.
"""

# don't parse anything on these sites. This ends up being webapps mostly.
blacklist = ["www.facebook.com",
             "news.ycombinator.com",
             "www.google.com",
             "en.wikipedia.org",
             "adserver.adtechus.com",
             "www.instapaper.com",
             "www.redfin.com",
             "code.google.com",
             "www.quora.com",
             "www.youtube.com",
             "vimeo.com",
             "www.twitter.com",
             "cdn.api.twitter.com"]


def should_parse(father):

    """
    Go through a series of quick tests to determine if this should even be
    parsed. Anything that shouldn't be parsed is completely bypassed.
    """
    
    ctype = get_ctype(father.responseHeaders.getRawHeaders("content-type"))
    if not_homepage(father.uri) and \
        father.code == 200 and \
        valid_content_type(ctype) and \
        not_on_blacklist(father.uri) and \
        father.method == "GET":
        return True
    else:
        return False


def get_ctype(typeheader):

    """
    Return the content type
    """

    if typeheader:
        return typeheader[0]
    else:
        return None


def add_to_blacklist(uri):

    """
    Adds a domain to the blacklist in memory. It's logged
    so I can determine if I want to add it permanently later.
    """
    global blacklist
    parsed = urlparse.urlparse(uri)
    blacklist.append(parsed.netloc)


def not_homepage(uri):
    parsed = urlparse.urlparse(uri)
    return parsed.path.strip("/")


def valid_content_type(contype):
    """
    Only parse these content types.
    """
    contypes = ["text/html", "application/xhtml+xml"]
    for ctype in contypes:
        if contype.startswith(ctype):
            return True
    return False


def not_on_blacklist(uri):
    parsed = urlparse.urlparse(uri)
    return parsed.netloc not in blacklist


def accepts_gzipped(encodings):
    return encodings and "gzip" in encodings[0]


def is_gzipped(headers):
    """
    Takes a twisted response header object.
    """
    return headers.hasHeader("content-encoding") and \
        headers.getRawHeaders("content-encoding")[0] == "gzip"


def is_deflated(headers):
    return headers.hasHeader("content-encoding") and \
        headers.getRawHeaders("content-encoding")[0] == "deflate"


def gunzip(buffer):

    bi = io.BytesIO(buffer)
    gf = gziplib.GzipFile(fileobj=bi, mode="rb")
    return gf.read()


def deflate(buffer):
    # bypass gzip headers by setting negative wbit value
    # http://bugs.python.org/issue5784
    return gziplib.zlib.decompress(buffer, -15)


def gzip(markup):

    sio = StringIO()
    gzf = gziplib.GzipFile(fileobj=sio, mode="wb")
    gzf.write(markup)
    gzf.close()
    return sio.getvalue()
    

