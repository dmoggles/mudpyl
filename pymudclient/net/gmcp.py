'''
Created on Jul 16, 2015

@author: Dmitry
'''
from twisted.internet.protocol import Protocol
import json
import re
import pymudclient


GMCP = chr(201)
GMCP_HANDSHAKE_1='Core.Hello { "client": "pymudclient", "version": "'+ pymudclient.__version__ +'" }'
GMCP_HANDSHAKE_2='Core.Supports.Set [ "Core 1", "Char 1", "Char.Name 1", "Char.Skills 1", "Char.Items 1", "Comm.Channel 1", "Redirect 1", "Room 1", "IRE.Rift 1", "IRE.Composer 1" ]'
GMCP_PING='Core.Ping'


decoder = re.compile('^([A-Za-z\.]*) (({|\[).*(}|\]))$')



class ImperianGmcpHandler:
    '''TODO: Better handling of unsupported gmcp types'''
        
    @staticmethod
    def handshakeMessages():
        return [GMCP_HANDSHAKE_1,GMCP_HANDSHAKE_2]
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
                    
            
        else:
            print("Oh OH! %s"%data_string)
        
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
    
def create_string(data,indent, base_indent=0):
    '''TODO: The output doesn't handle nesting THAT well.  Fix it'''
        
    if isinstance(data, dict):
        return "{\n"+ '\n'.join([' '*indent+create_string(i,indent, base_indent)+': '+create_string(data[i],indent+indent,indent) for i in data])+'\n' + base_indent* ' ' +'}'
    elif isinstance(data, list):
        return "[\n"+ '\n'.join([' '*indent+create_string(i, indent+indent,indent)+',' for i in data])[:-1] + '\n' + ' '*base_indent + ']'
    else:
        return str(data)
                



