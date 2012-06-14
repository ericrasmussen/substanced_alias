from persistent import Persistent
from substanced.content import content
from pyramid.httpexceptions import HTTPFound
from substanced.property import PropertySheet
from deform import widget
import colander
from substanced.schema import Schema
from zope.interface import Interface
from pyramid.traversal import find_resource

def includeme(config): # pragma no cover
    """ This doesn't work yet. """


class IAlias(Interface):
    """ Interface representing an alias that can redirect to another resource.
    """

def get_matching_keys(root, path):
    """
    Parameters:
      ``root`` : a resource to be used as the starting point for traversal
      ``path`` : a unicode or string object

    Returns:
      Splits the ``path`` into a search term (after the last '/') and a
      container object (up to the last '/'), relative to ``root``.
      Returns a list of matching keys in the container prefixed by the search
      term, or [].
   """
    prefix, sep, term = path.rpartition('/')

    # return empty list if resource does not exist
    try:
        resource = find_resource(root, prefix)
    except KeyError:
        return []

    prefix += sep # ensure the prefix ends with a trailing slash

    return [prefix + key for key in resource.keys() if key.startswith(term)]


@colander.deferred
def keys_autocomplete_widget(node, kw):
    """ Finds the ``alias_key_lookup`` view and uses it for autocomplete ajax
    queries with Deform.
    """
    request = kw['request']
    url = request.mgmt_path(request.root, '@@alias_key_lookup')
    return widget.AutocompleteInputWidget(values=url)

@colander.deferred
def alias_name_validator(node, kw):
    """ When adding or renaming an ``Alias``, ensures that the name is not
    already a key in the current container (context).
    Also ensures names meet length requirements and do not contain a '/'.
    """
    request = kw['request']
    context = request.context

    def exists(node, value):
        is_new = not IAlias.providedBy(context)
        renaming = value != context.__name__
        if is_new or renaming:
            try:
                context.check_name(value)
            except Exception as e:
                raise colander.Invalid(node, e.args[0], value)

    def noslashes(node, value):
        if '/' in value:
            raise colander.Invalid(node, 'Name cannot contain a "/"', value)

    return colander.All(
        colander.Length(min=1, max=255),
        exists,
        noslashes,
        )

@colander.deferred
def alias_resource_validator(node, kw):
    """ When adding or modifying an ``Alias``, ensures the resource is valid.
    """
    request = kw['request']
    context = request.context

    def exists(node, value):
        try:
            find_resource(context, value)
        except KeyError:
            raise colander.Invalid(node, 'Resource not found', value)

    return exists

class AliasSchema(Schema):
    """ The property schema for ``Alias`` objects."""
    name = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(),
        )
    resource = colander.SchemaNode(
        colander.String(),
        widget=keys_autocomplete_widget,
        validator=alias_resource_validator,
        )

class AliasPropertySheet(PropertySheet):
    schema = AliasSchema()

    def get(self):
        context = self.context
        props = {}
        props['name'] = context.name
        resource_path = self.request.resource_path(context.resource)
        props['resource'] = resource_path
        return props

    def set(self, struct):
        context = self.context
        parent = context.__parent__
        newname = struct['name']
        oldname = context.name
        if newname != oldname:
            parent.rename(oldname, newname)
            context.name = newname
        resourcename = struct['resource']
        context.resource = find_resource(parent, resourcename)


# TODO: make elems part of the propertysheet
@content(
    IAlias,
    name='Alias',
    icon='icon-chevron-right',
    add_view='add_alias',
    propertysheets = (
        ('Basic', AliasPropertySheet),
        )
)
class Alias(Persistent):
    """ Object representing a resource alias."""

    def __init__(self, name, resource, elems=()):
        self.name = name
        self.resource = resource
        self.elems = elems

    def generate_url(self, request):
        return request.resource_url(self.resource, *self.elems)

    def redirect(self, request):
        url = self.generate_url(request)
        return HTTPFound(location=url)

