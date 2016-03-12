'''
Created on Sep 18, 2015

@author: Dmitry
'''
import gtk
import csv
import os
import pango
import time

from pymudclient.gui.gui_elements import BlackEventBox, FormattedLabel,\
    BlackFrame, HpManaWidget, HpManaPanel, BleedPanel
    
import pymudclient.gui.gui_elements as ge
from pymudclient.library.imperian.char_data import get_char_data

TREE_BALANCE=15
PURGE_BALANCE=15
FOCUS_BALANCE=4

HERB_BALANCE=2
SALVE_BALANCE=3
PIPE_BALANCE=3

    


GUI_CURES=['orphine',
           'kelp',
           'mandrake',
           'wormwood',
           'galingale',
           'nightshade',
           'maidenhair',
           'toadstool',
           'caloric',
           'epidermal',
           'laurel',
           'lovage']





        
class AffLabel(BlackEventBox):
    def __init__(self,name,short_name,light):
        BlackEventBox.__init__(self)
        self.label = gtk.Label(short_name)
        self.label.modify_font(pango.FontDescription('monospace 8'))
        self.label.set_alignment(0.0,0.0)
        self.add(self.label)
        self.light=light
        if light:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.PINK))
        else:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.PURPLE))
            
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
        self.status=False
        
    def set(self, status):
        self.status = status
        if self.status == False:
            self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(ge.BG_BLACK))
        else:
            if self.light:
                self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.DARK_RED))
            else:
                self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(ge.RED))

class AffGroup(BlackEventBox):
    def __init__(self, cure_name, affs, panel=None):
        BlackEventBox.__init__(self)
        self.cure_name=cure_name        
        self.frame=BlackFrame(cure_name)
        self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(ge.BG_DARK_GRAY))
        t=gtk.Table(columns=1, rows=len(affs),homogeneous=True)
        self.labels={}
        for i, (name,short_name) in enumerate(affs):
            label=AffLabel(name,short_name,i%2==0)
            t.attach(label,
                     left_attach=0,right_attach=1,top_attach=i, bottom_attach=i+1)
            self.labels[name]=label
            if panel:
                panel.all_labels[name]=label
        
        self.frame.add(t)
        self.add(self.frame)
    
    def __getitem__(self,item):
        return self.labels[item]
        
class AffPanel(BlackEventBox):
    def __init__(self, client):
        BlackEventBox.__init__(self)
        f=BlackFrame('Afflictions')
        self.target=''
        t=gtk.Table(columns=6,rows=1,homogeneous=True)
        f.add(t)
        self.all_labels={}
        self.add(f)
        vboxes=[gtk.VBox() for i in xrange(6)]
        for i in xrange(6):
            t.attach(vboxes[i],left_attach=i,right_attach=i+1,top_attach=0, bottom_attach=1)
        
        aff_file=open(os.path.join(os.path.expanduser('~'),'muddata','affs_gui.csv'),'r')
        
        reader=csv.DictReader(aff_file)
        affs={c:[] for c in GUI_CURES}
        for row in reader:
            if row['cure'] in GUI_CURES:
                affs[row['cure']].append((row['affliction'],row['short_name']))
            #if row['cure2'] in GUI_CURES:
            #    affs[row['cure2']].append((row['affliction'],row['short_name']))
        
        for i,c in enumerate(affs.keys()):
            group = AffGroup(c,affs[c],self)
            vboxes[i%6].pack_start(group, expand=False)
        
        client.registerEventHandler('afflictionGainedEvent', self.on_affliction_gained)
        client.registerEventHandler('afflictionLostEvent', self.on_affliction_lost)
        client.registerEventHandler('setTargetEvent', self.on_set_target)
        
    def on_set_target(self, target):
        self.target = target
        
    def on_affliction_gained(self, target, afflictions):
        if target == self.target:
            for a in afflictions:
                self.set(a, True)
                
    def on_affliction_lost(self, target, afflictions):
        if target == self.target:
            for a in afflictions:
                self.set(a, False)
             
    def set(self, affliction, on):
        if affliction in self.all_labels:
            self.all_labels[affliction].set(on)  
    
    def reset_affs(self):
        for aff in self.all_labels.values():
            aff.set(False)

           
class CountdownTimer(BlackEventBox):
    def __init__(self, max_value):
        BlackEventBox.__init__(self)
        self.l=FormattedLabel(0)
        self.l.modify_font(pango.FontDescription('monospace 12'))
        
        self.max_value = max_value
        self.add(self.l)
        
    def set_value(self, value):
        self.l.set_text('%0.2f'%value)
        if value > self.max_value:
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.RED))
            self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.OFF_WHITE))
        else:
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
            if value == 0:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.OFF_WHITE))
            elif value < 0.25*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.GREEN))
            elif value < 0.5*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.YELLOW))
            elif value < 0.75*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.ORANGE))
            else:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.RED))
                
                
class CountdownBar(BlackEventBox):
    def __init__(self,  max_seconds):
        BlackEventBox.__init__(self)
        self.pb=gtk.ProgressBar()
        self.pb.set_fraction(0.0)
        self.pb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
        self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.RED))
        self.max_seconds=max_seconds
        self.add(self.pb)
        
    def set_value(self, seconds):
        if seconds <= self.max_seconds:
            value = float(seconds)/float(self.max_seconds)
            if value == 0:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.OFF_WHITE))
            elif value < 0.25:
                pass
                #self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.GREEN))
            elif value < 0.5:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.YELLOW))
            elif value < 0.75:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.ORANGE))
            else:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.RED))
        else:
            value = 1.0
            self.pb.set_fraction(1.0)
            self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.RED))
        #print(value)
        self.pb.set_fraction(value)
            
            
class CountdownWidget(BlackEventBox):
    def __init__(self, name, seconds):
        BlackEventBox.__init__(self)
        self.working=False
        self.timer_start=0
        f=BlackFrame("")
        t=gtk.Table(columns=4, rows=1, homogeneous=True)
        l = FormattedLabel(name)
        vbox=gtk.VBox()
        self.timer_label=CountdownTimer(seconds)
        self.timer_bar = CountdownBar(seconds)
        vbox.pack_start(self.timer_label, expand=True)
        vbox.pack_start(self.timer_bar, expand=True)
        t.attach(l, left_attach=0, right_attach=1, top_attach=0, bottom_attach=1)
        t.attach(vbox, left_attach=1, right_attach=4, top_attach=0, bottom_attach=1)
        f.add(t)
        self.add(f)
    
    def set_seconds(self, seconds):
        self.timer_label.set_value(seconds)
        self.timer_bar.set_value(seconds)
    def reset(self):
        self.timer_start = time.time()
        self.working=True
        self.set_seconds(0)
        
    def update(self):
        if self.working:
            seconds = time.time() - self.timer_start
            self.set_seconds(seconds)
     
    def turn_off(self):
        self.working=False
        self.set_seconds(0)      

class ToggleLabel(BlackEventBox):
    def __init__(self, label,  color):
        BlackEventBox.__init__(self)
        self.label=FormattedLabel(label)
        self.color = color
        self.label.modify_font(pango.FontDescription('monospace 12'))
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(self.color))
        self.add(self.label)
        
        
        
    def set_state(self, state):
        if state:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(self.color))
        else:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(self.color))
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
        

class ShieldBox(BlackEventBox):
    def __init__(self, realm):
        BlackEventBox.__init__(self)
        self.shield=ToggleLabel('Shield',ge.RED)
        self.rebound=ToggleLabel('Rebounding',ge.RED)
        self.prism=ToggleLabel('Prismatic',ge.RED)
        self.curseward=ToggleLabel('Curseward',ge.PURPLE)
        f = BlackFrame('Shields')
        t=gtk.Table(columns=2,rows=2,homogeneous=True)
        t.attach(self.shield, top_attach=0, bottom_attach=1, left_attach=0, right_attach=1)
        t.attach(self.curseward, top_attach=1, bottom_attach=2, left_attach=0, right_attach=1)
        t.attach(self.rebound, top_attach=0, bottom_attach=1, left_attach=1, right_attach=2)
        t.attach(self.prism, top_attach=1, bottom_attach=2, left_attach=1, right_attach=2)
        f.add(t)
        self.add(f)
        self.target = ''
        realm.registerEventHandler('setTargetEvent',self.set_target)
        realm.registerEventHandler('shieldEvent', self.on_shield_event)
        realm.registerEventHandler('reboundingEvent', self.on_rebounding_event)
        realm.registerEventHandler('barrierEvent', self.on_barrier_event)
        realm.registerEventHandler('cursewardEvent', self.on_curseward_event)
        
    def set_target(self, target):
        self.target = target
        
    def on_shield_event(self, target, value):
        if target == self.target:
            self.set_shield('shield', value==1)
            
    def on_rebounding_event(self, target, value):
        if target == self.target:
            
            self.set_shield('rebound', value==1)
            
    def on_barrier_event(self, target, value):
        if target == self.target:
            self.set_shield('prism', value==1)
            
    def on_curseward_event(self, target, value):
        if target == self.target:
            self.set_shield('curseward', value==1)
            
            
    def set_shield(self, shield, state):
        if shield=='shield':
            self.shield.set_state(state)
        if shield=='rebound':
            self.rebound.set_state(state)
        if shield=='curseward':
            self.curseward.set_state(state)
        if shield=='prism':
            self.prism.set_state(state)
    
    def all_off(self):
        self.shield.set_state(False)
        self.rebound.set_state(False)
        self.curseward.set_state(False)
        self.prism.set_state(False)

class CountdownPanel(BlackEventBox):
    def __init__(self):
        BlackEventBox.__init__(self)
        f = BlackFrame('Cooldowns')
        t=gtk.Table(columns=2, rows=3, homogeneous=True)
        self.cooldowns={'herb':CountdownWidget('Herb',HERB_BALANCE),
                        'pipe':CountdownWidget('Smoke',PIPE_BALANCE),
                        'salve':CountdownWidget('Salve',SALVE_BALANCE),
                        'focus':CountdownWidget('Focus',FOCUS_BALANCE),
                        'purge':CountdownWidget('Purge',PURGE_BALANCE),
                        'tree':CountdownWidget('Tree',TREE_BALANCE)}
        t.attach(self.cooldowns['herb'],left_attach=0, right_attach=1, top_attach=0, bottom_attach=1)
        t.attach(self.cooldowns['pipe'],left_attach=0, right_attach=1, top_attach=1, bottom_attach=2)
        t.attach(self.cooldowns['salve'],left_attach=0, right_attach=1, top_attach=2, bottom_attach=3)
        t.attach(self.cooldowns['focus'],left_attach=1, right_attach=2, top_attach=0, bottom_attach=1)
        t.attach(self.cooldowns['purge'],left_attach=1, right_attach=2, top_attach=1, bottom_attach=2)
        t.attach(self.cooldowns['tree'],left_attach=1, right_attach=2, top_attach=2, bottom_attach=3)
        f.add(t)
        
        self.add(f)
    
    def reset(self):
        for v in self.cooldowns.values():
            v.reset()
    def reset_one(self, cooldown):
        if cooldown in self.cooldowns:
            self.cooldowns[cooldown].reset()
            
    def update(self):
        for v in self.cooldowns.values():
            v.update()
            
    def turn_off(self):
        for v in self.cooldowns.values():
            v.turn_off()

class CharDataLabel(BlackEventBox):
    def __init__(self, name):
        BlackEventBox.__init__(self)
        f=BlackFrame(name)
        
        self.add(f)
        self.data_label = gtk.Label()
        self.data_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.OFF_WHITE))
        f.add(self.data_label) 
        
    def set_value(self, value):
        self.data_label.set_text(value)
            
class CharDataPanel(BlackEventBox):
    def __init__(self):
        BlackEventBox.__init__(self)
        f = BlackFrame('Character')
        hbox=gtk.HBox()
        self.elements={'class':CharDataLabel('Class'),
                       'level':CharDataLabel('Level'),
                       'statpack':CharDataLabel('Statpack'),
                       'org':CharDataLabel('Org')}
        
        hbox.pack_start(self.elements['class'],expand=True)
        hbox.pack_start(self.elements['level'],expand=True)
        hbox.pack_start(self.elements['statpack'],expand=True)
        hbox.pack_start(self.elements['org'],expand=True)
        f.add(hbox)
        self.add(f)
        
    def set_character(self, character):
        data = get_char_data(character)
        if data:
            self.elements['class'].set_value(data['profession'])
            self.elements['level'].set_value(data['level'])
            self.elements['org'].set_value(data['city'])
            self.elements['statpack'].set_value(data['statpack'])
            

class LimbDamageLabel(BlackEventBox):
    def __init__(self, limb_name):
        BlackEventBox.__init__(self)
        self.limb_name = limb_name
        self.title_label = FormattedLabel(limb_name)
        self.data_label = FormattedLabel('')
        self.damage=0
        self.hits_left=0
        self.confirmed_damage=0
        self.hits =0
        f=BlackFrame('')
        self.add(f)
        t=gtk.Table(rows=1, columns=3, homogeneous=True)
        f.add(t)
        t.attach(self.title_label, bottom_attach=1, top_attach=0, left_attach=0, right_attach=1)
        t.attach(self.data_label, bottom_attach=1, top_attach=0, left_attach=1, right_attach=3)
        self.update(self.damage, self.hits_left, self.confirmed_damage, self.hits)
        
        
    def update(self, damage, hits_left, confirmed_damage, hits):
        self.damage=damage
        self.hits_left=hits_left
        self.confirmed_damage=confirmed_damage
        t={0:'Non',0.33:'Hrt',0.66:'Inj'}
        c={0:ge.OFF_WHITE, 0.33:ge.YELLOW, 0.66:ge.ORANGE}
        self.data_label.set_text('%s: %d/%d %.2f'%(t[self.confirmed_damage],hits, hits_left,damage))
        self.data_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(c[confirmed_damage]))
        
        
class LimbDamagePanel(BlackEventBox):
    def __init__(self):
        BlackEventBox.__init__(self)
        f = BlackFrame('Limbs')
        self.add(f)
        t = gtk.Table(rows=3, columns=2, homogeneous=True)
        f.add(t)
        self.limbs = {'head':LimbDamageLabel('Head'),
                      'torso':LimbDamageLabel('Torso'),
                      'left arm':LimbDamageLabel('Left Arm'),
                      'right arm':LimbDamageLabel('Right Arm'),
                      'left leg':LimbDamageLabel('Left Leg'),
                      'right leg':LimbDamageLabel('Right Leg')}
        l=['head','torso','left arm','right arm','left leg','right leg']
        for i,k in enumerate(l):
            t.attach(self.limbs[k], top_attach=i/2, bottom_attach=i/2+1, left_attach=i%2, right_attach=i%2+1)
            
    def __getitem__(self, k):
        return self.limbs[k] if k in self.limbs else None
        
class EnemyPanel(BlackEventBox):
    def __init__(self, client):
        BlackEventBox.__init__(self)
        f=BlackFrame('Enemy')
        box = gtk.VBox()
        self.name_label = gtk.Label('Hello')
        self.name_label.modify_font(pango.FontDescription('monospace 20'))
        self.name_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.RED))
        box.pack_start(self.name_label, expand=False)
        self.char_data_panel=CharDataPanel()
        box.pack_start(self.char_data_panel, expand=False)
        self.cooldown_panel = CountdownPanel()
        box.pack_start(self.cooldown_panel, expand=False)
        self.aff_panel = AffPanel(client)
        box.pack_start(self.aff_panel, expand=False)
        f.add(box)
        self.add(f)
        self.shield = ShieldBox(client)
        box.pack_start(self.shield, expand=False)
        self.hp_mana = HpManaPanel("Target", client)
        box.pack_start(self.hp_mana, expand=False)
        self.limb_panel=LimbDamagePanel()
        box.pack_start(self.limb_panel, expand=False)
        
    def set_target_here(self, is_here):
        if is_here:
            self.name_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.RED))
        else:
            self.name_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(GREEN))
    
    
    def set_shield(self, shield, state):
        self.shield.set_shield(shield, state)
        
    def all_shields_off(self):
        self.shield.all_off()
        
    def set_target(self, target):
        self.aff_panel.reset_affs()
        self.name_label.set_text(target.capitalize())
        self.char_data_panel.set_character(target)
        self.cooldown_panel.turn_off()
    
    def set_aff(self, affliction, status):
        self.aff_panel.set(affliction, status)
        
    def update_cooldowns(self):
        self.cooldown_panel.update()
        
    def reset_cooldown(self, cd):
        self.cooldown_panel.reset_one(cd)

class SelfPanel(BlackEventBox):
    def __init__(self, client):
        BlackEventBox.__init__(self)
        f=BlackFrame('Self')
        
        box = gtk.VBox()
        f.add(box)
        self.hp_mana = HpManaPanel('Self', client)
        box.pack_start(self.hp_mana, expand=False)
        self.bleed = BleedPanel(client)
        box.pack_start(self.bleed, expand=False)
        self.add(f)
        
class ImperianGui(BlackEventBox):
    def __init__(self, realm):
        self.realm = realm
        #self.realm.registerEventHandler('setTargetEvent', self.set_target)
        #self.realm.registerEventHandler('statUpdateEvent', self.update_stats)
        #self.realm.registerEventHandler('targetInRoomEvent', self.set_target_is_here)
        #self.realm.registerEventHandler('targetLeftRoomEvent', self.set_target_is_not_here)
        
        self.realm.registerEventHandler('setTargetEvent', self.set_target)
        BlackEventBox.__init__(self)
        box=gtk.VBox()
        self.enemy=EnemyPanel(realm)
        self.self_panel=SelfPanel(realm)
        box.pack_start(self.self_panel, expand=True)
        box.pack_start(self.enemy, expand=True)
        self.add(box)
        
    
    def update_stats(self, stat, value):
        if stat == 'hp':
            self.self_panel.hp_mana.set_curr_hp(value)
        if stat == 'mp':
            self.self_panel.hp_mana.set_curr_mana(value)
        if stat == 'maxhp':
            self.self_panel.hp_mana.set_max_hp(value)
        if stat == 'maxmp':
            self.self_panel.hp_mana.set_max_mana(value)
        if stat == 'bleeding':
            self.self_panel.bleed.set_current(value)
            
    def set_target(self, target):
        self.enemy.set_target(target)
    
    def set_aff(self, affliction, status):
        self.enemy.set_aff(affliction, status)
        
    def update_cooldowns(self):
        self.enemy.update_cooldowns()

    def reset_cooldown(self, cd):
        self.enemy.reset_cooldown(cd)
    
    def set_target_here(self, is_here):
        self.enemy.set_target_here(is_here)
        
    def set_shield(self, shield, state):
        self.enemy.set_shield(shield, state)
    
    def set_target_is_here(self, player):
        self.enemy.set_target_here(True)
        
    def set_target_is_not_here(self, player):
        self.enemy.set_target_here(False)
    def all_shields_off(self):
        self.enemy.all_shields_off()