'''
Created on Jul 16, 2015

@author: Dmitry
'''
from twisted.internet.protocol import Protocol
import json
import re
import pymudclient


GMCP = chr(201)
GMCP_PING='Core.Ping'


decoder = re.compile('^([A-Za-z\.]*) (({|\[).*(}|\]))$')
string_decoder = re.compile('^([A-Za-z\.]*) (\"\w+\")$')


class GmcpHandler:
    '''TODO: Better handling of unsupported gmcp types'''
        
    #@staticmethod
    #def handshakeMessages():
    #    return [GMCP_HANDSHAKE_1,GMCP_HANDSHAKE_2]
    @staticmethod
    def process(bytes,realm):
        data_string = ''.join(bytes)
        result=decoder.match(data_string)
        if not result == None:
            
            message_type = result.group(1)
            message_data = result.group(2)
            gmcp_data = json.loads(message_data)
            realm.gmcp[message_type]=gmcp_data
            
            realm.gmcpReceived((message_type, gmcp_data))
                    
            
        else: #the payload is just a string
            result = string_decoder.match(data_string)
            if not result == None:
                message_type = result.group(1)
                message_data = result.group(2)
                realm.gmcp[message_type]=message_data
                realm.gmcpReceived((message_type, message_data))
            else:
                print('Really unknown GMCP type %s'%data_string)
        
        #structure = json.load(''.join(bytes))
        #print(structure)
    @staticmethod
    def gmcpToString(gmcp, tag=None):
        '''Neither json.dumps nor pprint seems to be up to the task for some reason, so sure, let's do this by hand, why not?
        '''
        if tag==None:
            root = gmcp
        elif gmcp.has_key(tag):
            root=gmcp[tag]
        else:
            return ''
        
        return json.dumps(root,indent=2, separators=(',',':'), sort_keys=True)
    
                



