from urlparse import urlparse, urljoin
import simplejson as json
from os.path import isfile
import jsonpath_rw
import requests
import logging


logging.basicConfig(level=logging.DEBUG)


def debug(message):
    logging.debug(message)
    
def info(message):
    logging.info(message)
    
cache = {}

class IdError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class URLFragment(object):

    def __init__(self):
        self.url_fragments = None

    def __init__(self, id_):
        self.id = id_
        if id is not None:
            self.url_fragments = urlparse(id_)
        else:
            self.url_fragments = None

    def __str__(self):
        return repr(self.id + ", " + str(self.url_fragments))


def resolveInFile(fragment, fileObj):
    debug("resolveInFile:: fragment->" + fragment)
    path_expr = jsonpath_rw.parse("$" + ".".join(fragment.split("/")))
    matched_values = [match.value for match in path_expr.find(fileObj)]
    debug("resolveInFile:: matches :: " + str(matched_values[0]))
    return matched_values[0] if len(matched_values) > 0 else None
    
#def parseAsFile(filename):

    
def parseAsHttp(url):
    debug("parseAsHttp::url -> " + url)
    json_dump = None
    if callable(requests.Response.json):
        json_dump = requests.get(url).json()
        debug(json_dump)
    else:
        json_dump = requests.get(url).json
    if 'id' in json_dump:
        _id  = json_dump.get('id')
        if _id not in cache:
            cache[_id] = resolve(json_dump)
        return cache[_id]
    else:
        raise IdError("$ref-ed file has no `id`. Will not continue parsing anything. Go fix it!")
        

def parseRef(fragment, value):
    ref_frag = urlparse(value)
    ref_file = ref_frag.netloc + ref_frag.path
    debug(value)
    # ref_frag ->ParseResult(scheme=u'http', netloc=u'localhost:3000', path=u'/ref_schema.json', params='', query='', fragment=u'/definitions/address')
    
    if ref_frag.scheme in ['http', 'https']:
        # http/https scheme retrieval of $refs
        _url = ref_frag.scheme + "://" + ref_file # -> http://localhost:3000/ref_schema.json
        http_file_json  = parseAsHttp(_url)
        debug("resolveInFile :: " +ref_frag.fragment)
        return resolveInFile(ref_frag.fragment, http_file_json)
    #elif fragment.url_fragments.scheme == 'file' and isfile(ref_file):
    # local file absolute and relative paths retrieval of $refs
    #    return parseAsFile(ref_file)
    #elif fragment.url_fragments.scheme == "":
    # same file internal $ref
    #    return parseAsFile(fragment.url_fragments.netloc + fragment.url_fragments.path)
    else:
        raise Exception("Scheme of resolution: " + fragment.url_fragments.scheme + " is currently not supported")
        

def update(fragment, key, value):
    if "$ref" == key:
        debug("update$ref:: " + key)
        parsedResult = parseRef(fragment, value)
        debug("update$ref to -> "+ str(parseRef(fragment, value)))
        return parsedResult
    else:
        return {key: apropose(fragment, value)}

def apropose(fragment, elem):
    debug("apropose:: ")
    if isinstance(elem, dict):
        return parse(fragment, elem)
    elif isinstance(elem, list):
        return map(lambda x: apropose(fragment, x), elem)
    else:
        return elem
        
def parse(fragment, json_dict):
    mut_dict = {}
    for (key,value) in json_dict.iteritems():
        debug("parse:: " + key)
        mut_dict.update(update(fragment, key, value))
    return mut_dict


def resolve(json_obj):
    """
    Resolves $ref in the `json_obj` and returns a `dict` that has inlined $ref elements.
    Raises an `IdError` if the `id` key is not present in the `json_obj`.
    """
    if 'id' not in json_obj:
        raise IdError("No `id` field in passed parameter")
    else:
        debug("resolve::" + json_obj.get('id'))
        return parse(URLFragment(json_obj.get("id")), json_obj)


if __name__ == "__main__":
    ejson = json.load(open('test_schema.json'))
    print resolve(ejson)