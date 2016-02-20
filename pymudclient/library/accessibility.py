'''
Created on Nov 7, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from accessible_output import speech
from pymudclient.triggers import binding_trigger



class ScreenreaderProtocol():
    
    def __init__(self, client):
        self.speaker = speech.Speaker()
        client.addProtocol(self)
        client.user_echo = False
        
        
    
        
    
    def close(self):
        pass
    
    def connectionMade(self):
        """The realm sends out the 'coonection made at X' notes."""
        pass
    connectionLost = connectionMade
    
    def metalineReceived(self, metaline):
        if 'main' in metaline.channels:
            self.speaker.output(metaline.line)
            
            
class ScreenreaderModule(BaseModule):
   
        
    @property
    def triggers(self):
        return [self.prompt_gag]
    
    @binding_trigger('^H:\d+')
    def prompt_gag(self, match, realm):
        realm.display_line=False