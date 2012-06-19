from pyramid.events import subscriber
from pyramid.security import Allow

from substanced.interfaces import IObjectAdded

from . import IAlias

@subscriber([IAlias, IObjectAdded])
def on_add(obj, event):
    """ Connect an ``Alias`` to a resource. This occurs as a callback rather
    than __init__ because the objectmap requires the ``Alias`` to be persisted.
    """
    obj.connect_to_resource_callback()

