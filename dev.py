from twisted.web import http
from twisted.internet import reactor
from monocles.proxy import Proxy

factory = http.HTTPFactory()
factory.protocol = Proxy

reactor.listenTCP(8080, factory)
reactor.run()
