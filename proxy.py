from twisted.web import proxy, http
from twisted.python import log
from twisted.internet import reactor
from readability.readability import Document
from StringIO import StringIO
from boilerpipe.extract import Extractor
from monocles.lib.proxy import helper_options, \
    get_helper_urls, \
    styled_markup, \
    gunzip, \
    is_gzipped, \
    should_parse

import gzip
import urlparse
import urllib



log.startLogging(open('/var/log/monocles.log', 'a'), setStdout=False)
#TODO:
# strip logging query strings from URI before sending a request
# put a url in the top of the page that includes the bypass url and a bypass and loggit option
# include some basic css so that it's not so damn wide.



class ProxyClient(proxy.ProxyClient):
    
    def __init__(self, *args, **kwargs):
        proxy.ProxyClient.__init__(self, *args, **kwargs)
        self.buffer = ""
        self.text = False
        self.haveAllHeaders = False


    def handleHeader(self, key, value):
        #TODO: probably don't need to do this, can get headers on self.father

        if key == "Content-Type" and should_parse(value.lower()):
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
            bypass, loggit, boiler = helper_options(self.father.uri)
            
            if bypass:
                self.father.write(self.buffer)
                if loggit:
                    log.msg("MONOCLES: %s" % self.father.uri)

                return proxy.ProxyClient.handleResponseEnd(self)

            if is_gzipped(self.father.responseHeaders):
                self.father.responseHeaders.removeHeader("content-encoding")
                self.buffer = gunzip(self.buffer)


            if self.text:
                try:
                    if boiler:
                        extractor = Extractor(extractor='ArticleExtractor', html=self.buffer)
                        readable_article = extractor.getHTML()
                    else:
                        readable_article = Document(self.buffer).summary()
                        
                    #todo: better way to determine if you shouldn't try to beautify the document.
                    if len(readable_article) > 250: 

                        bypass, loggit, boiler = get_helper_urls(self.father.uri)
                        markup = styled_markup(readable_article, bypass, loggit, boiler)

                        #accept-charset was set to only utf-8, so assuming
                        #the response is encoded as utf-8. we'll see how that works out...
                        #todo: it didn't work out. sometimes you get no charset and you need to
                        #default to what the http spec says you should. you'll have to look it up.
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
            self.father.responseHeaders.removeHeader("etag")
            self.father.responseHeaders.setRawHeaders("cache-control", ["no-store",
                                                                         "no-cache",
                                                                         "must-revalidate",
                                                                         "post-check=0",
                                                                         "pre-check=0"])

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

