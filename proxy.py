from monocles.lib.extract import Resource
from twisted.web import proxy, http
from twisted.python import log

from monocles.lib.proxy import gunzip, \
    is_gzipped, \
    accepts_gzipped, \
    gzip, \
    should_parse, \
    add_to_blacklist, \
    is_deflated, \
    deflate


log.startLogging(open('monocles.log', 'a'), setStdout=False)


class ProxyClient(proxy.ProxyClient):

    """
    Defines a bunch of handlers for events defined by the twisted
    proxyClient
    """
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.haveallheaders = False
        self.shouldparse = False


    def dataReceived(self, data):
        """
        This is basically for hacker news which doesn't put
        crlf at the end of headers
        """
        if not self.haveallheaders:
            if self.delimiter not in data and "\n" in data:
                data = data.replace("\n", self.delimiter)
                
        return proxy.ProxyClient.dataReceived(self, data)


    def handleResponsePart(self, data):
        """
        Handle requests that aren't being parsed like normal, so we
        write out data as we get the response. Otherwise we accumulate
        the article so we can do article extraction.
        """
        if self.shouldparse:
            self.buffer = self.buffer + data
        else:
            return proxy.ProxyClient.handleResponsePart(self, data)


    def handleEndHeaders(self):
        """
        This flag used in dataReceived, this function is in the http client
        """
        self.haveallheaders = True;
        self.shouldparse = should_parse(self.father)
        

    def handleResponseEnd(self):
        """
        This is the main function. Here we are at the end of the response
        and either we should parse it or we should just finish the response.

        We also modify the headers acccordingly, because we take this opportunity
        to gzip and do a few other things.
        """

        #bug in twisted (i think) which causes this method to be called twice, avoid problems
        # with this check
        if not self._finished:

            if should_parse(self.father):
                
                if is_gzipped(self.father.responseHeaders):
                    self.father.responseHeaders.removeHeader("content-encoding")
                    self.buffer = gunzip(self.buffer)
                elif is_deflated(self.father.responseHeaders):
                    self.father.responseHeaders.removeHeader("content-encoding")
                    self.buffer = deflate(self.buffer)

                resource = Resource(self.buffer, self.father.uri)
                
                if resource.should_bypass():
                    
                    self.father.write(self.buffer)

                    #in memory adds the domain to the blacklist. This usually
                    #helps to load the original site.
                    add_to_blacklist(self.father.uri)
                    if loggit:
                        log.msg("MONOCLES: %s" % self.father.uri)

                    return proxy.ProxyClient.handleResponseEnd(self)

                markup = resource.article
                
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



