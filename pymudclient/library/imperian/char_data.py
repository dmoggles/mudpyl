'''
Created on Mar 9, 2016

@author: Dmitry
'''
import requests
import json
import re
char_data={}

def get_char_data( name):
    if name.lower() in char_data:
        return char_data[name.lower()]
    else:
        r=requests.get('http://api.imperian.com/characters/%s.json'%name.lower())
        
        if not r.status_code == 200:
            return None
        else:
            d=json.loads(r.text)
            description = d['description']
            d1=description.split('.')[0]+'.'
            statpack = re.match('(?:She|He) is (?:a|an)(?:.*)? (\w+) (?:\w+)\.',d1).group(1)
            d['statpack']=statpack
            char_data[name.lower()]=d
            return d
                