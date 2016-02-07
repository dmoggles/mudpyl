"""A GUI for pymudclient written in PyGTK."""
from pymudclient.gui.gtkoutput import OutputView, ScrollingDisplayView
from pymudclient.gui.gtkcommandline import CommandView
from twisted.internet.task import LoopingCall
from pymudclient.gui.keychords import from_string
from datetime import datetime, timedelta
import traceback
import gtk
from Tkinter import Tk
from pymudclient.gui.gtkguiwidgets import UpdatingWidgetView
from gtk._gtk import SHRINK
from pymudclient.library.imperian.imperian_gui import EnemyPanel
from pymudclient.gui.gui_elements import BlackFrame, BlackEventBox,\
    BetterToggleButton
from pymudclient.colours import GREEN
from pymudclient.gui import gui_elements

class TimeOnlineLabel(gtk.Label):

    """A display of how long the current session has been online for."""

    def __init__(self):
        gtk.Label.__init__(self)
        self.looping_call = LoopingCall(self.update_time)
        self.start_time = None

    def start_counting(self):
        """Start ticking."""
        self.start_time = datetime.now()
        #don't leave our display blank
        self.update_time()
        self.looping_call.start(0.5) #update it twice per second

    def stop_counting(self):
        """We only count time online; stop counting."""
        self.looping_call.stop()

    def update_time(self):
        """Should tick once a second. Displays the current running count of
        how long's been spent online.
        """
        delta = datetime.now() - self.start_time
        #chop off microseconds, for neatness
        delta = timedelta(delta.days, delta.seconds)
        self.set_text('Time online: %s' % delta)

class updater:
    def __init__(self, gui):
        self.gui=gui
        self.looping_call = LoopingCall(self.update_gui_elements)
        self.looping_call.start(0.1)
    
    def update_gui_elements(self):
        for k in self.gui.updatable_elements:
            if k in self.gui.realm.state:
                value=self.gui.realm.state[k]
            else:
                value=''
            format_text,element=self.gui.updatable_elements[k]
            element.set_text(format_text%value)
            
                
class GUI(gtk.Window):

    """The toplevel window. Contains the command line and the output view."""

    def __init__(self, realm, mode):
        self.mode = mode
        gtk.Window.__init__(self)
        self.realm = realm
        self.realm.addProtocol(self)
        realm.gui = self
        self.output_container = gtk.VBox()
        self.command_line = CommandView(self)
        self.output_window = OutputView(self, self.output_container)
        self.scrolled_out = gtk.ScrolledWindow()
        self.scrolled_in = gtk.ScrolledWindow()
        self.scrolled_comm = gtk.ScrolledWindow()
        self.paused_label = gtk.Label()
        self.time_online = TimeOnlineLabel()
        self.clipboard = gtk.Clipboard(selection='PRIMARY')
        self.target=gtk.Label()
        self.map = UpdatingWidgetView(self)
        self.room_players = UpdatingWidgetView(self)
        self.class_widget = UpdatingWidgetView(self)
        self.self_aff_widget = UpdatingWidgetView(self)
        self.comm_widget = ScrollingDisplayView(self)
        self.map_buffer=[]
        self.updatable_elements={'target':('Target: %s',self.target)}
        
        self.updater = updater(self)
        self._make_widget_body()
        
        
        

    def connectionMade(self):
        self.time_online.start_counting()

    def connectionLost(self):
        self.time_online.stop_counting()

    def close(self):
        #GTK does all the destruction for us.
        pass

    def metalineReceived(self, metaline):
        channels = metaline.channels
        if not 'map' in channels and len(self.map_buffer)>0:
            self.map.writeLines(self.map_buffer)
            self.map_buffer=[]
        if len(channels)==0 or 'main' in channels:
            plain_line = metaline.line.replace('\n', '')
            self.command_line.add_line_to_tabdict(plain_line)
            self.output_window.show_metaline(metaline)
        if 'map' in channels:
            self.map_buffer.append(metaline)
        if 'players' in channels:
            self.room_players.writeLines([metaline])
        if 'class' in channels:
            self.class_widget.writeLines([metaline])
        if 'comm' in channels:
            self.comm_widget.show_metaline(metaline)
        if 'afflictions' in channels:
            self.self_aff_widget.writeLines([metaline])

    def _make_widget_body(self):
        """Put it all together."""
        self.set_title("%s - pymudclient" % self.realm.mod.name)
        self.connect('destroy', self.destroy_cb)
        self.maximize() #sic
        outputbox = gtk.Table(columns=6,rows=1,homogeneous=True)
        outputbox.set_col_spacings(3)
        #never have hscrollbars normally, always have vscrollbars
        self.scrolled_out.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.scrolled_out.add(self.output_window)

        self.scrolled_in.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        self.scrolled_in.add_with_viewport(self.command_line)

        #construct the bottom row of indicators and stuff
        labelbox = gtk.HBox()
        #we want the paused indicator to be to the left, because it comes 
        #and goes.
        if self.mode == 'enhanced':
            bbox = gtk.HButtonBox()
            bbox.set_spacing(5)
            split_button = BetterToggleButton(label='Split', depressed_label='Unsplit',
                                              color = gui_elements.GREEN, method=self.output_window.toggle_pause, gui=self, xsize = 50)
            system_on = BetterToggleButton(label='Processing', depressed_label='Processing',
                                              color = gui_elements.GREEN, method=self.realm.set_bypass, gui=self, xsize = 50)
            
            bbox.pack_end(split_button)
            bbox.pack_end(system_on)
            labelbox.pack_end(bbox, expand=False)
            labelbox.pack_end(gtk.VSeparator(), expand = False)
        labelbox.pack_end(self.time_online, expand = False)
        labelbox.pack_end(gtk.VSeparator(), expand = False)
        labelbox.pack_end(self.paused_label, expand = False)
        labelbox.pack_start(self.target, expand=False)
        
        widgetbox = gtk.Table(columns=1,rows=2, homogeneous=True)
        widgetbox1 = gtk.HBox()
        widgetbox1.pack_start(self.map)
        map_frame = BlackFrame('Map')
        map_frame.add(widgetbox1)
        map_box = BlackEventBox()
        map_box.add(map_frame)
        #widgetbox1.pack_start(gtk.VSeparator(),expand=False)
    
        #widgetbox.pack_start(widgethbox1, expand=True)
        #widgetbox.pack_start(gtk.HSeparator(), expand=False)
        widgetbox.attach(map_box, 0,1,0,1)
        #widgetbox.attach(gtk.HSeparator(),0,1,1,2, yoptions=gtk.SHRINK)
        self.scrolled_comm.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.scrolled_comm.add(self.comm_widget)
        #widgetbox.pack_start(self.scrolled_comm, expand=True)
        #widgetbox.pack_start(gtk.HSeparator(), expand=False)
        comm_frame = BlackFrame('Comms')
        
        comm_frame.add(self.scrolled_comm)
        comm_box = BlackEventBox()
        comm_box.add(comm_frame)
        widgetbox.attach(comm_box, 0,1,1,2)
        box = gtk.VBox()
        #outputbox.pack_start(self.scrolled_out, expand=True)
        #outputbox.pack_start(gtk.VSeparator(), expand=False)
        #outputbox.pack_start(widgetbox, expand=True)
        
        left_box = gtk.VBox()
        left_box.pack_start(self.realm.extra_gui)
        self.output_container.pack_start(self.scrolled_out, expand=True)
        outputbox.attach(left_box, left_attach=0, right_attach=1, top_attach=0, bottom_attach=1)
        outputbox.attach(self.output_container, left_attach=1, right_attach=4, top_attach=0, bottom_attach=1)
        outputbox.attach(widgetbox, left_attach=4, right_attach=6, top_attach=0, bottom_attach=1)
       
        
        box.pack_start(outputbox)
        box.pack_start(gtk.HSeparator(), expand = False)
        box.pack_start(self.room_players, expand=False)
        box.pack_start(gtk.HSeparator(), expand=False)
        box.pack_start(self.class_widget, expand=False)
        box.pack_start(gtk.HSeparator(), expand=False)
        box.pack_start(self.self_aff_widget, expand=False)
        box.pack_start(gtk.HSeparator(), expand=False)
        box.pack_start(self.scrolled_in, expand = False)
        box.pack_start(labelbox, expand = False)
        self.add(box)
        self.widgets={'map':self.map}

        self.show_all()

    def destroy_cb(self, widget, data = None):
        """Close everything down."""
        try:
            self.realm.close()
        except Exception:
            #swallow-log traceback here, because exiting gracefully is fairly
            #important. The traceback is written to stdout (or is it stderr?
            #one of the two, anyway), so we just plug on into the finally
            #clause.
            traceback.print_exc()
        finally:
            #if the reactor's been started, this will run straight away, else
            #it'll make the reactor die as soon as we do start. oh, and, we
            #can't import out there, because we may not have installed the
            #right reactor yet.
            from twisted.internet import reactor
            #and, of course, because of Twisted's namespace hackery, pylint
            #gets confused.
            #pylint: disable-msg= E1101
            reactor.callWhenRunning(reactor.stop)
            #pylint: enable-msg= E1101
            return True

    def forward_page_up_cb(self, realm):
        """Forward a page up key to the output window from the command line.

        As the command line is only one line, these don't make sense anyway.
        """
        self.output_window.pause()
        self.scrolled_out.emit("scroll-child", gtk.SCROLL_PAGE_BACKWARD,
                               False)

    def forward_page_down_cb(self, realm):
        """Forward a page down key from the command line to the output window.
        """
        self.scrolled_out.emit("scroll-child", gtk.SCROLL_PAGE_FORWARD,
                               False)

    def maybe_forward_copy_cb(self, realm):
        """If there is no selection in the command line, forward the copy
        command to the output window.

        This is needed so that focus can always stay on the command line.
        
        --dm 
        
        I had to rework this as the text wasn't hitting the system clipboard
        """
        print("Attempted to Copy")
        if self.command_line.get_selection_bounds():
            #let the command window handle if it's got the selection
            start_char, end_char = self.command_line.get_selection_bounds()
            copy_text = self.command_line.get_all_text()[start_char:end_char]
            copy_helper(copy_text)
        else:
            copy_text = self.clipboard.wait_for_text()
            print("COPY:------------------------------------------\n%s"%copy_text)
            print("\n-----------------------------------------------------")
            if copy_text != None:
                copy_helper(copy_text)


def copy_helper(text):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.destroy()

def configure(realm, mode = 'simple'):
    """Set the right reactor up and get the GUI going."""
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    gui = GUI(realm, mode)
    macros = {from_string("<page up>"): gui.forward_page_up_cb,
              from_string('<page down>'): gui.forward_page_down_cb,
              from_string("C-c"): gui.maybe_forward_copy_cb}
    realm.macros.update(macros)
    realm.baked_in_macros.update(macros)
