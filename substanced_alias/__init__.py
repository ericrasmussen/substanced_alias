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
    """ Register @content, @view_config, and @mgmt_view. """
    config.scan('.')

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
        """ Finds an appropriate name checking function (name_checker) when
        an Alias is being newly added to a Folder and when an existing Alias
        is renamed.
        Otherwise we're not adding or changing a key, so it uses a default
        name_checker that always passes.
        """

        # case: context is a Folder
        if not IAlias.providedBy(context):
            name_checker = context.check_name

        # case: context is an Alias that is being renamed
        elif value != context.__name__:
            name_checker = context.__parent__.check_name

        # case: context is an Alias and the key isn't changing
        else:
            name_checker = lambda v: None

        # raise colander.Invalid if the chosen name_checker fails
        try:
            name_checker(value)
        except Exception as e:
            raise colander.Invalid(node, e.args[0], value)

    return colander.All(
        colander.Length(min=1, max=255),
        exists,
        )

@colander.deferred
def alias_resource_validator(node, kw):
    """ When adding or modifying an ``Alias``, ensures the resource is valid.
    """
    request = kw['request']
    context = request.context

    def exists(node, value):
        try:
            find_resource(request.root, value)
        except KeyError:
            raise colander.Invalid(node, 'Resource not found', value)

    return exists

class QueryParams(colander.SequenceSchema):
    key_value = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=1),
        widget = widget.TextInputWidget(),
        )

class AliasSchema(Schema):
    """ The property schema for ``Alias`` objects."""
    name = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(),
        validator=alias_name_validator,
        )
    resource = colander.SchemaNode(
        colander.String(),
        widget=keys_autocomplete_widget,
        validator=alias_resource_validator,
        )
    query = QueryParams()


class AliasPropertySheet(PropertySheet):
    schema = AliasSchema()

    def get(self):
        context = self.context
        props = {}
        props['name'] = context.name
        resource_path = self.request.resource_path(context.resource)
        props['resource'] = resource_path
        props['query'] = context.query
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
        query = struct['query']
        context.updatequery(query)


# TODO: add an anchor kw also
@content(
    IAlias,
    name='Alias',
    icon='icon-arrow-right',
    add_view='add_alias',
    propertysheets = (
        ('Basic', AliasPropertySheet),
        )
)
class Alias(Persistent):
    """ Object representing a resource alias."""

    def __init__(self, name, resource, query=None):
        self.name = name
        self.resource = resource
        self.query = query
        self._querydict = self.dict_from_query(query)

    def generate_url(self, request):
        """ Only use the ``query`` parameter if not None, otherwise it will
        append a '?' to every URL. """
        if self._querydict is None:
            return request.resource_url(self.resource)
        else:
            return request.resource_url(self.resource, query=self._querydict)

    def redirect(self, request):
        """ Perform a redirect."""
        url = self.generate_url(request)
        return HTTPFound(location=url)

    def dict_from_query(self, query):
        """ Turns a sequence of "key=value" or "key" strings into a dict. """
        if query == None:
            return None

        d = {}

        for item in query:
            key, sep, value = item.partition('=')
            d[key] = value

        return d

    def updatequery(self, query):
        """ Convenience method to reset both ``query`` and ``_querydict``. """
        self.query = query
        self._querydict = self.dict_from_query(query)
