#!/usr/bin/python
"""Connand-line script to hook you up to the MUD of your choice."""
#import pygtkcompat
#pygtkcompat.enable()
#pygtkcompat.enable_gtk()


import argparse
from pymudclient.client import Connector, ClientProtocol
from pymudclient import __version__
from pymudclient.library.imperian.imperian_gui import ImperianGui
import os
import sys
from twisted.python import filepath
from twisted.internet import reactor
from twisted.internet import stdio
parser = argparse.ArgumentParser(version = "%(prog)s " + __version__, 
                                 prog = 'pymudclient')

known_guis = ['gtk']
gui_help = ("The GUI to use. Available options: %s. Default: %%(default)s" %
                     ', '.join(known_guis))

parser.add_argument('-g', '--gui', default = 'gtk', help = gui_help,
                    choices = known_guis)
parser.add_argument('-p', '--processor', help = 'Path to Processor executable', required = True)
parser.add_argument("modulename", help = "The module to import")
parser.add_argument("--profile", action = "store_true",  default = False,
                    help = "Whether to profile exection. Default: False")





def _spawnProcess(proto, sibling, *args, **kw):
        """
        Launch a child Python process and communicate with it using the
        given ProcessProtocol.

        @param proto: A L{ProcessProtocol} instance which will be connected
        to the child process.

        @param sibling: The basename of a file containing the Python program
        to run in the child process.

        @param *args: strings which will be passed to the child process on
        the command line as C{argv[2:]}.

        @param **kw: additional arguments to pass to L{reactor.spawnProcess}.

        @return: The L{IProcessTransport} provider for the spawned process.
        """
        import twisted
        subenv = dict(os.environ)
        subenv['PYTHONPATH'] = os.pathsep.join(
            [os.path.abspath(
                    os.path.dirname(os.path.dirname(twisted.__file__))),
             ';'.join(sys.path),
             
             ])
        args = [sys.executable,
             filepath.FilePath(__file__).sibling(sibling).path,
             reactor.__class__.__module__] + list(args)
        return reactor.spawnProcess(
            proto,
            sys.executable,
            args,
            env=subenv,
            **kw) 
        
         
def main():
    """Launch the client.

    This is the main entry point. This will first initialise the GUI, then
    load the main module specified on the command line.
    """
    options = parser.parse_args()
    subenv = dict(os.environ)
    mod = __import__(options.modulename, fromlist = ["name", "host", "port", "configure", "encoding"])

    realm = Connector(mod)

    if options.gui == 'gtk':
        realm.extra_gui = ImperianGui(realm)
        from pymudclient.gui.gtkgui import configure
    
    processor_exec = options.processor
    
    configure(realm)

    

    #pylint kicks up a major fuss about these lines, but that's because 
    #Twisted does some hackery with the reactor namespace.
    #pylint: disable-msg=E1101

    if hasattr(mod, "configure"):
        mod.configure(realm)

    realm.client = ClientProtocol(realm)
    
    sp = reactor.callWhenRunning(_spawnProcess, realm.client, processor_exec)
    if not options.profile:
        reactor.run()
    else:
        import cProfile
        cProfile.runctx("reactor.run()", globals(), locals(),
                        filename = "pymudclient.prof")

if __name__ == '__main__':
    main()
