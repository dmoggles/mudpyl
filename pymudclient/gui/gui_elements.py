import gtk
import pango

TEAL='#42CADA'
DARK_TEAL='#427DDA'
BG_GRAY='#B6B6B6'
BG_DARK_GRAY='#111111'
OFF_WHITE='#DDDDDD'
BG_BLACK='#000000'
PURPLE='#D400FF'
PINK='#FB6FC4'
DARK_RED='#550000'
RED='#AA0000'
GREEN='#00AA00'
YELLOW='#EDF00D'
ORANGE='#FF7C10'



class BetterToggleButton(gtk.Button):
    def __init__(self, label, depressed_label, method,  gui, color = BG_GRAY, depressed_color = RED, xsize=None):
        gtk.Button.__init__(self, label)
        self.normal_label = label
        self.gui = gui
        self.pressed_label = depressed_label
        self.normal_color = color
        self.pressed_color = depressed_color
        self.set_color(color)
        self.pressed_state=0
        self.connect('clicked', self.do_clicked)
        self.method = method
        self.connect('focus-in-event', self.got_focus_cb)
        if not xsize == None:
            size = self.get_size_request()
            self.set_size_request(xsize, size[1])
        
    
    def got_focus_cb(self, *args, **kwargs):
        self.gui.command_line.grab_focus()
        
    def set_color(self, color):
        style = self.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = gtk.gdk.Color(color)
        style.bg[gtk.STATE_PRELIGHT] = gtk.gdk.Color(color)
        self.set_style(style)
        
    def do_clicked(self, *args, **kwargs):
        
        if self.pressed_state==1:
            self.pressed_state = 0;
            self.set_color(self.normal_color)
            self.set_label(self.normal_label)
        else:
            self.pressed_state=1
            self.set_color(self.pressed_color)
            self.set_label(self.pressed_label)
        
        self.method(self.pressed_state)
        
        
        
        


class BlackEventBox(gtk.EventBox):
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BG_BLACK))
        
class BlackFrame(gtk.Frame):
    def __init__(self, name):
        gtk.Frame.__init__(self,name)
        self.get_label_widget().modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(OFF_WHITE))
        self.get_label_widget().modify_font(pango.FontDescription('monospace 8'))
        
class FormattedLabel(gtk.Label):
    def __init__(self, name):
        gtk.Label.__init__(self,name)
        self.modify_font(pango.FontDescription('monospace 8'))
        self.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(OFF_WHITE))        


class HpManaWidget(BlackEventBox):
    def __init__(self, name, event_name, client):
        BlackEventBox.__init__(self)
        self.type=name.lower()
        t = gtk.Table(rows=1, columns = 5, homogeneous=True)
        l = FormattedLabel(name)
        t.attach(l, left_attach=0, right_attach=1, top_attach=0, bottom_attach=1)
        self.current=100
        self.max = 100
        self.pb = gtk.ProgressBar()
        t.attach(self.pb, left_attach=1, right_attach=5, top_attach=0, bottom_attach=1)
        self.update()
        self.add(t)
        client.registerEventHandler(event_name, self.handle_event)
        
        
    def update(self):
        self.pb.set_text('%d/%d'%(self.current, self.max))
        self.pb.set_fraction(min(float(self.current)/float(self.max),1.0))
        #self.pb.update(percentage=min(float(self.current)/float(self.max),1.0))
    
    def set_max(self, value):
        self.max=value
        self.update()
        
    def set_current(self, value):
        self.current=value
        self.update()
        
    def handle_event(self, stat, value):
        if stat == self.type:
            self.set_current(int(value))
        elif stat == '%s_max'%self.type:
            self.set_max(int(value))

class HpManaPanel(BlackEventBox):
    def __init__(self, panel_name, client):
        BlackEventBox.__init__(self)
        f = BlackFrame('%s Hp/Mana'%panel_name)
        vbox=gtk.VBox()
        event_name = '%sStatUpdateEvent'%panel_name.lower()
        self.hp = HpManaWidget('HP',event_name, client)
        self.mana = HpManaWidget('Mana',event_name, client)
        vbox.pack_start(self.hp, expand=True)
        vbox.pack_start(self.mana, expand=True)
        f.add(vbox)
        self.add(f)
        
    def set_curr_hp(self, value):
        self.hp.set_current(value)
    
    def set_max_hp(self, value):
        self.hp.set_max(value)
        
    def set_curr_mana(self, value):
        self.mana.set_current(value)
        
    def set_max_mana(self, value):
        self.mana.set_max(value)


           
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
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(RED))
            self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(OFF_WHITE))
        else:
            self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BG_BLACK))
            if value == 0:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(OFF_WHITE))
            elif value < 0.25*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(GREEN))
            elif value < 0.5*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(YELLOW))
            elif value < 0.75*self.max_value:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ORANGE))
            else:
                self.l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(RED))
                
                
class CountdownBar(BlackEventBox):
    def __init__(self,  max_seconds):
        BlackEventBox.__init__(self)
        self.pb=gtk.ProgressBar()
        self.pb.set_fraction(0.0)
        self.pb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(BG_BLACK))
        self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(RED))
        self.max_seconds=max_seconds
        self.add(self.pb)
        
    def set_value(self, seconds):
        if seconds <= self.max_seconds:
            value = float(seconds)/float(self.max_seconds)
            if value == 0:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(OFF_WHITE))
            elif value < 0.25:
                pass
                #self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ge.GREEN))
            elif value < 0.5:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(YELLOW))
            elif value < 0.75:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(ORANGE))
            else:
                self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(RED))
        else:
            value = 1.0
            self.pb.set_fraction(1.0)
            self.pb.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.Color(RED))
        print(value)
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
        
        
class AffLabel(BlackEventBox):
    def __init__(self,name,short_name,light, client, permanent_target = None):
        BlackEventBox.__init__(self)
        self.label = gtk.Label(short_name)
        self.label.modify_font(pango.FontDescription('monospace 8'))
        self.label.set_alignment(0.0,0.0)
        self.add(self.label)
        self.light=light
        self.target = permanent_target
        self.permanent_target=permanent_target
        if light:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.PINK))
        else:
            self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.PURPLE))
            
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.BG_BLACK))
        self.status=False
        client.registerEventHandler('afflictionGainedEvent', self.on_affliction_gained)
        client.registerEventHandler('afflictionLostEvent',self.on_affliction_lost)
        client.registerEventHandler('setTargetEvent', self.on_target_set)
    
    def on_affliction_gained(self, target, afflictions):
        aff_list = afflictions.split(',')
        if self.target == target and self.name in aff_list:
            self.set(True)
            
    def on_affliction_lost(self, target, afflictions):
        aff_list = afflictions.split(',')
        if self.target == target and self.name in aff_list:
            self.set(False)
    
    def on_target_set(self, target):
        if self.permanent_target == None:
            self.target = target
            self.on_affliction_reset(target)
            
                
    def set(self, status):
        self.status = status
        if self.status == False:
            self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(ge.BG_BLACK))
        else:
            if self.light:
                self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(ge.DARK_RED))
            else:
                self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(ge.RED))
