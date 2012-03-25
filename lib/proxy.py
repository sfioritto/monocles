import urlparse
import urllib

def should_bypass(url):

    spliturl = url.split("?")

    if len(spliturl) > 1:
        
        querystring = spliturl[1]
        query = dict([tuple(pair.split("=")) for pair in querystring.split("&") if len(pair.split("=")) == 2])
        return query.has_key("bypass"), query.has_key("loggit")
    
    else:
        return False, False


def get_bypass_urls(url):
    
    bypassq = {"bypass" : "true"}
    loggitq = {"bypass" : "true",
               "loggit" : "true"}
    
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    
    query.update(bypassq)
    url_parts[4] = urllib.urlencode(query)
    bypass = urlparse.urlunparse(url_parts)
    
    query.update(loggitq)
    url_parts[4] = urllib.urlencode(query)
    loggit = urlparse.urlunparse(url_parts)

    return bypass, loggit
