default_location = 'muddata'
import os, json

def save_config(config_category, file_name, data, character=None, append=False):
    if character:
        folder_path = os.path.join(os.path.expanduser('~'), default_location, config_category, character)
    else: 
        folder_path = os.path.join(os.path.expanduser('~'), default_location, config_category)
        
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)
    
    path = '%(path)s/%(file)s.xml'%{'path':folder_path,
                                    'file':file_name}
    
     
    f = open(path, 'a' if append else 'w')
    f.write(json.dumps(data))
    f.close()
    
def load_config(config_category, file_name, character=None):
    if character:
        folder_path = os.path.join(os.path.expanduser('~'), default_location, config_category, character)
    else: 
        folder_path = os.path.join(os.path.expanduser('~'), default_location, config_category)
    path = '%(path)s/%(file)s.xml'%{'path':folder_path,
                                    'file':file_name}
    if os.path.isfile(path):
        f=open(path,'r')
        s = f.read()
        f.close
        return json.loads(s)
    else:
        return {}