from twisted.web import proxy, http
from twisted.python import log
from twisted.internet import reactor
from readability.readability import Document
from StringIO import StringIO
from lxml.etree import tounicode
import gzip
import io
import lxml
import urlparse
import urllib



log.startLogging(open('/var/log/monocles.log', 'a'), setStdout=False)
#TODO:
# strip logging query strings from URI before sending a request
# put a url in the top of the page that includes the bypass url and a bypass and loggit option
# include some basic css so that it's not so damn wide.



def should_bypass(uri):

    splituri = uri.split("?")

    if len(splituri) > 1:
        
        querystring = splituri[1]
        query = dict([tuple(pair.split("=")) for pair in querystring.split("&") if len(pair.split("=")) == 2])
        return query.has_key("bypass"), query.has_key("loggit")
    
    else:
        return False, False


class ProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.text = False
        self.haveAllHeaders = False


    def handleHeader(self, key, value):
        #TODO: probably don't need to do this, can get headers on self.father
        if key == "Content-Type" and value.startswith("text"):
            self.text = True

        proxy.ProxyClient.handleHeader(self, key, value)


    def dataReceived(self, data):

        #This is basically for hacker news which doesn't put
        #crlf at the end of headers
        if not self.haveAllHeaders:
            if self.delimiter not in data and "\n" in data:
                data = data.replace("\n", self.delimiter)
                
        return proxy.ProxyClient.dataReceived(self, data)


    def handleResponsePart(self, data):
        self.buffer = self.buffer + data


    def handleEndHeaders(self):
        # this flag used in dataReceived, this function is in the http client
        self.haveAllHeaders = True;
        

    def handleResponseEnd(self):

        if not self._finished:

            #skip urls with a special query string
            bypass, loggit = should_bypass(self.father.uri)
            if bypass:
                self.father.write(self.buffer)
                if loggit:
                    log.msg("MONOCLES: %s" % self.father.uri)

                return proxy.ProxyClient.handleResponseEnd(self)

            if self.father.responseHeaders.hasHeader("content-encoding") and \
                self.father.responseHeaders.getRawHeaders("content-encoding")[0] == "gzip":
                self.father.responseHeaders.removeHeader("content-encoding")
                bi = io.BytesIO(self.buffer)
                gf = gzip.GzipFile(fileobj=bi, mode="rb")
                self.buffer = gf.read()

            if self.text:
                try:
                    readable_article = Document(self.buffer).summary()
                    # todo: this is kludge, should be determined in
                    # readability module
                    if len(readable_article) > 250: 
                        markup = readable_article
                        # TODO: you should also just put in a style tag here to make things look a little nicer.
                        e = lxml.html.document_fromstring(markup)

                        bypassq = {"bypass" : "true"}
                        loggitq = {"bypass" : "true",
                                  "loggit" : "true"}
                        
                        url_parts = list(urlparse.urlparse(self.father.uri))
                        query = dict(urlparse.parse_qsl(url_parts[4]))
                        
                        query.update(bypassq)
                        url_parts[4] = urllib.urlencode(query)
                        bypass = urlparse.urlunparse(url_parts)

                        query.update(loggitq)
                        url_parts[4] = urllib.urlencode(query)
                        loggit = urlparse.urlunparse(url_parts)
                        

                        with open("styles.css") as styles:
                            css = styles.read()

                        with open("nav.html") as nhtml:
                            nav = nhtml.read()

                        e.body.insert(0, lxml.html.fragment_fromstring('<div class="clear"></div>'))
                        e.body.insert(0, lxml.html.fragment_fromstring(nav % (bypass, loggit)))
                        e.body.insert(0, lxml.html.fragment_fromstring('<style>%s</style>' % css))

                        markup = tounicode(e)
                        #accept-charset was set to only utf-8, so assuming
                        #the response is encoded as utf-8. we'll see how that works out...
                        markup = markup.encode("utf-8")
                    else:
                        markup = self.buffer
                except:
                    markup = self.buffer

            else:
                markup = self.buffer


            encodings = self.father.requestHeaders.getRawHeaders("accept-encoding")
            if encodings and "gzip" in encodings[0]:
                self.father.responseHeaders.setRawHeaders("content-encoding", ["gzip"])
                sio = StringIO()
                gzf = gzip.GzipFile(fileobj=sio, mode="wb")
                gzf.write(markup)
                gzf.close()
                markup = sio.getvalue()


            self.father.responseHeaders.setRawHeaders("content-length", [len(markup)])

            #TODO: turn off after done developing, for now don't ever cache anything.
            self.father.responseHeaders.removeHeader("cache-control")

            self.father.write(markup)
            return proxy.ProxyClient.handleResponseEnd(self)


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient


class ProxyRequest(proxy.ProxyRequest):
    
    protocols = {'http': ProxyClientFactory}
    ports = {'http': 80 }

    def process(self):

        self.requestHeaders.setRawHeaders("accept-charset", ["utf-8"])
        return proxy.ProxyRequest.process(self)
    

class Proxy(http.HTTPChannel):
    requestFactory = ProxyRequest


factory = http.HTTPFactory()
factory.protocol = Proxy


reactor.listenTCP(8080, factory)
reactor.run()

