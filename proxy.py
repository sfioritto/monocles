from twisted.web import proxy, http
from twisted.internet import reactor
from readability.readability import Document
import urllib

class MonoclesProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.text = False

    def handleHeader(self, key, value):
        if key == "Content-Type" and value == "text/html":
            self.text = True
        proxy.ProxyClient.handleHeader(self, key, value)

    def handleResponsePart(self, buffer):
        self.buffer += buffer

    def handleResponseEnd(self):
        if not self._finished:
            if self.text:
                readable_article = Document(self.buffer).summary()
                readable_title = Document(self.buffer).short_title()
                text = readable_article
                text = text.encode("utf-8")
            else:
                text = self.buffer
            self.father.responseHeaders.setRawHeaders("content-length", [len(text)])
            self.father.write(text)
        proxy.ProxyClient.handleResponseEnd(self)


class MonoclesProxyClientFactory(proxy.ProxyClientFactory):
    protocol = MonoclesProxyClient

class ProxyRequest(proxy.ProxyRequest):
    
    protocols = {'http': MonoclesProxyClientFactory}
    ports = {'http': 80 }
    
    def process(self):
        proxy.ProxyRequest.process(self)
        

class MonoclesProxy(http.HTTPChannel):
    requestFactory = ProxyRequest

factory = http.HTTPFactory()
factory.protocol = MonoclesProxy

reactor.listenTCP(8080, factory)
reactor.run()

