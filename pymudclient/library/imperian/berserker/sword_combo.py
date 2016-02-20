'''
Created on Feb 11, 2016

@author: Dmitry
'''



class SwordCombo1:
    
    def __init__(self, aff_tracker):
        self.tracker = aff_tracker
        
    def get_toxin(self, target):
        tracker = self.tracker.tracker(target)
        
        if not (tracker['paralysis'].on or tracker['numbness'].on) and tracker.time_to_next_tree() < 4:
            return 'ciguatoxin'
        
        if not tracker['hemotoxin'].on and tracker.time_to_next_purge() < 4:
            return 'hemotoxin'
        if tracker['slickness'].on:
            if not tracker['calotropis'].on:
                return 'calotropis'
            if not tracker['slow herbs'].on:
                return 'mazanor'
            if not tracker['slow elixirs'].on:
                return 'luminal'
            if not (tracker['crippled left arm'].on and tracker['crippled right arm'].on):
                return 'benzene' 
            if not (tracker['crippled left leg'].on and tracker['crippled right leg'].on):
                return 'benzedrene'
        if tracker['asthma'].on and tracker['sensitivity'].on and (tracker['numbness'].on or tracker['paralysis'].on):
            return 'iodine'
        if not tracker['xeroderma'].on:
            return 'xeroderma'
        if not tracker['vomiting'].on:
            return 'botulinum'
        if not tracker['clumsiness'].on:
            return 'arsenic'
        if tracker['vomiting'].on and tracker['clumsiness'].on and tracker['weariness'].on:
            return 'strychnine'
        if not tracker['hemotoxin'].on:
            return 'hemotoxin'
        if not tracker['asthma'].on:
            return 'mercury'
        if not tracker['butisol'].on:
            return 'butisol'
        if not (tracker['paralysis'].on or tracker['numbness'].on):
            return 'ciguatoxin'
        if not tracker['metrazol'].on:
            return 'metrazol'   
        if not tracker['sensitivity'].on:
            return 'strychnine' 
        