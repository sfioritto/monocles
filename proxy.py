from twisted.web import proxy, http
from twisted.internet import reactor
from readability.readability import Document
from StringIO import StringIO
import gzip
import io

#TODO:
# put a url in the top of the page that includes the bypass url.
# add logging so you can view your logs later and fix the borked urls

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
            bypass, log = should_bypass(self.father.uri)
            if bypass:
                self.father.write(self.buffer)
                if log:
                    #TODO: log right here
                    pass
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

