from twisted.internet import reactor
from monocles.proxy import factory

reactor.listenTCP(8080, factory)
reactor.run()
