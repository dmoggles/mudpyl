'''
Created on Jul 29, 2015

@author: dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.aliases import binding_alias
from pymudclient.gmcp_events import binding_gmcp_event

class PlayerTracker(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, realm):
        '''
        Constructor
        '''
        BaseModule.__init__(self,realm)
        self.players=[]
        self.target=''
        self.manual_target=False
        self.friends=[]
        self.enemies=[]
        
    @property
    def aliases(self):
        return [self.set_target_by_number, self.set_target_by_name]
    
    @property
    def gmcp_events(self):
        return [self.on_room_players, self.on_room_add_player, self.on_room_remove_player]
    
    @binding_alias('^tar (\w+)$')
    def set_target_by_name(self, match, realm):
        realm.send_to_mud=False
        self.target = match.group(1)
        realm.root.state['target']=self.target
        self.manual_target=True
        self.output_to_window(realm.root)
        
    @binding_alias('^t([0-9]+)')
    def set_target_by_number(self, match, realm):
        realm.send_to_mud=False
        target_num=int(match.group(1))-1
        if target_num > len(self.players):
            realm.cwrite('<white*:red>No player number %d in the room!'%target_num)
            return
        if target_num == -1:
            self.target = ''
            realm.root.state['target']=''
        else:
            target = self.players[target_num]
            realm.cwrite('<cyan*>Target set: <red*>%s'%target)
            realm.root.state['target']=target
            self.target=target
            self.manual_target=False
        self.output_to_window(realm.root)
    
    @binding_gmcp_event('Room.Players')
    def on_room_players(self, gmcp_data, realm):
        self.players=[str(p['name']) for p in gmcp_data]
        self.output_to_window(realm)
        
    def output_to_window(self,realm):
        my_active_channels=realm.active_channels
        realm.active_channels=['players']
        realm.cwrite(self.getPlayerWidgetStringHorizontal())
        realm.active_channels=my_active_channels
        if self.target not in self.players and not self.target=='' and not self.manual_target:
            realm.cwrite(('<white*:red>Target <blue*:red>%s <white*:red>no longer in the room!\n'%self.target)*2)
            
        
    @binding_gmcp_event('Room.AddPlayer')
    def on_room_add_player(self, gmcp_data, realm):
        self.players.append(str(gmcp_data['name']))
        self.output_to_window(realm)
        
    @binding_gmcp_event('Room.RemovePlayer')
    def on_room_remove_player(self, gmcp_data, realm):
        print(gmcp_data)
        print(self.players)
        name=str(gmcp_data)[1:-1]
        if name in self.players:
            print("found player to remove")
            self.players.remove(name)
            self.output_to_window(realm)
    
    def getPlayerWidgetStringHorizontal(self):
        output=''
        for i,p in enumerate(self.players):
            if p in self.enemies:
                color='<red*>'
            elif p in self.friends:
                color='<green*>'
            else:
                color='<white*>'
            if p == self.target:
                output+='<white*>%d. %s>%s< | '%(i+1, color, p)
            else:
                output+='<white*>%d. %s%s | '%(i+1, color, p)
            output=output[:-2]
        return output
        
    def getPlayerWidgetString(self):
        output='<cyan*>'+'-'*7+'<white*>Current Players<cyan*>'+'-'*7+'\n'
        
        for i,p in enumerate(self.players):
            if p==self.target:
                color='<red*>'
            else:
                color='<white*>'
            output+='<white*>%d. %s%s\n'%(i+1,color,p)
        
        
        output+='<cyan*>'+'-'*29
        return output
        
            
    