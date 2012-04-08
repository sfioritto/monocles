import io
import urlparse
import gzip as gziplib
from StringIO import StringIO


def should_parse(father):

    ctype = father.responseHeaders.getRawHeaders("content-type")[0]
    return not_homepage(father.uri) and valid_content_type(ctype) and not_on_blacklist(father.uri)


def not_homepage(uri):
    parsed = urlparse.urlparse(uri)
    return parsed.path.strip("/")


def valid_content_type(contype):
    contypes = ["text/html", "application/xhtml+xml"]
    for ctype in contypes:
        if contype.startswith(ctype):
            return True
    return False


def not_on_blacklist(uri):
    parsed = urlparse.urlparse(uri)
    blacklist = ["www.facebook.com",
                 "news.ycombinator.com",
                 "www.google.com",
                 "en.wikipedia.org"]
    return parsed.netloc not in blacklist

def accepts_gzipped(encodings):

    return encodings and "gzip" in encodings[0]

def is_gzipped(headers):
    """
    Takes a twisted response header object.
    """
    return headers.hasHeader("content-encoding") and \
        headers.getRawHeaders("content-encoding")[0] == "gzip"


def gunzip(buffer):

    bi = io.BytesIO(buffer)
    gf = gziplib.GzipFile(fileobj=bi, mode="rb")
    return gf.read()


def gzip(markup):

    sio = StringIO()
    gzf = gziplib.GzipFile(fileobj=sio, mode="wb")
    gzf.write(markup)
    gzf.close()
    return sio.getvalue()
    

