from pyramid.view import view_config
from pyramid.traversal import find_resource
from pyramid.httpexceptions import HTTPFound

from substanced.sdi import mgmt_view
from substanced.form import FormView

from substanced.interfaces import (
    ISite,
    IFolder,
)

from . import (
    IAlias,
    AliasSchema,
    get_matching_keys,
    objectid_for_resource,
)


@view_config(context=IAlias)
def default_alias_view(request):
    """ Default unprotected view for an ``Alias`` object. Uses the Alias's
    ``redirect`` method to send the visitor to the correct page.

    Note: this view is unprotected because it only performs the redirect. It
    does not know if the resource it redirects to exists or is protected.
    """
    context = request.context
    return context.redirect(request)

@mgmt_view(context=ISite, name='alias_key_lookup', permission='key lookup',
           renderer='json', tab_condition=False)
def alias_key_lookup(request):
    """ Used by Deform's autocomplete widget to return a list of possible
    completions.

    Ex.
      You have a resource foo/ containing bar, baz, and quux
      The user searches for foo/bar/b
      Keys returns a JSON representation of: ['foo/bar', 'foo/baz']
    """
    path = request.params.get('term', '')
    keys = get_matching_keys(request.context, path)
    return keys

@mgmt_view(context=IFolder, name='add_alias', permission='add alias',
           renderer='substanced.sdi:templates/form.pt',
           tab_condition=False)
class AddAliasView(FormView):
    """ Makes ``Alias`` objects addable to repoze.Folder objects or any object
    that inherits from it.
    """
    title = 'Add Alias'
    schema = AliasSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        name = appstruct['name']
        resource = find_resource(self.request.root, appstruct['resource'])
        query = appstruct['query']
        anchor = appstruct['anchor']
        inst = self.request.registry.content.create(
            IAlias, name, resource, query=query, anchor=anchor)
        self.context[name] = inst
        return HTTPFound(self.request.mgmt_path(inst, '@@properties'))


