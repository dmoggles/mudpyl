"""Utilities and stuff for HTML logging."""
from cgi import escape
from pymudclient.modules import BaseModule
from pymudclient.colours import fg_code, bg_code, WHITE, BLACK, GREY, HexFGCode
import time
import os

class HTMLLogOutput(object):
    """Handles the HTML log."""
   
    #these may be overriden in subclasses if they want to log in some other
    #way using different pre/postambles.
    log_preamble = '''
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<style>
body {
    background: black;
    font-family: monospace;
    font-size: 8pt;
}
</style>
</head>
<body>
<span style="color: #B0B0B0; background: #000000">
<pre>
'''

    log_postamble = '''
</span>
</pre>
</body>
</html>
'''

    colour_change = '''</span><span style="color: #%s; background: #%s">'''

    def __init__(self, client, logformat):
        self.fore = fg_code(WHITE, False)
        self.back = bg_code(BLACK)
        self.client = client
        self._dirty = False
        client.addProtocol(self)
        logname=time.strftime(logformat)%{'name':self.client.mod.name}
        if not os.path.exists(os.path.dirname(logname)):
            os.makedirs(os.path.dirname(logname))
        self.log = open(time.strftime(logformat) % 
                                   {'name': self.client.mod.name}, 'w+')
        self.log.write(self.log_preamble)

    def write_out_span(self, span):
        """Write a span of coloured text to the log, using our most recent
        colour setup.
        """
        self.log.write(escape(span))

    def change_colour(self):
        """The change itself is useless, as we'd have to write a new <span>
        anyway with both foreground and background, so use common code for
        both types of change.
        """
        self.log.write(self.colour_change % (self.fore.as_hex, 
                                             self.back.as_hex))
        self._dirty = False

    def close(self):
        """Clean up."""
        if self.log is not None:
            self.log.write(self.log_postamble)
            self.log.close()

    def connectionMade(self):
        """The realm sends out the 'coonection made at X' notes."""
        pass
    connectionLost = connectionMade

    def metalineReceived(self, metaline):
        """Write the line to the logs.
        
        This breaks the string up into coloured chunks, and feeds them to
        the log separately."""
        channels = metaline.channels
        if len(channels)>0 and not 'main' in channels:
            return
        if metaline.line[0]=='\n':
            ts_string='[%s] '%time.strftime('%H:%M:%S')
            metaline.insert(1,ts_string)
            metaline.change_fore(1, len(ts_string)+1, HexFGCode(0x80, 0x80, 0x80))
        line = metaline.line
        
        
        #the indices are relative to the original string, not the previous
        #index, so we need to track what the previous index was to figure out
        #how much of the string needs to be coloured.
        oldind = 0

        for ind, change in sorted(metaline.fores.items() +
                                  metaline.backs.items()):
            #calculate the length of the previous bit of coloured string
            inddiff = ind - oldind
            if len(line) >= inddiff > 0:
                if self._dirty:
                    self.change_colour()
                self.write_out_span(line[:inddiff])
            if change.ground == 'back':
                self._dirty = self.back != change
                self.back = change
            elif change.ground == 'fore':
                self._dirty = self.fore != change
                self.fore = change
            else:
                raise RuntimeError("Dunno what %r is." % change)
            line = line[inddiff:]
            oldind = ind
        
        if self._dirty:
            self.change_colour()
        if line:
            self.write_out_span(line)

class HTMLLoggingModule():
    """A module that logs to disk."""

    #defaultly log to a file in ~/logs/
    def __init__(self, client, logplace=None):
        if logplace == None:
            logplace = os.path.join(os.path.expanduser('~'), 'logs',
                            '%%(name)s/log_%Y_%m_%d__%H_%M_%S.html')
            HTMLLogOutput(client, logplace)


