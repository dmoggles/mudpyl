'''
Created on Feb 19, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule


class DeathknightCombo(EarlyInitialisingModule):
    
    def __init__(self, light, infused, draining, finisher, aff_tracker, shield_tracker):
        self.light = light,
        self.infused = infused
        self.draining = draining
        self.finisher = finisher
        self.tracker = aff_tracker
        self.shield_tracker = shield_tracker
        self.tracker.apply_priorities([('haemophilia',1)])
        
        
    def get_toxins(self, tracker):
        toxins =[]
        if not tracker['xeroderma'].on:
            toxins.append('xeroderma')
        if not tracker['botulinum'].on:
            toxins.append('botulinum')
        if not (tracker['paralysis'].on or tracker['numbness'].on):
            toxins.append('ciguatoxin')
        if not tracker['hemotoxin'] and tracker.time_to_next_purge() < 4:
            toxins.append('hemotoxin')
        if not tracker['mercury'].on:
            toxins.append('mercury')
        if not tracker['metrazol'].on:
            toxins.append('metrazol')
        if not tracker['ether'].on:
            toxins.append('ether')
        if not tracker['arsenic'].on:
            toxins.append('arsenic')
        if not tracker['strychnine'].on:
            toxins.append('strychnine')
            
        while len(toxins)<2:
            toxins.append('')
        return toxins[0:2]
            
    def get_finish(self, realm, target):
        tracker = self.tracker.tracker(target)
        combo = 'light pipes|enemy %(target)s|stand|order hound kill %(target)s'%{'target':target}
        toxins = self.get_toxins(tracker)
        if not 'aconite' in toxins[0:2]:
            toxins.insert(0, 'aconite')
            
        attack1 = 'lacerate'
        attack2 = 'lacerate'
        
        if self.shield_tracker[target].aura or self.shield_tracker[target].shield:
            attack1='raze'
            attack2='raze'
        
        combo+='|quickdraw %s shield'%self.finisher
        combo+='|wm %(attack1)s %(attack2)s %(target)s %(toxin1)s %(toxin2)s'%{'attack1':attack1,
                                                                               'attack2':attack2,
                                                                               'target':target,
                                                                               'toxin1':toxins[0],
                                                                               'toxin2':toxins[1]}
        combo+='|soulstorm %(target)s'%{'target':target}
        combo+='|trueassess %(target)s'%{'target':target}
        return combo
    
    def get_combo(self, realm, target):
        tracker = self.tracker.tracker(target)
        
        combo = 'light pipes|enemy %(target)s|stand|order hound kill %(target)s'%{'target':target}
        toxins = self.get_toxins(tracker)
        if tracker['haemophilia'].on:
            sword = self.infused
            attack1 = 'lacerate'
            attack2 = 'lacerate'
        else:
            mp=realm.root.get_state('mp')
            mpmax=realm.root.get_state('maxmp')
            
            mppct=float(mp)/float(mpmax)
            if mppct>0.6:
                sword = self.infused
            else:
                sword = self.draining
            attack1 = 'lacerate'
            attack2 = 'shred'
        
        if self.shield_tracker[target].aura and self.shield_tracker[target].shield:
            attack1='raze'
            attack2='raze'
        elif self.shield_tracker[target].aura or self.shield_tracker[target].shield:
            old_attack1 = attack1
            attack1='raze'
            attack2=old_attack1
            
        combo+='|quickdraw %s shield'%sword
        combo+='|wm %(attack1)s %(attack2)s %(target)s %(toxin1)s %(toxin2)s'%{'attack1':attack1,
                                                                               'attack2':attack2,
                                                                               'target':target,
                                                                               'toxin1':toxins[0],
                                                                               'toxin2':toxins[1]}
        combo+='|engage %(target)s'%{'target':target}
        combo+='|trueassess %(target)s'%{'target':target}
        return combo
        
    def get_reave(self, realm, target):    
        tracker = self.tracker.tracker(target)
        
        combo = 'light pipes|enemy %(target)s|stand|order hound kill %(target)s'%{'target':target}
        toxins = self.get_reave_toxins(tracker)
        attack1='reave'
        attack2='reave'
        if self.shield_tracker[target].aura and self.shield_tracker[target].shield:
            attack1='raze'
            attack2='raze'
        elif self.shield_tracker[target].aura or self.shield_tracker[target].shield:
            old_attack1 = attack1
            attack1='raze'
            attack2='reave'
        combo+='|quickdraw battleaxe shield'
        combo+='|wm %(attack1)s %(attack2)s %(target)s %(toxin1)s %(toxin2)s'%{'attack1':attack1,
                                                                               'attack2':attack2,
                                                                               'target':target,
                                                                               'toxin1':toxins[0],
                                                                               'toxin2':toxins[1]}
        combo+='|engage %(target)s'%{'target':target}
        combo+='|soulstorm %(target)s'%{'target':target}
        combo+='|trueassess %(target)s'%{'target':target}
        return combo
    
    def get_reave_toxins(self, tracker):
        if tracker['aconite'].on or tracker['botulinum'].on:
            return ('strychnine','strychnine')
        else:
            return ('strychnine','aconite')