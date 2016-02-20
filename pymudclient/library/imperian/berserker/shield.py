'''
Created on Feb 9, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule

from pymudclient.triggers import binding_trigger

class ShieldMaiming(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, manager, aff_tracker):
        self.manager = manager
        self.tracker = aff_tracker
        self.shatter_prep = False
        
        
    @property
    def triggers(self):
        return [self.shield_smash]
    
    
    @binding_trigger("^You smash a .* into (\w+)'s stomach, causing (?:him|her) to recoil in pain\.$")
    def shield_smash(self, matches, realm):
        target = matches.group(1)
        tracker = self.tracker.tracker(target)
        if not tracker['nausea'].on:
            tracker.add_aff('nausea', False)
        elif not tracker['clumsiness'].on:
            tracker.add_aff('clumsiness', False)
        elif not tracker['weariness'].on:
            tracker.add_aff('weariness', False)
        else:
            self.shatter_prep = True
        
    def smash_aff_count(self, target):
        tracker = self.tracker.tracker(target)
        count = 0
        if tracker['nausea'].on:
            count+=1
        if tracker['clumsiness'].on:
            count+=1
        if tracker['weariness'].on:
            count+=1
            