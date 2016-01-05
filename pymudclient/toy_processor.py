'''
Created on Jan 5, 2016

@author: Dmitry
'''
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ProcessProtocol
import json
import os
import sys
from twisted.python import filepath
from twisted.internet import reactor

class ToyProcessor(LineReceiver):
    '''
    classdocs
    '''
    def __init__(self):
        pass
       

    def lineReceived(self, line):
        meth, rest = line.split('|')
        if meth == 'ping':
            self.transport.write('ping received, %s'%rest)
            
            


class ToyProcessorProtocol(LineReceiver, ProcessProtocol):
    def __init__(self):
        self.communicator='test'
    def send_to_client(self, meth, params):
        print('send to processor: %s, %s'%(meth, json.dumps(params)))
        self.transport.write(json.dumps([meth, params]) + "\n")

    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        LineReceiver.connectionMade(self)
        self.transport.disconnecting = False #erm. Needs this to fix a bug in Twisted?
        self.send_to_client("hello", [self.communicator])
        self.send_to_client("close",[])
        
    def lineReceived(self, line):
        print('received line %s'%line)
        
    def errReceived(self, data):
        print('ERROR: %s'%data)
    
    outReceived = LineReceiver.dataReceived
        
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
             subenv.get('PYTHONPATH', '')
             ])
        print(subenv['PYTHONPATH'])
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
    

    prot = ToyProcessorProtocol()
    
    reactor.callWhenRunning(_spawnProcess, prot, 'processorconnect.py')
    reactor.run()
    
if __name__=='__main__':
    main()