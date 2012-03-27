from twisted.web import http
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from monocles.proxy import Proxy

factory = http.HTTPFactory()
factory.protocol = Proxy

application = Application("monocles")
service = TCPServer(80, factory)
service.setServiceParent(application)
