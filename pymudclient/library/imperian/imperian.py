'''
Created on Jul 29, 2015

@author: dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger
from pymudclient.aliases import binding_alias
from pymudclient.modules import load_file
from pymudclient.tagged_ml_parser import taggedml
from pymudclient.library.imperian.player_tracker import PlayerTracker
import requests
import json
import re
from pymudclient.gmcp_events import binding_gmcp_event
from pymudclient.net.gmcp import GmcpHandler

def get_char_data( name):
        
    r=requests.get('http://api.imperian.com/characters/%s.json'%name.lower())
    
    if not r.status_code == 200:
        return None
    else:
        d=json.loads(r.text)
        description = d['description']
        d1=description.split('.')[0]
        statpack = re.match('(?:She|He) is (?:a|an) (\w+) (?:\w+)',d1).group(1)
        d['statpack']=statpack
        return d
            
class ImperianModule(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, realm):
        '''
        Constructor
        '''
        BaseModule.__init__(self, realm)
        self.map_mode=False
        
    @property
    def aliases(self):
        return [self.show_gmcp, self.add_module,self.set_target,self.untar,
                self.whois,
                self.enemy]
    @property
    def triggers(self):
        return [self.on_map_header,
                #self.on_map_footer,
                self.pipes,
                self.bleeding]
    
    @property
    def modules(self):
        return [PlayerTracker]
    
    @property
    def gmcp_events(self):
        return[self.vitals#, 
               #self.on_map_redirect
               ]
    
    @binding_alias('^whois (\w+)')
    def whois(self, match,realm):
        realm.send_to_mud=False
        name=match.group(1)
        data=get_char_data(name)
        if not data:
            realm.write("Character %s not found."%name)
        else:
            realm.send('rt whois %s: %s %s, level:%s city:%s'%(name,data['statpack'],data['profession'],data['level'],data['city']))
            
    @binding_gmcp_event('Char.Vitals')
    def vitals(self, gmcp_data, realm):
        hp=int(gmcp_data['hp'])/11
        mp=int(gmcp_data['mp'])/11
        mhp=int(gmcp_data['maxhp'])/11
        mmp=int(gmcp_data['maxmp'])/11
        
        realm.root.set_state('hp',hp)
        realm.root.set_state('mp',mp)
        realm.root.set_state('maxhp',mhp)
        realm.root.set_state('maxmp',mmp)
        
        #if realm.root.gui:
        #    realm.root.gui.self_panel.hp_mana.set_curr_hp(hp)
        #    realm.root.gui.self_panel.hp_mana.set_curr_mana(mp)
        #    realm.root.gui.self_panel.hp_mana.set_max_hp(mhp)
        #    realm.root.gui.self_panel.hp_mana.set_max_mana(mmp)
    
    @binding_trigger('^Your wounds cause you to bleed (\d+) health\.$')
    def bleeding(self, match, realm):
        bleed=int(match.group(1))
        realm.root.set_state('bleed',bleed)
        #if realm.root.gui:
        #    realm.root.gui.self_panel.bleed.set_current(bleed)
            
                  
        
    @binding_trigger('^(\w+) of your pipes have gone cold and dark\.$')
    def pipes(self, match,realm):
        realm.send('queue eqbal light pipes')
        
    @binding_gmcp_event('Redirect.Window')
    def on_map_redirect(self, gmcp_data, realm):
        realm.root.setActiveChannels([gmcp_data])
    
    @binding_trigger('^\-\-\-(.*) v(\d+) (.*)\-\-\-$')
    def on_map_header(self, matches, realm):
        block = realm.block
        start_line = realm.line_index
        for i in xrange(start_line, start_line + 25): #MASSIVE HACK, THIS ONLY WORKS WITH 
                                                      #RADIUS 5
            block[i].channels=['map']
        #inner_text = matches.group(1).lower()
        #if 'announcement' in inner_text: #hacky to avoid announcement lines that look similar
        #    return
        #realm.root.setActiveChannels(['map'])
        #self.map_mode=True
        
    #@binding_trigger("-+(?: .+ )?-* [-\d]+\:[-\d]+\:[-\d]+ -+")
    #def on_map_footer(self, matches, realm):
    #    realm.display_line=False
    #    realm.root.write(realm.metaline)
    #    realm.root.setActiveChannels(['main'])
    #    self.map_mode=False
    
    
    @binding_alias('^show_gmcp(?: ((?:\w|\.)+))?$')
    def show_gmcp(self,match,realm):
        tag = match.group(1)
        if tag != None and tag in realm.root.gmcp:
            realm.write(GmcpHandler.gmcpToString(realm.root.gmcp[tag]), soft_line_start=True)
        else:
            realm.write(GmcpHandler.gmcpToString(realm.root.gmcp), soft_line_start=True)
        realm.send_to_mud=False
        
    @binding_alias(r"^add_module (\w+)$")
    def add_module(self,match,realm):
        modname=match.group(1)
        realm.write("Adding module %s" % modname)
        realm.send_to_mud=False
        cls=load_file(modname)
        realm.write(cls)
        if cls!=None:
            realm.write('Got a class')
            realm.root.load_module(cls)
            
    @binding_alias('^untar$')
    def untar(self,match,realm):
        realm.root.state['target']=''
        realm.send_to_mud=False
        
    @binding_alias('^tar (\w+)$')    
    def set_target(self, match, realm):
        my_target=match.group(1).capitalize()
        
        #ml = Metaline('Target set: %s'%my_target, RunLengthList([(0, fg_code(CYAN, True)),
        #                                                         (12,fg_code(RED,True))]),
        #              RunLengthList([(0,bg_code(BLACK))]))
        ml = taggedml('<cyan*:black>Target set: <red*>%s'%my_target)                                                    
        realm.write(ml)
        realm.root.set_state('target',my_target)
        #realm.root.gui.set_target(my_target)
        realm.root.fireEvent('setTargetEvent',my_target)
        realm.send_to_mud=False  
        
    @binding_alias('^en$')
    def enemy(self, match,realm):
        my_target=realm.root.get_state('target')
        realm.send_to_mud=False
        realm.send('enemy %s'%my_target)
    
    