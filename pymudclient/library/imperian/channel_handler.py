'''
Created on Aug 13, 2015

@author: Dmitry
'''
from pymudclient.modules import BaseModule
from pymudclient.triggers import binding_trigger
from twilio import rest
from pymudclient.gmcp_events import binding_gmcp_event
import re
from pymudclient.aliases import binding_alias

class ChannelHandler(BaseModule):
    '''
    classdocs
    '''


    def __init__(self, manager):
        BaseModule.__init__(self, manager)
        self.sms_forward = True
        
    @property
    def triggers(self):
        return [self.channel_trigger]
    
    @property
    def gmcp_events(self):
        return [self.sms_tell]
    
    @property
    def aliases(self):
        return [self.toggle_sms]
    
    @binding_alias('^sms (on|off)$')
    def toggle_sms(self, match, realm):
        realm.send_to_mud = False
        status = match.group(1)
        realm.cwrite('SMS is '+('<green*>ON' if status=='on' else '<red*>OFF'))
        if status == 'on':
            self.sms_forward = True
        else:
            self.sms_forward = False
    
    @binding_trigger(['^\([\w ]+\): ',
                      '^.*(\w+) tells you, "'])
    def channel_trigger(self, match, realm):
        block = realm.block
        start_line = realm.line_index
        active_channels = realm.root.active_channels
        #realm.root.active_channels=['comm']
        #realm.root.setActiveChannels(['comm'])
        for i in xrange(start_line, len(block)-1):
            block[i].channels = active_channels + ['comm']
        #realm.root.setActiveChannels(active_channels)
        
    @binding_gmcp_event('Comm.Channel.Text')
    def sms_tell(self, data, realm):
        #realm.root.debug('huh')
        if self.sms_forward==True and data['channel'].startswith('tell'):
            
            tell_from = data['talker']
            if tell_from.lower()=='alesei':
                return
            msg = re.search('\\"(.*)\\"', data['text'])
            #realm.root.debug(msg.string)
            if msg == None:
                return
            msg = msg.group(1)
            #realm.root.debug('%s,%s'%(tell_from, msg))
            account_sid = "AC86e03751b03f2c43a49d202481e4a7a2"
            auth_token = "0abc4747d82c6d50bd14e253966c28ae"
            client = rest.TwilioRestClient(account_sid, auth_token)
 
            client.messages.create(to="+13125437626", from_="+13125614574",
                                     body="Tell from %s: %s"%(tell_from, msg))