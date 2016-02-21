'''
Created on Oct 6, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.aliases import binding_alias



    
class WeaponMasteryCommands(BaseModule):
    
    @property
    def aliases(self):
        return [self.cleave,
                self.sunder,
                self.impale,
                self.disembowel,
                self.arc,
                self.barge,
                self.lunge]
    
    def single_command_alias(self, match, realm, command):
        realm.send_to_mud=False
        target=realm.root.get_state('target')
        realm.send('queue eqbal %s %s'%(command, target))
    
    
    @binding_alias('^clea$')
    def cleave(self, match, realm):
        realm.send_to_mud=False
        target=realm.root.get_state('target')
        realm.send('acoff')
        realm.send('queue eqbal cleave %s'%target)
        
        
    @binding_alias('^sund$')
    def sunder(self, match, realm):
        realm.send('acoff')
        self.single_command_alias(match, realm, 'sunder')
        
    @binding_alias('^impa$')
    def impale(self, match, realm):
        self.single_command_alias(match, realm, 'impale')
        
    @binding_alias('^dise$')
    def disembowel(self, match, realm):
        self.single_command_alias(match, realm, 'disembowel')
        
    @binding_alias('^aoe$')
    def arc(self, match, realm):
        realm.send_to_mud=False
        realm.send('queue eqbal quickdraw broadsword shield|arc')
    
    @binding_alias('^bar(ne|n|nw|w|sw|s|se|e|ou|in|up|do)$')
    def barge(self, match, realm):
        realm.send_to_mud = False
        target = realm.root.get_state('target')
        direction = match.group(1)
        realm.send('queue eqbal barge %s %s'%(target, direction))
    
    @binding_alias('^lun$')
    def lunge(self, match, realm):
        realm.send_to_mud = False
        target = realm.root.get_state('target')
        realm.send('queue eqbal lunge %s'%target)
 