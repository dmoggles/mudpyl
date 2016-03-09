'''
Created on Feb 9, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.aliases import binding_alias
from pymudclient.triggers import binding_trigger
import time
from pymudclient.library.imperian.berserker.sword_combo import SwordCombo1
from pymudclient.library.imperian.berserker.rampage import RampageCommands
from pymudclient.library.imperian.berserker.maiming import MaimingCommands

class BerskerComboMaker(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, 
                 manager, 
                 shield_maiming, 
                 rage, 
                 shield_status, 
                 dances, 
                 aff_tracker,
                 toxin_priority,
                 warchants):
        self.manager = manager
        self.shield_maiming=shield_maiming
        self.rage = rage
        self.raze= shield_status
        self.dances = dances
        self.tracker = aff_tracker
        self.toxin_list = toxin_priority
        self.warchants = warchants
        self.hp = 0
        self.max_hp = 0
        self.mana = 0
        self.max_mana = 0
        self.next_balance=0
        self.next_equilibrium=0
        self.sword_combo = SwordCombo1(self.tracker)
        self.manager.registerEventHandler('afflictionGainedEvent',self.send_prompt_info)
        self.manager.registerEventHandler('afflictionLostEvent',self.send_prompt_info)
        
    @property
    def aliases(self):
        return [self.pk,
                self.auto_macro]
    
    @property
    def triggers(self):
        return [self.on_balance,
                self.on_equilibrium,
                self.trueassess]
    
    @property
    def macros(self):
        return {'<F1>':'delayed_pk'}
    
    @property
    def modules(self):
        return [RampageCommands,
                MaimingCommands]
    
    @binding_trigger("^(\w+)'s condition stands at (\d+)\/(\d+) health and (\d+)\/(\d+) mana\.$")
    def trueassess(self, match, realm):
        target = realm.root.get_state('target').lower()
        name = str(match.group(1)).lower()
        self.hp = int(match.group(2))
        self.max_hp = int(match.group(3))
        self.mana = int(match.group(4))
        self.max_mana = int(match.group(5))
            
#         realm.send('rt %(name)s - %(hp)dh [%(hppct)d%% m:%(mppct)d%%]'%{'name':name,
#                                                                             'hp':self.hp,
#                                                                             'hppct':int((float(self.hp)/float(self.max_hp))*100),
#                                                                             'mppct':int((float(self.mana)/float(self.max_mana))*100)})
#         
        
        if target==name:
            realm.root.fireEvent('targetStatUpdateEvent','hp',self.hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana',self.mana)
            realm.root.fireEvent('targetStatUpdateEvent','hp_max',self.max_hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana_max',self.max_mana)
        
    
    def send_prompt_info(self, event_target, affs):
        target = self.manager.root.get_state('target').lower()
        if not target==event_target: 
            return
        if self.warchants.get_weaken_count(target)>0:
            wkn_prompt_line='<cyan*>WKN:<red*>%d'%self.warchants.get_weaken_count(target)
        else:
            wkn_prompt_line = ""
        self.manager.root.fireEvent('promptDataEvent','weaken_count',wkn_prompt_line)
    
    @binding_trigger('^Balance Taken: (\d+\.\d+)s$')
    def on_balance(self, match, realm):
        #realm.root.set_state('attack_queued',False)
        self.next_balance=time.time()+float(match.group(1))
        
       
    @binding_trigger('^Equilibrium Taken: (\d+\.\d+)s$')
    def on_equilibrium(self, match,realm):
        self.next_equilibrium=time.time()+float(match.group(1))
    
    
    @property
    def to_balance(self):
        return max(0, self.next_balance-time.time())
    
    @property
    def to_equilibrium(self):
        return max(0, self.next_equilibrium-time.time())
    
    @property
    def to_eqbal(self):
        return max(self.to_balance, self.to_equilibrium)   
    
    def auto_macro_do(self, realm):
        realm.send('pk')
        
    @binding_alias('^delayed_pk$')
    def auto_macro(self, matches, realm):
        realm.send_to_mud = False
        delay = self.to_eqbal
        realm.root.debug('delay: %f'%delay)
        if delay > 0.1:
            realm.cwrite('Scheduling AUTO MACRO in <red*>%0.2f<white> seconds'%float(delay))
            realm.root.set_timer(delay-0.1, self.auto_macro_do)
        else:
            self.auto_macro_do(realm)    
            
            
    @binding_alias('^pk$')
    def pk(self, matches, realm):
        realm.send_to_mud = False
        my_mana = realm.root.get_state('mp')
        combo = 'warchant rage focus|combo %(first)s %(second)s %(warchant)s %(target)s'
        target = realm.root.get_state('target')
        tracker = self.tracker.tracker(target)
        realm.cwrite('<white*:red>Stats: Rage - %(rage)d, Affs: %(affs)d\n\n'%{'rage':self.rage.rage,
                                                                           'affs':self.warchants.get_weaken_count(target)})
        #Maiming part
        if self.raze[target].aura and self.raze[target].shield and not self.dances.beguile:
            first = 'raze'
            second = 'raze'
        else:
            if (self.raze[target].aura or self.raze[target].shield) and not self.dances.beguile:
                first = 'raze'
            else:
                toxin = self.sword_combo.get_toxin(target)
                first = 'strike %s'%toxin
            if self.shield_maiming.smash_aff_count(target) < 3:
                second = 'smash'
            else:
                second = 'bash'
        #warchant part
        if self.warchants.get_weaken_count(target)>=3 or self.warchants.get_weaken_count(target)>= 2 and self.hp < 150:# or (self.warchants.get_weaken_count(target)>=4 and tracker['sensitivity'].on) or (self.rage.rage>=30 and self.warchants.get_weaken_count(target)>=4):
            if self.rage.rage>=30:
                warchant = 'thunder pierce'
            else:
                warchant = 'pierce'
        #elif self.rage.rage == 100:
        #    warchant = 'enrage'
         
        elif self.rage.rage>=50: #and self.warchants.get_weaken_count(target)<3:
            warchant = 'repeat weaken'
        else:
            warchant = 'weaken'
        
            
        
        combo=combo%{'first':first,
                     'second':second,
                     'warchant':warchant,
                     'target':target}
        
        if my_mana > 150:
            realm.send('queue eqbal %(combo)s|trueassess %(target)s '%{'combo':combo,
                                                                       'target':target})
        else:
            realm.send('queue eqbal %s'%combo)
        
    def get_toxin(self, realm):
        target = realm.root.get_state('target')
        tracker = self.tracker.tracker(target)
        for t in self.toxin_list:
            if t == 'hemotoxin' and tracker.time_to_next_purge()>3:
                continue
            if not tracker[t].on:
                return t