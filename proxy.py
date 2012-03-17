from twisted.web import proxy, http
from twisted.internet import reactor
from readability.readability import Document
import urllib
import gzip


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
            if self.text:
                try:
                    import pdb; pdb.set_trace()
                    readable_article = Document(self.buffer).summary()
                    markup = readable_article
                    markup = markup.encode("utf-8")
                except:
                    markup = self.buffer

            else:
                markup = self.buffer

            if requestHeaders.getHeader("content-encoding") == "gzip":
                
                
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

