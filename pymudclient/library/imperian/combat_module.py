'''
Created on Apr 3, 2016

@author: dmitrymogilevsky
'''
from pymudclient.modules import EarlyInitialisingModule


class CombatModule(EarlyInitialisingModule):
    def __init__(self, realm, aff_tracker, shield_tracker, limb_tracker, autoparry, communication):
        self.tracker=aff_tracker
        self.shield=shield_tracker
        self.limbs=limb_tracker
        self.parry = autoparry
        self.comm = communication
        self.realm = realm
        self.next_balance=0
        self.next_equilibrium=0
        self.realm.registerEventHandler('setTargetEvent', self.on_target_set)
        
        
    def on_target_set(self, target):
        self.tracker.tracker(target).reset()
        self.comm.announce_target(target)
        
        
        