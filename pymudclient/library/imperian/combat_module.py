'''
Created on Apr 3, 2016

@author: dmitrymogilevsky
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger
import time
from pymudclient.aliases import binding_alias


class ImperianCombatModule(EarlyInitialisingModule):
    def __init__(self, realm, aff_tracker, shield_tracker, limb_tracker, autoparry, communication, ta_interval = 0):
        self.tracker=aff_tracker
        self.shield=shield_tracker
        self.limbs=limb_tracker
        self.parry = autoparry
        self.comm = communication
        self.realm = realm
        self.next_balance=0
        self.next_equilibrium=0
        self.realm.registerEventHandler('setTargetEvent', self.on_target_set)
        self.last_ta = 0
        self.ta_interval = ta_interval
        
        
    @property
    def triggers(self):
        return [self.on_balance,
                self.on_equilibrium,
                self.trueassess_trigger,
                self.clot,
                self.on_prompt]
        
    
    @property
    def aliases(self):
        return [self.auto_macro]
    
    
    def on_target_set(self, target):
        self.tracker.tracker(target).reset()
        self.comm.announce_target(target)
        
        
        
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
        
        
    def auto_macro_do(self, realm, command):
        realm.send(command)
        
    def send_combo(self, realm, attack_string):
        combo = ''
        target = realm.root.get_state('target')
        parry = self.parry.evaluate_parry()
        limb_target = self.get_limb_target(target)
        if parry!= '':
            combo = 'parry %s|'%parry
        combo+='stand|enemy %(target)s|light pipes|curseward'%{'target':target}
        combo+='|target %s'%limb_target
        combo+='|%s'%attack_string
        combo+='|trueassess %s'%target
        realm.send('queue eqbal %s'%combo)
        
        
    def get_limb_target(self, target):
        return 'nothing'
    
    @binding_alias('^delayed (\w+)$')
    def auto_macro(self, matches, realm):
        command = matches.group(1)
        realm.send_to_mud = False
        delay = self.to_eqbal
        realm.root.debug('delay: %f'%delay)
        if delay > 0.1:
            realm.cwrite('Scheduling AUTO MACRO in <red*>%0.2f<white> seconds'%float(delay))
            realm.root.set_timer(delay-0.1, self.auto_macro_do, command)
        else:
            self.auto_macro_do(realm, command) 

    @binding_trigger("^(\w+)'s condition stands at (\d+)/(\d+) health and (\d+)/(\d+) mana\.$")
    def trueassess_trigger(self, match, realm):
        #if self.gags and self.combo_fired:
        #    realm.display_line=False
        person = match.group(1).lower()
        hp=int(match.group(2))
        max_hp=int(match.group(3))
        mana=int(match.group(4))
        max_mana=int(match.group(5))
        target = realm.root.get_state('target').lower()
        #realm.send('rt %s: %d/%d HP, %d/%d (%0.0f%%) Mana'%
        #          (person.upper(), hp, max_hp, mana, max_mana, 100*float(mana)/float(max_mana)))
        self.comm.send_health_mana(person, hp, max_hp, mana, max_mana)
        if target==person:
            realm.root.fireEvent('targetStatUpdateEvent','hp',hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana',mana)
            realm.root.fireEvent('targetStatUpdateEvent','hp_max',max_hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana_max',max_mana)
            
    @binding_trigger('^Autocuring: clot$')
    def clot(self, match,realm):
        realm.safe_send('clot|clot|clot|clot|clot')
        
    @binding_trigger('^H:(\d+) M:(\d+)')
    def on_prompt(self, match, realm):
        self.execute_on_prompt(match, realm)
        
    def execute_on_prompt(self, match, realm):
        pass