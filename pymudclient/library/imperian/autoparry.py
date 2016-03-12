'''
Created on Mar 7, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.library.imperian.limb_tracker import limbs
from _functools import partial
from random import randint
from pymudclient.aliases import binding_alias
from pymudclient.triggers import binding_trigger
import json

class Autoparry(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, realm, limb_tracker):
        self.realm=realm
        self.limb_tracker=limb_tracker
        self.mode='guard'
        
    
    @property
    def aliases(self):
        return [self.set_mode]
    
    @property
    def triggers(self):
        return [self.status_change]
    
    
    @binding_alias('^parry setmode (guard|protect)$')
    def set_mode(self, match, realm):
        realm.send_to_mud=False
        mode = match.group(1)
        self.mode = mode
        realm.cwrite('Parry mode set to <red*>%s'%mode)
        
        
    @binding_trigger(['^Your (.*) trembles slightly under the blow\.$',
                      '^Painful bruises are forming on your (.*)\.$',
                      '^Your (.*) feels healthier\.$',
                      '^Your (.*) is greatly damaged from the beating\.$',
                      '^To your horror, your (.*) has been mutilated beyond repair by ordinary means\.$',
                      '^You have cured damaged (.*)\.$',
                      '^You have cured mangled (.*)\.$'])
    def status_change(self, match, realm):
        new_parry = self.evaluate_parry()
        if not new_parry=='':
            realm.send('queue eqbal parry %s'%new_parry)
            
            
    def evaluate_parry(self, mode=None):
        if mode==None:
            mode = self.mode
        if mode=='guard':
            weights=self.calc_guard()
        elif mode=='protect':
            weights=self.calc_protect()
            
        self.realm.debug(json.dumps(weights))
        highest = ''
        highest_value = -1
        for l in limbs:
            part = weights[l]
            if part > highest_value:
                the_list = [l]
                highest = l
                highest_value = part
            elif part == highest_value:
                the_list.append(l)
        #tiebreakers
        if highest_value > 0 and len(the_list) == 1:
            if highest != self.limb_tracker['me'].parrying:
                return highest
            else:
                return ''
        elif len(the_list)>1 and highest_value > 0:
            legs_only = [l for l in the_list if 'leg' in l]
            if len(legs_only)>0:
                return legs_only[randint(0, len(legs_only)-1)]
            else:
                if self.limb_tracker['me'].parrying not in the_list:
                    return the_list[randint(0, len(the_list)-1)]
                else:
                    return ''
        else:
            return ''
        
        
    def calc_guard(self):
        weights = {l:0 for l in limbs}
        for l in limbs:
            part = 0
            if self.limb_tracker['me'][l].bruised:
                part+=3
            elif self.limb_tracker['me'][l].trembling:
                part+=1
            if self.limb_tracker['me'][l].mangled:
                part+=1
            elif self.limb_tracker['me'][l].damaged:
                part+=2
            weights[l]=part
        return weights
            
    
    def calc_protect(self):
        weights = {l:0 for l in limbs}
        for l in limbs:
            part = self.limb_tracker['me'][l].partial + 1
            if self.limb_tracker['me'][l].damaged:
                part+=1
            weights[l]=part
        return weights
        
    
    
        