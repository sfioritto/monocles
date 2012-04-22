import monocles.lib.proxy as proxy
import monocles.lib.extract as extract
from nose.tools import with_setup


def test_helper_options():

    url = "http://tomayko.com/writings/your-clever-weblog-title?bypass=true&loggit=true"
    bypass = extract.helper_options(url)
    assert bypass

    url = "http://tomayko.com/writings/your-clever-weblog-title?loggit=true"
    bypass = extract.helper_options(url)
    assert not bypass

    url = "http://tomayko.com/writings/your-clever-weblog-title"
    bypass = extract.helper_options(url)
    assert not bypass

    url = "http://tomayko.com/writings/your-clever-weblog-title?boilerpipe=true"
    bypass = extract.helper_options(url)
    assert not bypass


def test_get_helper_urls():

    url = "http://news.ycombinator.com/item?id=3758048"
    bypass = url + "&bypass=true"
    b = extract.get_helper_urls(url)
    assert b == bypass


def test_clean_and_add_styles():

    markup = open("tests/test_proxy/data/original.html").read()
    cleaned = open("tests/test_proxy/data/clean.html").read()
    result = extract.styled_markup(markup, "http://www.wired.com/epicenter/2012/03/ff_facebookipo/")
    result = result.encode("utf-8")

    assert result == cleaned
