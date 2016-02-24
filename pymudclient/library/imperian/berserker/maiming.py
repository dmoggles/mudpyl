'''
Created on Feb 24, 2016

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.aliases import binding_alias


class MaimingCommands(BaseModule):
    
    @property
    def aliases(self):
        return [self.fleche,
                self.entrench]
    
    
    @binding_alias('^fl$')
    def fleche(self, match, realm):
        realm.send_to_mud = False
        target = realm.root.get_state('target')
        realm.send('queue eqbal blade fleche %s'%target)
        
    @binding_alias('^sen$')
    def entrench(self, match, realm):
        realm.send_to_mud = False
        realm.send('acoff')
        realm.send('shield entrench')