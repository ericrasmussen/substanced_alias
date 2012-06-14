import unittest
import colander
from pyramid import testing
from zope.interface import (
    alsoProvides,
    implementer,
    )
from substanced.interfaces import IFolder


class TestAlias(unittest.TestCase):
    def _makeOne(self, name, resource, elems=()):
        from .. import Alias
        return Alias(name, resource, elems)

    def test_ctor(self):
        resource = testing.DummyResource()
        inst = self._makeOne('test', resource)
        self.assertEqual(inst.name, 'test')
        self.assertEqual(inst.resource, resource)

    def test_generate_url(self):
        resource = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne('test', resource, ['a', 'b'])
        url = inst.generate_url(request)
        self.assertEqual(url, 'http://example.com/a/b')

    def test_generate_url_nested_resource(self):
        request = testing.DummyRequest()
        request.root = DummyFolder()
        resource = testing.DummyResource()
        request.root['myresource'] = resource
        request.context = resource
        inst = self._makeOne('test', resource, ['a', 'b'])
        url = inst.generate_url(request)
        self.assertEqual(url, 'http://example.com/myresource/a/b')

    def test_redirect(self):
        resource = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne('test', resource)
        resp = inst.redirect(request)
        self.assertEqual(resp.code, 302)


class Test_keys_autocomplete_widget(unittest.TestCase):
    def _makeOne(self, request):
        from .. import keys_autocomplete_widget
        node = object()
        kw = {'request':request}
        return keys_autocomplete_widget(node, kw)

    def test_serialize_url(self):
        import json
        from deform.tests.test_widget import (
            DummyRenderer,
            DummyField,
            DummySchema,
            )
        request = testing.DummyRequest()
        request.mgmt_path = lambda req, name: 'myurl'
        widget = self._makeOne(request)
        renderer = DummyRenderer()
        schema = DummySchema()
        field = DummyField(schema, renderer=renderer)
        cstruct = 'abc'
        widget.serialize(field, cstruct)
        self.assertEqual(renderer.template, widget.template)
        self.assertEqual(renderer.kw['field'], field)
        self.assertEqual(renderer.kw['cstruct'], cstruct)
        self.assertEqual(renderer.kw['options'],
                         '{"delay": 400, "minLength": 2}')
        self.assertEqual(renderer.kw['values'],
                         json.dumps('myurl'))


class Test_alias_name_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import alias_name_validator
        return alias_name_validator(node, kw)

    def _makeKw(self):
        request = testing.DummyRequest()
        request.context = DummyFolder()
        return dict(request=request)

    def test_not_adding_with_exception(self):
        kw = self._makeKw()
        kw['request'].context['abc'] = testing.DummyResource()
        node = object()
        validator = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, validator, node, 'abc')

    def test_adding_with_exception(self):
        from .. import IAlias
        kw = self._makeKw()
        context = kw['request'].context
        context['abc'] = testing.DummyResource()
        alsoProvides(context, IAlias)
        node = object()
        validator = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, validator, node, 'abc')

    def test_adding_no_exception(self):
        kw = self._makeKw()
        node = object()
        validator = self._makeOne(node, kw)
        self.assertEqual(None, validator(node, 'abc'))

    def test_slash_in_name_exception(self):
        kw = self._makeKw()
        node = object()
        validator = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, validator, node, 'a/b')

class Test_alias_resource_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import alias_resource_validator
        return alias_resource_validator(node, kw)

    def _makeKw(self):
        request = testing.DummyRequest()
        request.context = DummyFolder()
        return dict(request=request)

    def test_valid_resource(self):
        context = DummyFolder()
        context['a'] = DummyFolder()
        context['a']['b'] = testing.DummyResource()
        kw = self._makeKw()
        kw['request'].context = context
        node = object()
        validator = self._makeOne(node, kw)
        self.assertEqual(None, validator(node, 'a/b'))

    def test_invalid_resource(self):
        context = DummyFolder()
        kw = self._makeKw()
        kw['request'].context = context
        node = object()
        validator = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, validator, node, 'bad/path')


class TestAliasPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import AliasPropertySheet
        return AliasPropertySheet(context, request)

    def _makeContext(self, resource):
        context = testing.DummyResource()
        context.__name__ = 'name'
        context.name = 'name'
        context.resource = resource
        return context

    def test_get_properties(self):
        parent = DummyFolder()
        resource = testing.DummyResource()
        parent['resource'] = resource
        context = self._makeContext(resource)
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        props = inst.get()
        self.assertEqual(props['name'], 'name')
        self.assertEqual(props['resource'], '/resource/')

    def test_set_properties(self):
        root = DummyFolder()
        resource = testing.DummyResource()
        root['resource'] = resource
        context = self._makeContext(resource)
        context.__parent__ = root
        root['name'] = context
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        struct = dict(name='newname', resource='resource')
        inst.set(struct)
        self.assertIn('newname', root)
        self.assertEqual(context.name, 'newname')
        self.assertEqual(context.resource, resource)

class Test_get_matching_keys(unittest.TestCase):
    def _makeOne(self):
        from .. import get_matching_keys
        return get_matching_keys

    def test_root_search(self):
        inst = self._makeOne()
        root = DummyFolder()
        root['a1'] = testing.DummyResource()
        root['a2'] = testing.DummyResource()
        root['b1'] = testing.DummyResource()
        result = inst(root, 'a')
        result.sort()
        self.assertEqual(result, ['a1', 'a2'])

    def test_non_root_search(self):
        inst = self._makeOne()
        root = DummyFolder()
        root['a_ignored'] = testing.DummyResource()
        root['relative'] = DummyFolder()
        root['relative']['a_found'] = testing.DummyResource()
        result = inst(root['relative'], 'a')
        self.assertEqual(result, ['a_found'])

    def test_empty_search(self):
        inst = self._makeOne()
        root = DummyFolder()
        root['a'] = DummyFolder()
        result = inst(root, '')
        self.assertEqual(result, ['a'])

    def test_nested_serach(self):
        inst = self._makeOne()
        root = DummyFolder()
        root['a'] = DummyFolder()
        root['a']['b'] = DummyFolder()
        root['a']['b']['c'] = testing.DummyResource()
        result = inst(root, 'a/b/')
        self.assertEqual(result, ['a/b/c'])

    def test_invalid_search(self):
        inst = self._makeOne()
        root = DummyFolder()
        result = inst(root, 'bad/key')
        self.assertEqual(result, [])

@implementer(IFolder)
class DummyFolder(testing.DummyResource):

    def check_name(self, value):
        if value in self:
            raise KeyError(value)

    def rename(self, oldname, newname):
        old = self[oldname]
        del self[oldname]
        self[newname] = old

