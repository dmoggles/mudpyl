'''
Created on Jan 5, 2016

@author: Dmitry
'''
import os
import sys
from twisted.python import filepath

def spawnProcess(proto, sibling, *args, **kw):
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
        from twisted.internet import reactor
        import twisted
        subenv = dict(os.environ)
        subenv['PYTHONPATH'] = os.pathsep.join(
            [os.path.abspath(
                    os.path.dirname(os.path.dirname(twisted.__file__))),
             ';'.join(sys.path),
             
             ])
        args = [sys.executable,
             filepath.FilePath(__file__).sibling(sibling).path#,
             #reactor.__class__.__module__] 
             ]+ list(args)
        print(args)
        return reactor.spawnProcess(
            proto,
            sys.executable,
            args,
            env=subenv,
            **kw) 