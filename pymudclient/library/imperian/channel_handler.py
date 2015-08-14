'''
Created on Aug 13, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger

class ChannelHandler(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, manager):
        BaseModule.__init__(self, manager)
        
    @property
    def triggers(self):
        return [self.channel_trigger]
    
    @binding_trigger(['^\(\w+\): ',
                      '(\w+) tells you, "'])
    def channel_trigger(self, match, realm):
        block=realm.root.block
        active_channels = realm.root.active_channels
        realm.root.active_channels=['comm']
        for l in block:
            realm.root.write(l)
        realm.root.active_channels=active_channels
        
        