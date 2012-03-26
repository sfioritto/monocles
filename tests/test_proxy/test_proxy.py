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



def test_get_helper_urls():

    url = "http://tomayko.com/writings/your-clever-weblog-title"
    bypass = url + "?bypass=true"
    bypasslog = url + "?loggit=true&bypass=true"
    boilerpipe = url + "?boilerpipe=true"

    b, l, boiler = proxy.get_helper_urls(url)
    assert b == bypass
    assert l == bypasslog
    assert boilerpipe == boiler


def test_clean_and_add_styles():

    markup = open("tests/test_proxy/data/original.html").read()
    cleaned = open("tests/test_proxy/data/clean.html").read()

    bypass = "http://www.wired.com/epicenter/2012/03/ff_facebookipo/?bypass=true"
    loggit = "http://www.wired.com/epicenter/2012/03/ff_facebookipo/?bypass=true&loggit=true"
    boiler = "http://www.wired.com/epicenter/2012/03/ff_facebookipo/?boiler=true"
    result = proxy.styled_markup(markup, bypass, loggit, boiler)
    result = result.encode("utf-8")

#    with open("tests/test_proxy/data/clean.html", "w") as cleanedf:
#        cleanedf.write(result)

    assert result == cleaned
