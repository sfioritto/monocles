from twisted.web import proxy, http
from twisted.internet import reactor
from readability.readability import Document
import gzip
import io


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

            if self.father.responseHeaders.hasHeader("content-encoding") and \
                self.father.responseHeaders.getRawHeaders("content-encoding")[0] == "gzip":
                self.father.responseHeaders.removeHeader("content-encoding")
                bi = io.BytesIO(self.buffer)
                gf = gzip.GzipFile(fileobj=bi, mode="rb")
                self.buffer = gf.read()

            if self.text:
                try:
                    readable_article = Document(self.buffer).summary()
                    if len(readable_article) > 250:
                        markup = readable_article
                        markup = markup.encode("utf-8")
                    else:
                        markup = self.buffer
                except:
                    markup = self.buffer

            else:
                markup = self.buffer
                
            self.father.responseHeaders.setRawHeaders("content-length", [len(markup)])
            self.father.write(markup)
            return proxy.ProxyClient.handleResponseEnd(self)


    def ahandleResponseEnd(self):

        if not self._finished:
            if self.father.responseHeaders.hasHeader("content-encoding") and \
                self.father.responseHeaders.getRawHeaders("content-encoding")[0] == "gzip":
                bi = io.BytesIO(self.buffer)
                gf = gzip.GzipFile(fileobj=bi, mode="rb")
                self.buffer = gf.read()


            self.father.responseHeaders.setRawHeaders("content-length", [len(markup)])
            self.father.write(markup)
            
            proxy.ProxyClient.handleResponseEnd(self)


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient


class ProxyRequest(proxy.ProxyRequest):
    
    protocols = {'http': ProxyClientFactory}
    ports = {'http': 80 }
    
    def process(self):
        self.requestHeaders.removeHeader('accept-encoding')
        proxy.ProxyRequest.process(self)
        

class Proxy(http.HTTPChannel):
    requestFactory = ProxyRequest


factory = http.HTTPFactory()
factory.protocol = Proxy


reactor.listenTCP(8080, factory)
reactor.run()

