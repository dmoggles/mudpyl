'''
Created on Feb 19, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger
import time
from pymudclient.library.imperian.people_services import damage_map

class DeathknightCombo(EarlyInitialisingModule):
    
    def __init__(self, weapons, aff_tracker, shield_tracker, limb_trackers):
        self.regular = weapons['regular']
        self.infused = weapons['infused']
        self.draining = weapons['draining']
        self.finisher = weapons['finisher']
        self.tracker = aff_tracker
        self.shield_tracker = shield_tracker
        self.limb_trackers = limb_trackers
        self.tracker.apply_priorities([('haemophilia',1)])
        
        self.teeth_off_cd=time.time()
    
    @property
    def triggers(self):
        return [self.teeth]
    
    @binding_trigger("^The teeth along the weapon edge cut into (\w+)'s flesh\.$")
    def teeth(self, match,realm): 
        self.teeth_off_cd = time.time() + 4
        realm.root.debug('next teeth at '+str(self.teeth_off_cd))
        
    @property
    def teeth_ready(self):
        return self.teeth_off_cd < time.time()
    
    
    
    def get_solo_combo(self, realm, target):
        profession = realm.root.get_state('target_prof')
        if profession == '' or profession in damage_map['physical']:
            dmg_type = 'p'
        else:
            dmg_type = 'm'
        combo = 'light pipes|enemy %(target)s|stand|target nothing|displace nothing|order hound kill %(target)s'%{'target':target}
        tracker = self.tracker.tracker(target)
        toxins = self.get_math_mental_toxin(tracker) if dmg_type == 'm' else self.get_math_physical_toxin(tracker)
        
        
        mp=realm.root.get_state('mp')
        mpmax=realm.root.get_state('maxmp')
            
        mppct=float(mp)/float(mpmax)
        if mppct > 0.6:
            weapon = self.regular
        else:
            weapon = self.draining
        realm.root.debug('teeth are ready' if self.teeth_ready else 'teeth are not ready')
        if tracker['haemophilia'].on:
            attack1 = 'lacerate'
            attack2 = 'lacerate'
        else:
            if self.teeth_ready:
                attack1='slash'
                attack2='shred'
            else:
                attack1='slash'
                attack2='slash'
                weapon = 'sabre'
        
        if self.shield_tracker[target].aura and self.shield_tracker[target].shield:
            attack1='raze'
            attack2='raze'
        elif self.shield_tracker[target].aura or self.shield_tracker[target].shield:
            
            attack1='raze'
            attack2='slash'
            weapon = 'sabre'
            
        combo+='|quickdraw %s shield'%weapon
        combo+='|wm %(attack1)s %(attack2)s %(target)s %(toxin1)s %(toxin2)s'%{'attack1':attack1,
                                                                               'attack2':attack2,
                                                                               'target':target,
                                                                               'toxin1':toxins[0],
                                                                               'toxin2':toxins[1]}
        combo+='|engage %(target)s'%{'target':target}
        combo+='|trueassess %(target)s'%{'target':target}
        return combo
    
    
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
        combo+='|lns|wm %(attack1)s %(attack2)s %(target)s %(toxin1)s %(toxin2)s'%{'attack1':attack1,
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
        
    def prep_limb(self, realm, target, limb_priority):
        limb_tracker = self.limb_trackers[target]
        tracker = self.tracker.tracker(target) 
        toxins = self.get_prep_toxin(tracker)
        limbs_to_use=[]
        limb = next(l for l in limb_priority if (limb_tracker[l].hits_left>1 or limb_tracker[l].hits_left<=0))
        limbs_to_use.append(limb)
        realm.root.debug('primary limb left %d'%limb_tracker[limb].hits_left)
        if limb_tracker[limb].hits_left == 2:
            limb2 = next(l for l in limb_priority if (limb_tracker[l].hits_left>1 or limb_tracker[l].hits_left<=0) and l!=limb)
            limbs_to_use.append(limb2)
            realm.root.debug('secondary limb %s'%limb2)
            
        combo = 'light pipes|enemy %(target)s|stand|order hound kill %(target)s'%{'target':target}
        combo+= '|quickdraw scimitar shield'
        combo+= '|target %(limb)s'%{'limb':limbs_to_use[0]}
        if len(limbs_to_use)>1:
            combo+= '|displace %(limb)s'%{'limb':limbs_to_use[1]}
        else:
            combo+= '|displace nothing'
        combo+= '|wm hack hack %(target)s %(toxin1)s %(toxin2)s'%{'target':target,
                                                                  'toxin1':toxins[0],
                                                                  'toxin2':toxins[1]}
        return combo
    
    def get_prep_toxin(self, tracker):
        toxins = []
        if not tracker['hemotoxin'].on and tracker.time_to_next_purge() < 4:
            toxins.append('hemotoxin')
        if not tracker['mercury'].on:
            toxins.append('mercury')
        if not tracker['hemotoxin'].on:
            toxins.append('hemotoxin')
        if not tracker['ether'].on:
            toxins.append('ether')
        if not tracker['arsenic'].on:
            toxins.append('arsenic')
        if not tracker['butisol'].on:
            toxins.append('butisol')
        if not (tracker['paralysis'].on or tracker['numbness'].on):
            toxins.append('ciguatoxin')
        toxins.append('strychnine')
        toxins.append('strychnine')
        return toxins[:2]
    
    
    def get_math_physical_toxin(self, tracker):
        hemo = tracker['hemotoxin'].on or tracker.time_to_next_purge() >4
        toxins=[]
        if not tracker['anorexia'].on and tracker['slickness'].on and hemo and tracker['impatience'].on:
            toxins.append('bromine')
        if not tracker['recklessness'].on and tracker['impatience'].on:
            toxins.append('atropine')
        if not tracker['slow_balance'].on and tracker['asthma'].on and hemo:
            toxins.append('noctec')
        if not tracker['slickness'].on and tracker['asthma'].on and hemo:
            toxins.append('iodine')
        if not tracker['slow_elixirs'].on and tracker['slickness'].on and hemo:
            toxins.append('luminal')
        if not tracker['slow_herbs'].on and tracker['slickness'].on and hemo:
            toxins.append('mazanor')
        if not tracker['calotropis'].on and tracker['slickness'].on and hemo:
            toxins.append('calotropis')
        if not (tracker['paralysis'].on or tracker['numbness'].on):
            toxins.append('ciguatoxin')
        if not tracker['asthma'].on:
            toxins.append('mercury')
        if not tracker['clumsiness'].on:
            toxins.append('ether')
        if not tracker['hemotoxin'].on and tracker.time_to_next_purge() < 4:
            toxins.append('hemotoxin')
        if not tracker['nausea'].on:
            toxins.append('botulinum')
        if not tracker['sunallergy'].on:
            toxins.append('xeroderma')
        if not tracker['weariness'].on:
            toxins.append('arsenic')
        if not tracker['sensitivity'].on:
            toxins.append('strychnine')
        if not tracker['metrazol'].on:
            toxins.append('metrazol')
        if not tracker['butisol'].on:
            toxins.append('butisol')
        if not tracker['dizziness'].on:
            toxins.append('lindane')
        if not tracker['slow_equilibrium'].on and tracker['asthma'].on and hemo:
            toxins.append('mebaral')
        if not tracker['stupidity'].on and tracker['impatience'].on:
            toxins.append('aconite')
        if not tracker['ignorance'].on:
            toxins.append('avidya')
        toxins.append('atropine')
        toxins.append('strychnine')
        return toxins[:2]
        
        
    def get_math_mental_toxin(self, tracker):    
        hemo = tracker['hemotoxin'].on or tracker.time_to_next_purge() >4
        toxins=[]
        
        if not tracker['anorexia'].on and tracker['slickness'].on and hemo and tracker['impatience'].on:
            toxins.append('bromine')
        if not tracker['recklessness'].on and tracker['impatience'].on:
            toxins.append('atropine')
        if not tracker['slow_equilibrium'].on and tracker['asthma'].on and hemo:
            toxins.append('mebaral')
        if not tracker['slickness'].on and tracker['asthma'].on and hemo:
            toxins.append('iodine')
        if not tracker['slow_elixirs'].on and tracker['slickness'].on and hemo:
            toxins.append('luminal')
        if not tracker['slow_herbs'].on and tracker['slickness'].on and hemo:
            toxins.append('mazanor')
        if not tracker['calotropis'].on and tracker['slickness'].on and hemo:
            toxins.append('calotropis')
        if not (tracker['paralysis'].on or tracker['numbness'].on):
            toxins.append('ciguatoxin')
        if not tracker['asthma'].on:
            toxins.append('mercury')
        if not tracker['ignorance'].on:
            toxins.append('avidya')
        if not tracker['hemotoxin'].on and tracker.time_to_next_purge() < 4:
            toxins.append('hemotoxin')
        if not tracker['nausea'].on:
            toxins.append('botulinum')
        if not tracker['sunallergy'].on:
            toxins.append('xeroderma')
        if not tracker['stupidity'].on:
            toxins.append('aconite')
        if not tracker['butisol'].on:
            toxins.append('butisol')
        if not tracker['dizziness'].on:
            toxins.append('lindane')
        if not tracker['slow_balance'].on and tracker['asthma'].on and hemo:
            toxins.append('noctec')
        if not tracker['clumsiness'].on:
            toxins.append('ether')
        
        if not tracker['metrazol'].on:
            toxins.append('metrazol')
        if not tracker['weariness'].on:
            toxins.append('arsenic')
        toxins.append('atropine')
        toxins.append('strychnine')
        return toxins[:2]