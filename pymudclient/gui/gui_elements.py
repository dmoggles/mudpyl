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

