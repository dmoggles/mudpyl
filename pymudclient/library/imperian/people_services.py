'''
Created on Mar 8, 2016

@author: Dmitry
'''
from pymudclient.modules import EarlyInitialisingModule
from pymudclient.aliases import binding_alias
from pymudclient.triggers import binding_trigger

from pymudclient.colours import PURPLE, BROWN, ORANGE
from pymudclient.config_helper import load_config, save_config
from pymudclient.library.imperian.char_data import get_char_data



profession_map={'deathknight':'demonic',
                'defiler':'demonic',
                'summoner':'demonic',
                'diabolist':'demonic',
                'assassin':'demonic',
                'wytch':'demonic',
                'runeguard':'magick',
                'bard':'magick',
                'druid':'magick',
                'hunter':'magick',
                'renegade':'magick',
                'mage':'magick',
                'templar':'antimagick',
                'monk':'antimagick',
                'priest':'antimagick',
                'berserker':'antimagick',
                'ranger':'antimagick',
                'predator':'antimagick',
                'outrider':'antimagick',
                'amazon':'antimagick'}

damage_map={'physical':['berserker',
                        'templar',
                        'ranger',
                        'amazon',
                        'monk',
                        'assassin',
                        'deathknight',
                        'defiler',
                        'druid',
                        'outrider',
                        'predator',
                        'priest',
                        'renegade',
                        'runeguard'],
            'mental':['hunter',
                      'mage',
                      'bard',
                      'diabolist',
                      'summoner',
                      'wytch']}

config_category='people_services'
circle_db_file='circle_db'
people_db_file='people_db'

class PeopleServices(EarlyInitialisingModule):

    def __init__(self, realm):
        self.people_db=load_config(config_category,people_db_file)
        self.circle_db=load_config(config_category,circle_db_file)
        if len(self.circle_db)==0:
            self.circle_db={'antimagick':{}, 'magick':{}, 'demonic':{}}
        self.who_state = 'none'
        self.realm=realm
#         for person in self.people_db:
#             data = self.people_db[person]
#             if not person.capitalize() in self.realm.highlights:
#                 if 'profession' in data and data['profession'] in profession_map:
#                     self.realm.add_highlight(person.capitalize(), self.get_color_tag(profession_map[data['profession'].lower()]), True)
#          
        
        
    
    @property
    def aliases(self):
        return [self.full_who,
                self.print_circles,
                self.check_person]
        
    @property
    def triggers(self):
        return [self.who_end_trigger,
                self.who_trigger]
        
    def get_color(self, circle):
        if circle=='demonic':
            return 'purple*'
        elif circle == 'magick':
            return 'brown*'
        else:
            return 'orange*'
    
    def get_color_tag(self, circle):
        if circle=='demonic':
            return PURPLE
        if circle=='magick':
            return BROWN
        if circle == 'antimagick':
            return ORANGE
    
    
    def check_circle(self, person):
        for k in self.circle_db:
            if person.lower() in self.circle_db[k]:
                return k
        return ''
            
    
    @binding_alias('^check_person (\w+)$')
    def check_person(self, match, realm):
        realm.send_to_mud=False
        name=match.group(1)
        self.process_person(name.capitalize())
        save_config(config_category, circle_db_file, self.circle_db)
        save_config(config_category, people_db_file, self.people_db)
        
    @binding_alias('^print circles$')
    def print_circles(self, match, realm):
        realm.send_to_mud = False
        realm.cwrite('\n'.join('<%(color)s>%(circle)s<white>: %(plist)s'%{'color':self.get_color(k),
                                                                   'circle':k,
                                                                   'plist':', '.join(sorted(self.circle_db[k].keys()))} for k in self.circle_db))
    
    @binding_alias('^fwho$')
    def full_who(self, match, realm):
        realm.send_to_mud = False
        self.who_state = 'full_who'
        realm.send('who')
        
    def process_person(self, person):
        data = get_char_data(person)
        self.people_db[data['name'].lower()]=data
        if not 'profession' in data or data['profession']==u'':
            return
        self.circle_db[profession_map[data['profession'].lower()]][data['name'].lower()]=data
        if not person in self.realm.highlights:
            self.realm.add_highlight(person, self.get_color_tag(profession_map[data['profession'].lower()]), True)
            
    @binding_trigger("^(?: *)(\w+) - .*$")
    def who_trigger(self, match, realm):
        
        target = match.group(1)
        if self.who_state == 'full_who':
            self.process_person(target)
            
    @binding_trigger('^There are (\d+) players in this world\.$')
    def who_end_trigger(self, match, realm):
        if self.who_state == 'full_who':
            self.who_state = None
            save_config(config_category, circle_db_file, self.circle_db)
            save_config(config_category, people_db_file, self.people_db)