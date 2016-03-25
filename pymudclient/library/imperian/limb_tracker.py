'''
Created on Mar 7, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger
import math

limbs = ['left arm','right arm','left leg','right leg','torso','head']

class Limb:
    def __init__(self, limb):
        self.limb = limb
        self.partial = 0
        self.damaged=False
        self.mangled=False
        self.hits=0
        self.calculated_hits_to_break=0
        self.confirmed_hits_to_break=0
        
        
        
    def add_hit(self):
        self.hits+=1
        
    @property 
    def hits_left(self):
        if self.confirmed_hits_to_break!=0:
            return self.confirmed_hits_to_break-self.hits
        else:
            return self.calculated_hits_to_break-self.hits - 1
        
    
    
    @property
    def bruised(self):
        return self.partial==2
        
    
    def set_bruised(self):
        self.partial = 2
        self.calculated_hits_to_break = int(math.ceil(float(self.hits) / (2./3.0)))
    
    @property
    def full_damage(self):
        if self.damaged:
            return 1
        if self.mangled:
            return 2
        return 0
    
    @property
    def trembling(self):
        return self.partial==1
    
    def set_trembling(self):
        self.partial = 1
        self.calculated_hits_to_break = int(math.ceil(float(self.hits) / (1./3.)))
        
    def reset_partial(self):
        self.partial = 0
        self.hits=0
    
    def set_healed(self):
        self.damaged=0
        self.mangled = 0
        self.hits=0
        self.partial = 0

    def set_damaged(self):
        self.damaged=1
        self.mangled = 0
        self.confirmed_hits_to_break=self.hits
        self.hits=0
        self.partial = 0
        
    def set_mangled(self):
        self.mangled=1
        self.confirmed_hits_to_break=self.hits
        self.hits = 0
        self.partial = 0
    
class Person:
    def __init__(self, name):
        self.name=name
        self.limbs={l:Limb(l) for l in limbs}
        self.parrying = ''
        self.target=''
        
    def __getitem__(self, limb):
        return self.limbs[limb] if limb in self.limbs else None
    
    def set_target(self, limb):
        self.target = limb
        
    def add_hit(self, limb):
        self.limbs[limb].add_hit()
        
    def set_bruised(self, limb):
        self.limbs[limb].set_bruised()
        
    def set_trembling(self, limb):
        self.limbs[limb].set_trembling()
        
    def reset_partial(self, limb):
        self.limbs[limb].reset_partial()
        
    def set_damaged(self, limb):
        self.limbs[limb].set_damaged()
        
    def apply_salve(self, limb):
        if limb=='head':
            if self.limbs['head'].mangled:
                self.limbs['head'].set_damaged()
            else:
                self.limbs['head'].set_healed()
            return 'head'
        if limb=='torso':
            if self.limbs['torso'].mangled:
                self.limbs['torso'].set_damaged()
            else:
                self.limbs['torso'].set_healed()
            return 'torso'
        if limb=='arms':
            if self.limbs['left arm'].mangled:
                self.limbs['left arm'].set_damaged()
                healed_limb = 'left arm'
            elif self.limbs['right arm'].mangled:
                self.limbs['right arm'].set_damaged()
                healed_limb = 'right arm'
            elif self.limbs['left arm'].damaged:
                self.limbs['left arm'].set_healed()
                healed_limb = 'left arm'
            else:
                self.limbs['right arm'].set_healed()
                healed_limb = 'right arm'
            return healed_limb
        if limb=='legs':
            if self.limbs['left leg'].mangled:
                self.limbs['left leg'].set_damaged()
                healed_limb = 'left leg'
            elif self.limbs['right leg'].mangled:
                self.limbs['right leg'].set_damaged()
                healed_limb = 'right leg'
            elif self.limbs['left leg'].damaged:
                self.limbs['left leg'].set_healed()
                healed_limb = 'left leg'
            else:
                self.limbs['right leg'].set_healed()
                healed_limb = 'right leg'
            return healed_limb
    
class LimbTrack(EarlyInitialisingModule):
    def __init__(self, realm):
        self.realm=realm
        self.persons={'me':Person('me')}
        self.event_counter = 0
        realm.registerEventHandler('setTargetEvent',self.on_target)
        
    def __getitem__(self, person):
        person=person.lower()
        #self.realm.debug('person requested: %s'%person)
        #self.realm.debug('all people: %s'%str(self.persons.keys()))
        
        if not person in self.persons:
            self.persons[person]=Person(person)
        return self.persons[person]
    
    @property
    def triggers(self):
        return [self.self_trembles,
                self.self_bruises,
                self.self_reset_partial,
                self.self_damaged,
                self.self_mangled,
                self.self_heal_damaged,
                self.self_heal_mangled,
                self.dead,
                self.set_parry,
                self.capture_hack,
                self.capture_bruised,
                self.capture_trembling,
                self.capture_reset,
                self.capture_damaged,
                self.capture_damaged_torso,
                self.capture_damaged_head,
                self.apply_salve,
                self.tendoncut]
    
    
    #self
    
    def on_target(self, target):
        self.event_counter=0
        
    
    def send_limb_status_event(self, realm, person, limb):
        lt = self.__getitem__(person)
        a_limb = lt[limb]
        realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, self.event_counter)
        self.event_counter+=1
    
    
    @binding_trigger('^Your (.*) trembles slightly under the blow\.$')
    def self_trembles(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].set_trembling()
        
    @binding_trigger('^Painful bruises are forming on your (.*)\.$')
    def self_bruises(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].set_bruised()
        
    @binding_trigger('^Your (.*) feels healthier\.$')
    def self_reset_partial(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].reset_partial()
        
    @binding_trigger(['^Your (.*) is greatly damaged from the beating\.$',
                      '^has a partially damaged (.*)\.$'])
    def self_damaged(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].set_damaged()
        
        
    @binding_trigger(['^To your horror, your (.*) has been mutilated beyond repair by ordinary means\.$',
                      '^has a mangled (.*)\.$'])
    def self_mangled(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].set_mangled()
        
        
    @binding_trigger('^You have cured mangled (.*)\.$')
    def self_heal_mangled(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].mangled=False
        lt[limb].reset_partial()
        
    @binding_trigger('^You have cured damaged (.*)\.$')
    def self_heal_damaged(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].damaged=False
        lt[limb].reset_partial()
        
    @binding_trigger('^You have been slain by .*$')
    def dead(self, match, realm):
        lt = self.__getitem__('me')
        for l in limbs:
            lt[l].damaged=False
            lt[l].mangled=False
            lt[l].reset_partial()
            
    @binding_trigger('^You will now attempt to parry attacks to your (.*)\.$')
    def set_parry(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt.parrying = limb
        
    #other
    
    @binding_trigger("^You hack at (\w+)'s (.*) with a gleaming scimitar\.$")
    def capture_hack(self, match, realm):
        self.did_hack=True
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_target(limb)
        lt.add_hit(limb)
        a_limb = lt[limb]
        realm.root.debug('hack %d'%a_limb.hits_left)
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'hack')
        self.send_limb_status_event(realm, person, limb)
    
    @binding_trigger("^You notice several bruises forming on (\w+)'s (.*)\.$")
    def capture_bruised(self, match, realm):
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_bruised(limb)
        a_limb = lt[limb]
        realm.root.debug('damage %d'%(a_limb.full_damage*3+a_limb.partial))
        
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'bruised')
        self.send_limb_status_event(realm, person, limb)
        
    @binding_trigger("^(\w+)'s (.*) trembles slightly under the blow\.")
    def capture_trembling(self, match, realm):
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_trembling(limb)
        a_limb = lt[limb]
        realm.root.debug('damage %d'%(a_limb.full_damage*3+a_limb.partial))
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'trembling')
        self.send_limb_status_event(realm, person, limb)
    
        
    @binding_trigger("^(\w+)'s (.*) looks healthier\.$")
    def capture_reset(self, match, realm):
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.reset_partial(limb)
        #a_limb = lt[limb]
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'reset')
        self.send_limb_status_event(realm, person, limb)
    
    @binding_trigger("^(\w+)'s (.*) has been mutilated\.$")
    def capture_damaged(self, match, realm):
        realm.root.debug('damaged')
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_damaged(limb)
        #a_limb = lt[limb]
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'damaged')
        self.send_limb_status_event(realm, person, limb)
        
    @binding_trigger("^(\w+) suffers internal damage from your blow\.$")
    def capture_damaged_torso(self, match, realm):
        realm.root.debug('torso damaged')
        
        limb = 'torso'
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_damaged(limb)
        #a_limb = lt[limb]
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'damaged')
        self.send_limb_status_event(realm, person, limb)
    
    @binding_trigger("^(\w+)'s head is crushed under your blow\.$")
    def capture_damaged_head(self, match, realm):
        realm.root.debug('head damaged')
        
        limb = 'head'
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.set_damaged(limb)
        #a_limb = lt[limb]
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'damaged')
        self.send_limb_status_event(realm, person, limb)
        
    @binding_trigger("^(\w+) rubs some salve on (?:her|his) (legs|arms|head|torso)\.$")
    def apply_salve(self, match, realm):
        person = match.group(1)
        limb = match.group(2)
        lt = self.__getitem__(person)
        limb_healed = lt.apply_salve(limb)
        realm.root.debug('applied salve to %s'%limb_healed)
        self.send_limb_status_event(realm, person, limb_healed)
    
    @binding_trigger("^You swing a gleaming scimitar at (\w+), calmly severing the tendons in (?:his|her) (.*)\.$")
    def tendoncut(self, match, realm):
        limb = match.group(2)
        person = match.group(1)
        lt = self.__getitem__(person)
        lt.reset_partial(limb)
        #a_limb = lt[limb]
        #realm.root.fireEvent('limbStatusEvent', person, limb, a_limb.full_damage, a_limb.partial, a_limb.hits, a_limb.hits_left, 'reset')
        self.send_limb_status_event(realm, person, limb)