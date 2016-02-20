'''
Created on Feb 9, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger

class Warchants(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, manager, aff_tracker):
        self.manager = manager
        self.tracker = aff_tracker
        self.last_chant = ''
        
    @property
    def triggers(self):
        return [self.chant_aff,
                self.weaken,
                self.no_effect]
        
        
    @binding_trigger('^The thrill of the battle flowing through your body, you hurl a powerful weakening scream towards')
    def weaken(self, matches, realm):
        self.last_chant = 'weaken'
        realm.cwrite('<red*:green>WEAKEN!')
    
    @binding_trigger('^The chant has no effect\.$')
    def no_effect(self, matches, realm):
        if self.last_chant == 'weaken':
            realm.cwrite('<red*:green>~~~~~~~WEAKEN DONE!!!!!~~~~~~~~~~')
            target = realm.root.get_state('target')
            tracker = self.tracker.tracker(target)
            tracker.add_aff('healthleech')
            tracker.add_aff('clumsiness')
            tracker.add_aff('weariness')
            tracker.add_aff('lethargy')
            tracker.add_aff('nausea')
    
    
    @binding_trigger('The chant causes (\w+) to suffer from (\w+)\.')
    def chant_aff(self, matches, realm):
        target = str(matches.group(1))
        aff = str(matches.group(2))
        self.tracker.tracker(target).add_aff(aff)
        
    def get_weaken_count(self, target):
        count = 0
        tracker = self.tracker.tracker(target)
        if tracker['healthleech'].on:
            count+=1
        if tracker['clumsiness'].on:
            count+=1
        if tracker['weariness'].on:
            count+=1
        if tracker['lethargy'].on:
            count+=1
        if tracker['nausea'].on:
            count+=1
            
        return count
        