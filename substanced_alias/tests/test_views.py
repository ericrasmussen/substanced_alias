import unittest
from . import DummyFolder
from pyramid import testing

class Test_default_alias_view(unittest.TestCase):
    def _makeOne(self):
        from ..views import default_alias_view
        return default_alias_view

    def test_it(self):
        from pyramid.httpexceptions import HTTPFound
        inst = self._makeOne()
        request = testing.DummyRequest()
        context = testing.DummyResource()
        context.redirect = lambda req: HTTPFound(location='http://example.com')
        request.context = context
        resp = inst(request)
        self.assertEqual(resp.code, 302)
        self.assertEqual(resp.location, 'http://example.com')

class Test_alias_key_lookup(unittest.TestCase):
    def _makeOne(self):
        from ..views import alias_key_lookup
        return alias_key_lookup

    def _makeRequest(self):
        request = testing.DummyRequest()
        root = DummyFolder()
        root['foo'] = DummyFolder()
        root['foo']['bar'] = testing.DummyResource()
        root['foo']['baz'] = testing.DummyResource()
        root['foo']['qux'] = testing.DummyResource()
        request.context = root
        return request

    def test_match(self):
        request = self._makeRequest()
        request.params['term'] = 'foo/b'
        inst = self._makeOne()
        result = inst(request)
        result.sort()
        expected = ['foo/bar', 'foo/baz']
        self.assertEqual(result, expected)

    def test_no_match(self):
        request = self._makeRequest()
        request.params['term'] = 'bad/path'
        inst = self._makeOne()
        result = inst(request)
        self.assertEqual(result, [])


class TestAddAliasView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import AddAliasView
        return AddAliasView(context, request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        root = DummyFolder()
        root['test'] = testing.DummyResource()
        request.context = root
        request.root = root
        return request

    def test_add_success(self):
        resource = testing.DummyResource()
        request = self._makeRequest(resource)
        inst = self._makeOne(request.context, request)
        struct = dict(name='name', resource='test')
        resp = inst.add_success(struct)

class DummyContent(object):
    def __init__(self, resource):
        self.resource = resource

    def create(self, iface, *arg, **kw):
        return self.resource
