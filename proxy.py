from monocles.lib.extract import Resource
from twisted.web import proxy, http
from twisted.python import log

from monocles.lib.proxy import gunzip, \
    is_gzipped, \
    accepts_gzipped, \
    gzip, \
    should_parse


log.startLogging(open('monocles.log', 'a'), setStdout=False)
#TODO:
# strip logging query strings from URI before sending a request
# put a url in the top of the page that includes the bypass url and a bypass and loggit option
# include some basic css so that it's not so damn wide.



class ProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.haveallheaders = False
        self.shouldparse = False


    def dataReceived(self, data):
        #This is basically for hacker news which doesn't put
        #crlf at the end of headers
        if not self.haveallheaders:
            if self.delimiter not in data and "\n" in data:
                data = data.replace("\n", self.delimiter)
                
        return proxy.ProxyClient.dataReceived(self, data)


    def handleResponsePart(self, data):

        if self.shouldparse:
            self.buffer = self.buffer + data
        else:
            return proxy.ProxyClient.handleResponsePart(self, data)


    def handleEndHeaders(self):
        # this flag used in dataReceived, this function is in the http client
        self.haveallheaders = True;
        self.shouldparse = should_parse(self.father)
        

    def handleResponseEnd(self):

        if not self._finished:

            if should_parse(self.father):

                if is_gzipped(self.father.responseHeaders):
                    self.father.responseHeaders.removeHeader("content-encoding")
                    self.buffer = gunzip(self.buffer)

                resource = Resource(self.buffer, self.father.uri)

                
                if resource.should_bypass():
                    self.father.write(self.buffer)
                    if loggit:
                        log.msg("MONOCLES: %s" % self.father.uri)

                    return proxy.ProxyClient.handleResponseEnd(self)

                if len(resource.markup) > 500:
                    markup = resource.article
                else:
                    markup = self.buffer
                
                encodings = self.father.requestHeaders.getRawHeaders("accept-encoding")
                if accepts_gzipped(encodings):
                    self.father.responseHeaders.setRawHeaders("content-encoding", ["gzip"])
                    markup = gzip(markup)


                self.father.responseHeaders.setRawHeaders("content-length", [len(markup)])
                self.father.responseHeaders.setRawHeaders("content-type", ["text/html; charset=utf-8"])

                #TODO: turn off after done developing, for now don't ever cache anything.
                self.father.responseHeaders.removeHeader("etag")
                self.father.responseHeaders.setRawHeaders("cache-control", ["no-store",
                                                                             "no-cache",
                                                                             "must-revalidate",
                                                                             "post-check=0",
                                                                             "pre-check=0"])
            else:
                markup = self.buffer


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



