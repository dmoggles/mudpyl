'''
Created on Jul 29, 2015

@author: dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger
from pymudclient.gmcp_events import binding_gmcp_event
from pymudclient.aliases import binding_alias
from pymudclient.modules import load_file
from pymudclient.tagged_ml_parser import taggedml
from pymudclient.net.gmcp import ImperianGmcpHandler

class ImperianModule(BaseModule, ImperianGmcpHandler):
    '''
    classdocs
    '''


    def __init__(self, realm):
        '''
        Constructor
        '''
        BaseModule.__init__(self, realm)
        self.map_mode=False
        
    @binding_trigger(r'---+ .+ --+$')
    def on_map_header_footer(self, matches, realm):
        if self.map_mode==False:
            realm.root.active_channels=['map']
            self.map_mode=True
        else:
            realm.display_line=False
            realm.root.write(realm.metaline)
            realm.root.active_channels=['main']
            self.map_mode=False
    
    
    @binding_alias(r'^show_gmcp$')
    def show_gmcp(self,match,realm):
        realm.write(self.gmcpToString(realm.root.gmcp), soft_line_start=True)
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
            
    @binding_alias('^tar (\w+)$')    
    def set_target(self, match, realm):
        my_target=match.group(1).capitalize()
        
        #ml = Metaline('Target set: %s'%my_target, RunLengthList([(0, fg_code(CYAN, True)),
        #                                                         (12,fg_code(RED,True))]),
        #              RunLengthList([(0,bg_code(BLACK))]))
        ml = taggedml('<cyan*:black>Target set: <red*>%s'%my_target)                                                    
        realm.write(ml)
        realm.root.state['target']=my_target
        realm.send_to_mud=False  
    
    @property
    def aliases(self):
        return [self.set_target, self.add_module, self.show_gmcp]
    
    @property
    def triggers(self):
        return [self.on_map_header_footer]