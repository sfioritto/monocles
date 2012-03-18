from twisted.web import proxy, http
from twisted.internet import reactor
from readability.readability import Document
import urllib
import gzip
import StringIO


class ProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.text = False


    def handleHeader(self, key, value):
        if key == "Content-Type" and value.startswith("text/html"):
            self.text = True

        proxy.ProxyClient.handleHeader(self, key, value)


    def handleResponsePart(self, buffer):
        self.buffer += buffer


    def handleResponseEnd(self):
        
        if not self._finished:

            headers = dict(self.father.requestHeaders.getAllRawHeaders())
            if headers.has_key("content-encoding") and headers["content-encoding"] == "gzip":
                sio = StringIO.StringIO(self.buffer)
                gzipf = gzip.GzipFile(fileobj=sio, mode='r')
                self.buffer = gzipf.read()
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

