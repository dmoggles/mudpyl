'''
Created on Mar 7, 2016

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger

class Alerts(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, realm):
        BaseModule.__init__(self, realm)
        
        
    @property
    def triggers(self):
        return [self.incindiary1]
    
    @binding_trigger(['^Sparks catch your eye as an arrow cuts through the air, burying itself deep in your flesh.',
                      '^ The fuse on the arrow buried in your gut begins to burn low, your sense of alarm building\.$'])
    def incindiary1(self, match, realm):
        realm.cwrite('<white:orange>INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!!')
        realm.cwrite('<white:orange>INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!!')
        realm.cwrite('<white:orange>INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!!')
        realm.cwrite('<white:orange>INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!! INCENDIARY STARTED!!!!')
        