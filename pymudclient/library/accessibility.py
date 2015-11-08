'''
Created on Nov 7, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from accessible_output import speech
from pymudclient.triggers import binding_trigger

class ScreenreaderProtocol(BaseModule):
    
    def __init__(self, realm):
        BaseModule.__init__(self, realm)
        self.speaker = speech.Speaker()
        realm.addProtocol(self)
        realm.accessibility_mode = True
        
        
    @property
    def triggers(self):
        return [self.prompt_gag]
    
    @binding_trigger('^H:\d+')
    def prompt_gag(self, match, realm):
        realm.display_line=False
        
    
    def close(self):
        pass
    
    def connectionMade(self):
        """The realm sends out the 'coonection made at X' notes."""
        pass
    connectionLost = connectionMade
    
    def metalineReceived(self, metaline,channels):
        if 'main' in channels:
            self.speaker.output(metaline.line)