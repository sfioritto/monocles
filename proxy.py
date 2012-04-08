from monocles.lib.extract import Resource
from twisted.web import proxy, http
from twisted.python import log
from StringIO import StringIO
from monocles.lib.proxy import get_helper_urls, \
    styled_markup, \
    gunzip, \
    is_gzipped, \
    should_parse

import gzip
import urlparse
import urllib



log.startLogging(open('monocles.log', 'a'), setStdout=False)
#TODO:
# strip logging query strings from URI before sending a request
# put a url in the top of the page that includes the bypass url and a bypass and loggit option
# include some basic css so that it's not so damn wide.



class ProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.haveAllHeaders = False


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

            resource = Resource(self.buffer, self.father.uri)
            
            if resource.should_bypass():
                self.father.write(self.buffer)
                if loggit:
                    log.msg("MONOCLES: %s" % self.father.uri)

                return proxy.ProxyClient.handleResponseEnd(self)
                

            ctype = self.father.responseHeaders.getRawHeaders("content-type")[0]
            if should_parse(ctype.lower()):

                if is_gzipped(self.father.responseHeaders):
                    self.father.responseHeaders.removeHeader("content-encoding")
                    self.buffer = gunzip(self.buffer)

                resource.set_content(self.buffer)
                markup = resource.markup
                
                #todo: write a gzipit function
                encodings = self.father.requestHeaders.getRawHeaders("accept-encoding")
                if encodings and "gzip" in encodings[0]:
                    self.father.responseHeaders.setRawHeaders("content-encoding", ["gzip"])
                    sio = StringIO()
                    gzf = gzip.GzipFile(fileobj=sio, mode="wb")
                    gzf.write(markup)
                    gzf.close()
                    markup = sio.getvalue()


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



