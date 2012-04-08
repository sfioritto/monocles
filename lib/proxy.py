import io
import gzip as gziplib
from StringIO import StringIO

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
    

