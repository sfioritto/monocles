from twisted.application.internet import TCPClient
from twisted.application.service import Application
from monocles.proxy import factory

application = Application("monocles")
service = TCPClient("localhost", 8080, factory)
service.setServiceParent(application)
