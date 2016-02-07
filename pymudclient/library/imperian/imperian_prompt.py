'''
Created on Nov 8, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger

class ImperianPrompt(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, realm):
        BaseModule.__init__(self, realm)
        self.extra_data={}
        realm.registerEventHandler('promptDataEvent', self.prompt_extra_data)
        
    def prompt_extra_data(self, key, data):
        if data == '' and key in self.extra_data:
            del self.extra_data[key]
        else:
            self.extra_data[key]=data
            
        
    @property
    def triggers(self):
        return [self.prompt_trigger]
    
    
    #gotta find a better way to trigger on prompt
    @binding_trigger('^H:\d+ M:\d+')
    def prompt_trigger(self, match, realm):
        realm.display_line=False
        
        new_prompt=''
        
        hp=int(self.manager.gmcp['Char.Vitals']['hp'])/11
        mp=int(self.manager.gmcp['Char.Vitals']['mp'])/11
        maxhp=int(self.manager.gmcp['Char.Vitals']['maxhp'])/11
        maxmp=int(self.manager.gmcp['Char.Vitals']['maxmp'])/11
        hc="green"
        mc="green"
        if float(hp)/float(maxhp) < 0.75:
            hc="yellow*"
        if float(hp)/float(maxhp) < 0.5:
            hc="red*"
            
        if float(mp)/float(maxmp) < 0.75:
            mc="yellow*"
        if float(mp)/float(maxmp) < 0.5:
            mc="red*"
        new_prompt = new_prompt+"H:<%s>%d<white>/<green>%d"%(hc, hp, maxhp)
        new_prompt = new_prompt+" "
        new_prompt = new_prompt+"<white>M:<%s>%d<white>/<green>%d"%(mc, mp, maxmp)
        
        bal_char = '<green*>b' if ('bal' in self.manager.gmcp['Char.Vitals'] and self.manager.gmcp['Char.Vitals']['bal']=='1') else '<white>-'
        eq_char = '<green*>e' if ('eq' in self.manager.gmcp['Char.Vitals'] and self.manager.gmcp['Char.Vitals']['eq']=='1') else '<white>-'
        
        new_prompt+= " <white>["
        new_prompt+= eq_char
        new_prompt+= bal_char
        
        blind = 'blind' in self.manager.gmcp['Char.Vitals'] and self.manager.gmcp['Char.Vitals']['blind']=='1'
        deaf = 'deaf' in self.manager.gmcp['Char.Vitals'] and self.manager.gmcp['Char.Vitals']['deaf']=='1'
        if blind or deaf:
            new_prompt+=' '
        if blind:
            new_prompt+='<yellow*>b'
        if deaf:
            new_prompt+='<yellow*>d'
            
            
        #target 
        target = self.manager.get_state('target')
        if not target == None and not target == '':
            new_prompt += " <cyan*>T:<red*>%s"%target.capitalize()
        
        #autocuring 
        
        new_prompt+= " <yellow*>AC: "+ ("<red*>OFF" if self.manager.get_state('autocuring')=='off' else "<green*>ON")
        
        #extra data
        if len(self.extra_data):
            new_prompt+= ' '+' <white>| '.join(self.extra_data.values())
        
        new_prompt+= "<white>]"
        
        realm.cwrite(new_prompt)
        
        
        