'''
Created on Feb 9, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.aliases import binding_alias
from pymudclient.triggers import binding_trigger

class Dances(EarlyInitialisingModule):
    def __init__(self, manager):
        self.elusion=False
        self.beguile = False
        self.bemuse = False
        self.sentinel = False
        
        self.manager = manager
        
        self.timer = None
        self.last_two_seen =['','']
        
        
    @property
    def aliases(self):
        return [self.doubledance,
                self.wardance]
    
    @property
    def triggers(self):
        return [self.beguile_tr,
                self.bemuse_tr,
                self.sentinel_tr,
                self.elusion_tr]
    
    @binding_alias('^dd (\w+) (\w+)$')
    def doubledance(self, matches, realm):
        realm.send_to_mud = False
        realm.send('doubledance %s %s'%(matches.group(1), matches.group(2)))
    
    
    @binding_alias('^wd (\w+)$')
    def wardance(self, matches, realm):
        realm.send_to_mud = False
        realm.send('wardance %s'%matches.group(1))
    
    
    @binding_trigger('Twirling your blade, you continue your beguiling dance\.')
    def beguile_tr(self, matches, realm):
        self.seen_dance('beguile', realm)
        
    @binding_trigger('You continue the confusing, erratic dance\.')
    def bemuse_tr(self, matches, realm):
        self.seen_dance('bemuse', realm)
        
    @binding_trigger('Stomping the ground, you continue the dance of the sentinel\.')
    def sentinel_tr(self, matches, realm):
        self.seen_dance('sentinel', realm)
        
    @binding_trigger('Lightfooted, you continue the elusive dance\.')
    def elusion_tr(self, matches, realm):
        self.seen_dance('elusion', realm)
        
    def seen_dance(self, dance, realm):
        realm.display_line=False
        self.last_two_seen.pop(0)
        self.last_two_seen.append(dance)
        
        for s in self.last_two_seen:
            if s == 'beguile':
                self.beguile = True
            elif s == 'bemuse':
                self.bemuse = True
            elif s == 'elusion':
                self.elusion = True
            elif s == 'sentinel':
                self.sentinel = True
            if self.timer!=None and self.timer.active():
                self.timer.cancel()
              
            self.timer = realm.root.set_timer(14, self.reset_dances)
            self.make_prompt_line()
    
    def reset_dances(self, realm):
        self.last_two_seen=['','']
        self.beguile = False
        self.bemuse = False
        self.elusion = False
        self.sentinel = False
        self.make_prompt_line()
        
    def make_prompt_line(self):
        line = '<blue*>DC:'
        lines =[]
        if self.beguile:
            lines.append('<blue>BG')
        if self.bemuse:
            lines.append('<blue>BM')
        if self.sentinel:
            lines.append('<blue>ST')
        if self.elusion:
            lines.append('<blue>EL')
        line+=','.join(lines)
        if len(lines)>0:
            self.manager.fireEvent('promptDataEvent','dances',line)
        else:
            self.manager.fireEvent('promptDataEvent','dances','')
        
    
    

        