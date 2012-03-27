from twisted.application.internet import TCPServer
from twisted.application.service import Application
from monocles.proxy import factory

application = Application("monocles")
service = TCPServer(80, factory)
service.setServiceParent(application)
