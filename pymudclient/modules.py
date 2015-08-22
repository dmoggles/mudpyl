"""A modularisation system for triggers, aliases and macros."""
import sys

def load_file(name):
    """Load a module from a file.
    
    The module that this looks for is named MainModule, and it is expected
    to have a similar interface to those in modules.py.
    """
    if name in sys.modules:
        del sys.modules[name]
    pymod = __import__(name, globals(), locals(), ['MainModule'])
    return pymod.MainModule

class BaseModule(object):
    """A base class for modules."""

    triggers = []
    aliases = []
    macros = {}
    modules = []
    gmcp_events=[]
    encoding = 'utf-8'

    def __init__(self, manager):
        self.manager = manager
        manager.triggers.extend(self.triggers)
        manager.aliases.extend(self.aliases)
        manager.macros.update(self.macros)
        manager.gmcp_events.extend(self.gmcp_events)

    def is_main(self, realm):
        """We're the main module; do funky main module initialisation.
        
        This function will only be called once per session, by connect.py, so
        put everything (such as log opening, etc) that should only be done 
        once in here.
        """
        pass
    def get_gmcp_handler(self):
        return None
    
    
    def on_prompt(self, realm):
        pass
    
    def __hash__(self):
        return id(self)

class EarlyInitialisingModule(object):
    """A module that needs to be initialised in __init__ before it is loaded.
    """
    
    def __call__(self, manager):
        self.manager = manager
        manager.triggers.extend(self.triggers)
        manager.aliases.extend(self.aliases)
        manager.macros.update(self.macros)
        manager.gmcp_events.extend(self.gmcp_events)
        return self

    def is_main(self, realm):
        """Override me!"""
        pass
    
    def get_gmcp_handler(self):
        return None
    
    def on_prompt(self, realm):
        pass
    macros = {}
    triggers = []
    aliases = []
    modules = []
    gmcp_events=[]
    encoding = "utf-8"

    def __hash__(self):
        return id(self)
