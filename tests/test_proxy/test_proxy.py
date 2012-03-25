import monocles.lib.proxy as proxy
from nose.tools import with_setup


def test_should_bypass():

    url = "http://tomayko.com/writings/your-clever-weblog-title?bypass=true&loggit=true"
    bypass, loggit = proxy.should_bypass(url)
    assert bypass and loggit

    url = "http://tomayko.com/writings/your-clever-weblog-title?bypass=true"
    bypass, loggit = proxy.should_bypass(url)
    assert bypass and not loggit

    url = "http://tomayko.com/writings/your-clever-weblog-title?loggit=true"
    bypass, loggit = proxy.should_bypass(url)
    assert not bypass and loggit

    url = "http://tomayko.com/writings/your-clever-weblog-title"
    bypass, loggit = proxy.should_bypass(url)
    assert not bypass and not loggit



def test_get_bypass_urls():

    url = "http://tomayko.com/writings/your-clever-weblog-title"
    bypass = url + "?bypass=true"
    bypasslog = url + "?loggit=true&bypass=true"

    b, l = proxy.get_bypass_urls(url)
    assert b == bypass
    print l
    assert l == bypasslog

