'''
Created on Mar 7, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger

limbs = ['left arm','right arm','left leg','right leg','torso','head']

class Limb:
    def __init__(self, limb):
        self.limb = limb
        self.partial = 0
        self.damaged=False
        self.mangled=False
        
    @property
    def bruised(self):
        return self.partial==2
    
    def set_bruised(self):
        self.partial = 2
        
    @property
    def trembling(self):
        return self.partial==1
    
    def set_trembling(self):
        self.partial = 1
        
    def reset_partial(self):
        self.partial = 0
    
class Person:
    def __init__(self, name):
        self.name=name
        self.limbs={l:Limb(l) for l in limbs}
        self.parrying = ''
        
    def __getitem__(self, limb):
        return self.limbs[limb] if limb in self.limbs else None

    
    
class LimbTrack(EarlyInitialisingModule):
    def __init__(self, realm):
        self.realm=realm
        self.persons={'me':Person('me')}
        
    def __getitem__(self, person):
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
                self.set_parry]
    
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
        lt[limb].damaged=True
        lt[limb].reset_partial()
        
    @binding_trigger(['^To your horror, your (.*) has been mutilated beyond repair by ordinary means\.$',
                      '^has a mangled (.*)\.$'])
    def self_mangled(self, match, realm):
        limb = match.group(1)
        lt = self.__getitem__('me')
        lt[limb].mangled=True
        lt[limb].reset_partial()
        
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