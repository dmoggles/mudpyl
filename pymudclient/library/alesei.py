from pymudclient.library.html import HTMLLoggingModule
from pymudclient.library.imperian.imperian_gui import ImperianGui
from pymudclient.modules import BaseModule
import pymudclient
name = 'Alesei'
host = 'imperian.com'
port = 23
encoding = 'ascii'
gmcp_handshakes=['Core.Hello { "client": "pymudclient", "version": "'+ pymudclient.__version__ +'" }',
                 'Core.Supports.Set [ "Core 1", "Char 1", "Char.Name 1", "Char.Skills 1", "Char.Items 1", "Comm.Channel 1", "Redirect 1", "Room 1", "IRE.Rift 1", "IRE.Composer 1" ]']
use_blocks = True

def configure(realm):
    HTMLLoggingModule(realm)
    
    
def gui_configure(realm):
    realm.extra_gui=ImperianGui(realm)

class MainModule(BaseModule):

    def __init__(self, manager):
        BaseModule.__init__(self, manager)