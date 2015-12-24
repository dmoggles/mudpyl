from twisted.protocols.basic import LineReceiver
from pymudclient.escape_parser import EscapeParser
import json
from pymudclient.metaline import json_to_metaline, metaline_to_json



class MudProcessor(LineReceiver):
    delimiter = "\n"
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self):
        self._escape_parser=EscapeParser()
        self.macros = {}
        self.log=open(r'c:\temp\log_process.log','w')
        self.log.write('Init MudProcessor')
        
    def connectionMade(self):
        self.log.write('ConnectionMade')
        self.transport.write(json.dumps(["hello", [self.macros]]) + "\n")
        
    def lineReceived(self, line):
        meth,rest = json.loads(line)
        if meth == "close":
            #XXX: do better
            self.transport.loseConnection()
            from twisted.internet import reactor
            reactor.stop()
        elif meth == "hello":
            self.log.write('Hello received')
            name = rest[0]
            self.name = name
        elif meth == 'mud_line':
            metaline = json_to_metaline(rest[0])
            display_line = bool(rest[1])
            self.match_triggers(metaline, display_line)
            self.transport.write(json.dumps(['display_line', [metaline_to_json(metaline), 1]]))
        elif meth == 'user_line':
            line = rest[0]
            self.transport.write(json.dumps(['send_to_mud',[line]]))
        elif meth == 'do_block':
            lines = json.loads(rest[0])
            for l in lines:
                self.transport.write(json.dumps(['display_line',[l]]))
            
        
        else:
            raise ValueError("bad line: %s" % line)
        self.transport.write(json.dumps(["ack", []]) + "\n")