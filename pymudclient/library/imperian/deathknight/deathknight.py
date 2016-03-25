'''
Created on Oct 6, 2015

@author: Dmitry
'''
from pymudclient.modules import   EarlyInitialisingModule
from pymudclient.aliases import binding_alias
from pymudclient.triggers import binding_trigger
from pymudclient.gmcp_events import binding_gmcp_event
import time
from pymudclient.library.imperian.deathknight.weaponmastery import WeaponMasteryCommands
from pymudclient.library.imperian.deathknight.DeathknightCombo import DeathknightCombo

def shield_handler(realm, shield_status):
    realm.cwrite('SHIELD HANDLER, SHIELD HANDLER:')
    if realm.get_state('attack_queued'):
        
        realm.send('fc')


limb_priority=['torso','head','left leg','right arm','right leg','right arm']
class Deathknight(EarlyInitialisingModule):
    '''
    classdocs
    '''


    def __init__(self, realm, communicator, aff_tracker, shield_track,
                 weapons,
                 autoparry, limb_trackers):
        self.aff_tracker = aff_tracker
        self.communicator =communicator
        self.aff_tracker.apply_priorities([('haemophilia',1)])
        #self.shield_track = ShieldRez(realm, shield_handler, shield_handler)
        self.shield_track = shield_track
        self.prev_target=''
        self.next_balance=0
        self.next_equilibrium=0
        self.realm = realm
        self.display_data={}
        self.display_attack_counter=-1
        self.gags=True
        self.post_combo = False
        self.combo_fired = False
        self.autoparry = autoparry
        self.realm.registerEventHandler('setTargetEvent', self.on_target_set)
        self.combo_maker = DeathknightCombo(weapons, aff_tracker, shield_track, limb_trackers)
    
    @property
    def modules(self):
        return [WeaponMasteryCommands, self.combo_maker]
    
    @property
    def aliases(self):
        return [self.bulwark, self.pk, self.pk_solo, self.auto_macro,
                self.finish, 
                self.rv, 
                self.prep, 
                self.break_it, 
                self.tendoncut, 
                self.seal,
                self.seal2]
    
    @property
    def triggers(self):
        return [self.trueassess_trigger,
                self.clot, self.on_balance,
                self.on_equilibrium,
                self.bloodscent_enter,
                self.bloodscent_leave,
                self.just_gag,
                self.quickdraw_weapons,
                self.target_nothing,
                self.slash_attack,
                self.lacerate_attack,
                self.shred_attack,
                self.hack_attack,
                self.toxin_hit,
                self.on_prompt,
                self.engage,
                self.raze_attack,
                self.teeth,
                self.fleshburn,
                self.soulquench,
                self.rage]
    @property
    def macros(self):
        return {'<F1>':'delayed pk',
                'C-q':'delayed pk',
                '<F2>':'delayed finish',
                'C-w':'delayed finish',
                '<F3>':'delayed rv',
                '<F4>':'delayed pks',
                'C-a':'delayed pks',
                '<F12>':'sh',
                'C-e':'sh',
                '<F11>':'queue eqbal bwind',
                'C-b':'queue eqbal bwind'} 
        
    @property
    def gmcp_events(self):
        return[self.on_char_afflictions_add]
        
    @binding_gmcp_event('Char.Afflictions.Add')
    def on_char_afflictions_add(self, gmcp_data, realm):
        if gmcp_data['name']=='peace':
            realm.send('rage') 
    
    
    @binding_trigger('^You sense through your hound that (\w+) has entered the area.$')
    def bloodscent_enter(self, match, realm):
        player = match.group(1)
        area = realm.root.gmcp['Room.Info']['area']
        self.communicator.player_entered(player, area)    
    
    @binding_trigger('^You sense through your hound that (\w+) has left the area.$')
    def bloodscent_leave(self, match, realm):
        player = match.group(1)
        area = realm.root.gmcp['Room.Info']['area']
        self.communicator.player_left(player, area)
    
    
    
    @binding_trigger('^Autocuring: clot$')
    def clot(self, match,realm):
        realm.safe_send('clot|clot|clot|clot|clot')
    
    
    
    
    
    @binding_trigger('^Balance Taken: (\d+\.\d+)s$')
    def on_balance(self, match, realm):
        #realm.root.set_state('attack_queued',False)
        self.next_balance=time.time()+float(match.group(1))
       
    @binding_trigger('^Equilibrium Taken: (\d+\.\d+)s$')
    def on_equilibrium(self, match,realm):
        self.next_equilibrium=time.time()+float(match.group(1))
    
    @property
    def to_balance(self):
        return max(0, self.next_balance-time.time())
    
    @property
    def to_equilibrium(self):
        return max(0, self.next_equilibrium-time.time())
    
    @property
    def to_eqbal(self):
        return max(self.to_balance, self.to_equilibrium)    
        
        
    def on_target_set(self, target):
        self.aff_tracker.tracker(target).reset()
    
    def auto_macro_do(self, realm, command):
        realm.send(command)
        
        
    @binding_trigger(['^You are afflicted with peace\.$',
                    '^You are feeling far too passive to do that\.$'])
    def rage(self, match, realm):
        realm.send("rage")
        
    @binding_alias('^delayed (\w+)$')
    def auto_macro(self, matches, realm):
        command = matches.group(1)
        realm.send_to_mud = False
        delay = self.to_eqbal
        realm.root.debug('delay: %f'%delay)
        if delay > 0.1:
            realm.cwrite('Scheduling AUTO MACRO in <red*>%0.2f<white> seconds'%float(delay))
            realm.root.set_timer(delay-0.1, self.auto_macro_do, command)
        else:
            self.auto_macro_do(realm, command) 
            
    @binding_alias('^pk$')
    def pk(self, match, realm):
        realm.send_to_mud = False
        self.combo_fired=True
        target = realm.root.get_state('target')
        parry = self.autoparry.evaluate_parry()
        combo = self.combo_maker.get_combo(realm, target)
        if parry!='':
            combo='parry %(parry)s|%(combo)s'%{'parry':parry,
                                               'combo':combo}
        realm.send('queue eqbal %s'%combo)
        
    @binding_alias('^pks$')
    def pk_solo(self, match, realm):
        realm.send_to_mud = False
        self.combo_fired=True
        target = realm.root.get_state('target')
        parry = self.autoparry.evaluate_parry()
        combo = self.combo_maker.get_solo_combo(realm, target)
        if parry!='':
            combo='parry %(parry)s|%(combo)s'%{'parry':parry,
                                               'combo':combo}
        realm.send('queue eqbal %s'%combo)
    
    @binding_alias('^prep$')
    def prep(self, match, realm):
        realm.send_to_mud = False
        target = realm.root.get_state('target')
        parry = self.autoparry.evaluate_parry()
        combo = self.combo_maker.prep_limb(realm, target, limb_priority)
        if parry!='':
            combo='parry %(parry)s|%(combo)s'%{'parry':parry,
                                               'combo':combo}
        realm.send('queue eqbal %s'%combo)
    
    @binding_alias('^prep1$')
    def break_it(self, match, realm):
        target = realm.root.get_state('target')
        
        realm.send('queue eqbal target head|displace nothing|wm hack hack %s butisol hemotoxin'%target)
     
    @binding_alias('^prep2$')
    def tendoncut(self, match, realm):
        target = realm.root.get_state('target')
        
        realm.send('queue eqbal target nothing|wm tendoncut slash %s torso bromine'%target)
        
    @binding_alias('^prep3$')
    def seal(self, match, realm):
        target = realm.root.get_state('target')
        
        realm.send('queue eqbal quickdraw sabre|wm slash slash %s iodine mercury'%target)
    @binding_alias('^prep4$')
    def seal2(self, match, realm):
        target = realm.root.get_state('target')
        
        realm.send('queue eqbal quickdraw sabre|wm slash slash %s hemotoxin ciguatoxin'%target)
      
    @binding_alias('^rv')
    def rv(self, match, realm):
        realm.send_to_mud = False
        self.combo_fired=True
        target = realm.root.get_state('target')
        parry = self.autoparry.evaluate_parry()
        combo = self.combo_maker.get_reave(realm, target)
        if parry!='':
            combo='parry %(parry)s|%(combo)s'%{'parry':parry,
                                               'combo':combo}
        realm.send('queue eqbal %s'%combo)
    
    @binding_alias('^finish$')
    def finish(self, match, realm):
        realm.send_to_mud=False
        self.combo_fired=True
        target = realm.root.get_state('target')
        combo = self.combo_maker.get_finish(realm, target)
        parry = self.autoparry.evaluate_parry()
        if parry!='':
            combo='parry %(parry)s|%(combo)s'%{'parry':parry,
                                               'combo':combo}
        realm.send('queue eqbal %s'%combo)
    
    
    @binding_alias('^sh$')
    def bulwark(self, match,realm):
        realm.send_to_mud = False
        realm.send('queue eqbal curseward|bulwark')
    
    
    
    @binding_trigger("^(\w+)'s condition stands at (\d+)/(\d+) health and (\d+)/(\d+) mana\.$")
    def trueassess_trigger(self, match, realm):
        #if self.gags and self.combo_fired:
        #    realm.display_line=False
        person = match.group(1).lower()
        hp=int(match.group(2))
        max_hp=int(match.group(3))
        mana=int(match.group(4))
        max_mana=int(match.group(5))
        target = realm.root.get_state('target').lower()
        #realm.send('rt %s: %d/%d HP, %d/%d (%0.0f%%) Mana'%
        #          (person.upper(), hp, max_hp, mana, max_mana, 100*float(mana)/float(max_mana)))
        self.communicator.send_health_mana(person, hp, max_hp, mana, max_mana)
        if target==person:
            realm.root.fireEvent('targetStatUpdateEvent','hp',hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana',mana)
            realm.root.fireEvent('targetStatUpdateEvent','hp_max',max_hp)
            realm.root.fireEvent('targetStatUpdateEvent','mana_max',max_mana)
            
        
    
  
            
    
  
            
            
    #Gags and replacements
    @binding_trigger(['^You already have curseward up\.$',
                      "^Removed defense: \[u'anti-weapon field'\]$",
                      'Added defense: engage',
                      'Your aura of weapons rebounding disappears\.$',
                      '^You have lost the anti-weapon field defence\.$',
                      '^You have gained the engage defence\.$',
                      '^Mana Lost:',
                      '^You order a ravenous hound to attack (\w+)$',
                      '^Your aura of weapons rebounding disappears\.$'
                      '^A ravenous hound obeys your command\.$'
                      '^Your aura of weapons rebounding disappears\.$',
                      '^You rub some (\w+) on (?:a|an) (.*)\.$',
                      '^You are already engaging (\w+)\.$',
                      '^\w+ appears terrified as (?:her|his) muscles seem to become difficult to control\.$'])
    def just_gag(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line=False
        
    @binding_trigger('^You secure your previously wielded items and instantly draw (?:a|an) (.*) into your (\w+) hand, with (?:a|an) (.*) flowing into your right hand\.$')
    def quickdraw_weapons(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line=False
        item1=match.group(1)
        hand1=match.group(2)
        item2=match.group(3)
        self.display_data['left_hand']=item1 if hand1=='left' else item2
        self.display_data['right_hand']=item1 if hand1=='right' else item2
        
    @binding_trigger('^You will now aim your attacks wherever you see openings\.$')
    def target_nothing(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line = False
        self.display_data['limb']='None'
        
    @binding_trigger(['^With a lightning-quick motion, you slash (\w+) with (?:a|an) (.*)\.$',
                      '^You slash viciously into (\w+) with (?:a|an) .*\.$',
                      '^You swing (?:a|an) .* at (\w+) with a powerful strike\.$'])
    def slash_attack(self, match, realm):
        self.single_attack(match.group(1), 'Slash', realm)
    
    @binding_trigger("^You lacerate (\w+)'s skin calmly with the sharp edge of (?:a|an) (.*), amplifying (?:his|her) bleeding wounds\.$")
    def lacerate_attack(self, match, realm):
        self.single_attack(match.group(1), 'Lacerate', realm)
        
    @binding_trigger("^You shred (\w+)'s skin viciously with (?:a|an) .*, causing a nasty infection.")
    def shred_attack(self, match, realm):
        self.single_attack(match.group(1), "Shred", realm)
        
    @binding_trigger("^You hack at (\w+)'s (\w+) with a gleaming scimitar\.$")
    def hack_attack(self, match, realm):
        self.single_attack(match.group(1), 'Hack (%s)'%match.group(2), realm)
        
    def single_attack(self, target, attack, realm):
        if not self.post_combo:
            if self.aff_tracker.tracker(target)['haemophilia'].on:
                self.haemophilia_combo_counter+=1
            else:
                self.haemophilia_combo_counter=0
        if self.gags and self.combo_fired:
            realm.display_line=False
        self.post_combo=True
        self.display_attack_counter+=1
        self.display_data['target']=target
        if not 'attacks' in self.display_data:
            self.display_data['attacks'] =[]
        if len(self.display_data['attacks']) <= self.display_attack_counter:
            self.display_data['attacks'].append({})
        self.display_data['attacks'][self.display_attack_counter]['attack']=attack
        
        
    @binding_trigger('^Your (\w+) toxin has affected (\w+)\.$')
    def toxin_hit(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line = False
        if self.display_attack_counter>=0:
            self.display_data['attacks'][self.display_attack_counter]['toxin']=match.group(1)
    
    @binding_trigger('^You move in to engage (\w+)')
    def engage(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line=False
        self.display_data['engage']=match.group(1)
    
    @binding_trigger('^H:(\d+) M:(\d+)')
    def on_prompt(self, match, realm):
        
        if self.post_combo:
            self.combo_fired=False
            realm.cwrite(self.build_output())
            target = realm.root.get_state('target')
            tracker = self.aff_tracker.tracker(target)
            realm.cwrite('<red*:yellow>COOLDOWNS: TREE %(tree)d, PURGE %(purge)d'%{'tree':tracker.time_to_next_tree(),
                                                                                   'purge':tracker.time_to_next_purge()})
            self.display_data={}
            self.display_attack_counter=-1
     
            self.post_combo = False
        
    @binding_trigger(['^You raze (\w+)\'s aura of rebounding with .+\.$',
                      '^You whip .+ through the air in front of (\w+), to no effect\.$',
                      '^You raze (\w+)\'s translucent shield with (.*)\.$'])
    def raze_attack(self, match, realm):
        self.single_attack(match.group(1), 'Raze', realm)
  
    @binding_trigger("^As the weapon strikes (\w+), it burns (?:his|her) flesh painfully\.$")
    def fleshburn(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line = False
        if 'flares' not in self.display_data['attacks'][self.display_attack_counter]:
            self.display_data['attacks'][self.display_attack_counter]['flares']=[]
        self.display_data['attacks'][self.display_attack_counter]['flares'].append('Fleshburn')
    
    @binding_trigger("^As the weapon strikes (\w+), (?:she|he) pales and (?:her|his) flesh clings closer to (?:her|his) bones\.$")
    def soulquench(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line = False
        if 'flares' not in self.display_data['attacks'][self.display_attack_counter]:
            self.display_data['attacks'][self.display_attack_counter]['flares']=[]
        self.display_data['attacks'][self.display_attack_counter]['flares'].append('Soulquench')
    
    @binding_trigger("^The teeth along the weapon edge cut into (\w+)'s flesh\.$")
    def teeth(self, match, realm):
        if self.gags and self.combo_fired:
            realm.display_line = False
        if 'flares' not in self.display_data['attacks'][self.display_attack_counter]:
            self.display_data['attacks'][self.display_attack_counter]['flares']=[]
        self.display_data['attacks'][self.display_attack_counter]['flares'].append('Teeth')
    
    def build_output(self):
        output=''
        if not 'attacks' in self.display_data:
            return ''
        for data in self.display_data['attacks']:
            output+='\n<white>     [T: <red*> %15s <white>Attack: <'%self.display_data['target']
            if data['attack']=='Slash':
                output+='yellow*>'
            elif data['attack']=='Lacerate':
                output+='purple*>'
            elif data['attack']=='Shred':
                output+='cyan*>'
            elif data['attack']=='Raze':
                output+='white*>'
            elif data['attack'].startswith('Hack'):
                output+='brown*>'
            output+='%10s<white>'%data['attack']
            if 'toxin' in data:
                output+=' Toxin: <green*> %15s'%data['toxin']
            if 'flares' in data:
                output+=' <white>Enh: '
                flare_texts=[]
                for flare in data['flares']:
                    
                    if flare=='Teeth':
                        flare_texts.append('<black*:white>%10s'%'Teeth')
                    if flare=='Fleshburn':
                        flare_texts.append('<red*:white>%10s'%'Fleshburn')
                    if flare=='Soulquench':
                        flare_texts.append('<green*:white>%10s'%'Soulquench')
                    if flare=='Negating':
                        flare_texts.append('<blue*:white>%10s'%'Negating')
                output+='<white>,'.join(flare_texts)
            output+='<white>]'
        if 'engage' in self.display_data:
            extras=[]
            output+='\n<white>     ['
            if 'engage' in self.display_data:
                extras.append('<white*:blue>++Engaged++')
                
            output+=','.join(extras)
            output+='<white>]'    
            
        return output
        