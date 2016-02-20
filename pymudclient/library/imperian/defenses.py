'''
Created on Feb 12, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.gmcp_events import binding_gmcp_event
from pymudclient.aliases import binding_alias

class Defenses(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, manager, defense_list):
        self.dl = defense_list
        self.manager = manager
        self.applied_defenses=set()
        
        
    @property
    def gmcp_events(self):
        return [self.on_defense_add,
                self.on_defense_remove,
                self.on_defense_list]
    
    @property
    def aliases(self):
        return [self.apply_next,
                self.show_missing]
    
    @binding_gmcp_event('Char.Defences.Add')
    def on_defense_add(self, data, realm):
        name = str(data['name']).lower()
        self.applied_defenses.add(name)
        realm.cwrite('<purple>Added defense: <green*> %s'%name)
       
        
    
    @binding_gmcp_event('Char.Defences.Remove')
    def on_defense_remove(self, data, realm):
        for d in data:
            d= str(d)
            if d in self.dl:
                realm.cwrite('<purple>Removed defense: <green*> %s'%d)
                if d in self.applied_defenses:
                    self.applied_defenses.remove(d)
                    
    
    @binding_gmcp_event('Char.Defences.List')
    def on_defense_list(self, data, realm):
        self.applied_defenses=set()
        for d in data:
            name = str(d['name'])
            self.applied_defenses.add(name)
    
    @binding_alias('^d1$')
    def apply_next(self, matches, realm):
        realm.send_to_mud=False
        l = [self.dl[d] for d in self.dl if not d in self.applied_defenses]
        l = sorted(l, key=lambda df: df[1])
        if len(l)>0:
            realm.send('queue eqbal %s'%l[0][0])
    
    @binding_alias('^dshow$')
    def show_missing(self, matches, realm):
        realm.send_to_mud=False
        l = [(d,self.dl[d][1]) for d in self.dl if not d in self.applied_defenses]
        l = sorted(l, key=lambda df: df[1])
        realm.cwrite('<purple>Missing Defenses: <red>%s'%','.join([d[0] for d in l]))