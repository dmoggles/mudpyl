'''
Created on Feb 4, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.triggers import binding_trigger

class RageTracker(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self):
        self.rage=0
        
        
    @property
    def triggers(self):
        return [self.rage_set,
                self.rage_set_0]
    
    @binding_trigger('^Your rage increases! It is now at (\d+)%\.$')
    def rage_set(self, match, realm):
        self.rage = int(match.group(1))
        realm.display_line=False
        if self.rage <30:
            color_tag = '<white*:green>'
        elif self.rage < 60:
            color_tag = '<white*:yellow>'
        elif self.rage < 80:
            color_tag = '<white*:orange>'
        else:
            color_tag = '<white*:red>'
        realm.cwrite('<white*:purple>RAGE: %(color)s%(level)d'%{'color':color_tag,
                                                                'level':self.rage})
        realm.fireEvent('promptDataEvent','rage',self.make_prompt_text())
        
    @binding_trigger('^Your berserking rage leaves you\.$')
    def rage_set_0(self,match,realm):
        self.rage=0
        realm.display_line=False
        realm.cwrite('<white*:purple>RAGE: <white*:green>0')
        realm.fireEvent('promptDataEvent','rage',self.make_prompt_text())
        
    def make_prompt_text(self):
        if self.rage <30:
            color_tag = '<green>'
        elif self.rage < 60:
            color_tag = '<yellow>'
        elif self.rage < 80:
            color_tag = '<orange>'
        else:
            color_tag = '<red>'
            
        return '<purple*>r: %(color)s%(rage)d'%{'color':color_tag, 
                                             'rage':self.rage}
            