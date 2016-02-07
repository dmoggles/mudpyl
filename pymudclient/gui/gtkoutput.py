"""Contains the widget that displays the text from the MUD."""
from itertools import izip, chain
import gtk
import pango
from pymudclient.metaline import RunLengthList
from datetime import datetime
    
def do_print(ele, tag_table):
    tag_table.add(ele)

class DisplayView(gtk.TextView):
    def __init__(self, gui):
        gtk.TextView.__init__(self)
        self.gui = gui
        self.buffer = self.get_buffer()
        
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0)) #sic
        self.modify_font(pango.FontDescription('monospace 8'))
        self.connect('focus-in-event', self.got_focus_cb)
        self._tags = {}
        
    def got_focus_cb(self, widget, event):
        """We never want focus; the command line automatically lets us have
        all incoming keypresses that we're interested in.
        """
        self.gui.command_line.grab_focus()
        
    def apply_colours(self, colours, offset, end_offset):
        """Apply a RunLengthList of colours to the buffer, starting at
        offset characters in.
        """
        end_iter = self.buffer.get_iter_at_offset(offset)
        for tag, end in zip(map(self.fetch_tag, colours.values()),
                                colours.keys()[1:] + [end_offset]):
            start_iter = end_iter
            end_iter = self.buffer.get_iter_at_offset(end + offset)
            self.buffer.apply_tag(tag, start_iter, end_iter)
            
    def fetch_tag(self, colour):
        """Check to see if a colour is in the tag table. If it isn't, add it.

        Returns the tag.
        """
        #use our own tag table, because GTK's is too slow
        if colour in self._tags:
            tag = self._tags[colour]
        else:
            tag = self.buffer.create_tag(None)
            tag.set_property(colour.ground + 'ground', '#' + colour.as_hex)
            tag.set_property(colour.ground + 'ground-set', True)
            self._tags[colour] = tag
        return tag
    
    def show_metaline(self, metaline):
        """Write a span of text to the window using the colours defined in
        the other channels.

        This will autoscroll to the end if we are not paused.
        """
        bytes = metaline.line.encode('utf-8')
        end_iter = self.buffer.get_end_iter()
        offset = end_iter.get_offset()
        self.buffer.insert(end_iter, bytes)
        self.apply_colours(metaline.fores, offset, len(metaline.line))
        self.apply_colours(metaline.backs, offset, len(metaline.line))
        return offset
        
class ScrollingDisplayView(DisplayView):
    def __init__(self, gui):
        DisplayView.__init__(self, gui)
        self.end_mark = self.buffer.create_mark('end_mark', 
                                                self.buffer.get_end_iter(), 
                                                False)
    def show_metaline(self, metaline):
        offset= DisplayView.show_metaline(self, metaline)
        self.scroll_mark_onscreen(self.end_mark)
        return offset
    
class DuplicateScrollingDisplayView(DisplayView):
    def __init__(self, gui, buf):
        DisplayView.__init__(self, gui)
        self.set_buffer(buf)
        self.end_mark = self.buffer.get_mark('end_mark')
        
    def show_metaline(self, metaline):
        #offset= DisplayView.show_metaline(self, metaline)
        self.scroll_mark_onscreen(self.end_mark)
        return DisplayView.offset
          
class OutputView(DisplayView):

    """The display for all the text received from the MUD."""

    def __init__(self, gui, container):
        DisplayView.__init__(self, gui)
        #the identity of the return value of get_buffer() doesn't seem to be
        #stable. before, we used a property, but now we just get it once and
        #leave it at that because GTK complains about the non-identicality
        #of them.
        #self.gui = gui
        self.paused = False
        self.end_mark = self.buffer.create_mark('end_mark', 
                                                self.buffer.get_end_iter(), 
                                                False)
        self.timestamps = RunLengthList({})
        self.connect('focus-in-event', self.got_focus_cb)
        self.set_property("has-tooltip", True)
        self.connect("query-tooltip", self.display_tooltip_cb)
        self.container = container
        self.paused_scrolling_view = None
        self.paused_separator = gtk.HSeparator()
        self.scrolled_paused=gtk.ScrolledWindow()
        
    

    def display_tooltip_cb(self, widget, wx, wy, keyboard_mode, tooltip):
        """Display a timestamp for the line the user hovers over."""
        #XXX: I'm not sure this is converting between coordinates right, I
        #need to double-check the GTK docs.
        bx, by = self.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, wx, wy)
        textiter = self.get_iter_at_location(bx, by)
        #GTK is very keen for the above code to succeed, but really it's only
        #useful for us if there's a tooltip above a bit of text, as opposed
        #to the ENTIRE FREAKING WIDGET. So test to see if bx and by can
        #roundtrip in the character's pixel rectangle
        rect = self.get_iter_location(textiter)
        if not 0 <= bx - rect.x <= rect.width or \
           not 0 <= by - rect.y <= rect.height:
            return False
        received_at = self.timestamps.get_at(textiter.get_offset())
        tooltip.set_text(received_at.strftime("Received at: %H:%M:%S"))
        return True


    def toggle_pause(self, state):
        if state==1:
            self.pause()
        else:
            self.unpause()
        
    def pause(self):
        """Stop autoscrolling to new data."""
        if not self.paused:
            self.paused = True
            self.gui.paused_label.set_markup("PAUSED")
            self.scroll_mark_onscreen(self.end_mark)
            self.scrolled_paused.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
            #self.paused_scrolling_view = ScrollingDisplayView(self.gui)
            self.paused_scrolling_view = DuplicateScrollingDisplayView(self.gui, self.buffer)
            self.scrolled_paused.add(self.paused_scrolling_view)
            
            self.container.pack_start(self.paused_separator, expand=False)
            self.container.pack_start(self.scrolled_paused, expand=True)
            self.scrolled_paused.show()
            self.paused_separator.show()
            self.paused_scrolling_view.scroll_mark_onscreen(self.end_mark)
            self.paused_scrolling_view.show()
            
            

    def unpause(self):
        """Restart autoscrolling to new data.
        
        This does not automatically scroll to the buffer's end.
        """
        if self.paused:
            self.paused = False
            self.gui.paused_label.set_markup("")
            self.container.remove(self.paused_separator)
            self.container.remove(self.paused_scrolling_view)
            self.container.remove(self.scrolled_paused)
            self.paused_scrolling_view.destroy()
            self.paused_scrolling_view=None
        #scroll to the end of output
        self.scroll_mark_onscreen(self.end_mark)

    def show_metaline(self, metaline):
        """Write a span of text to the window using the colours defined in
        the other channels.

        This will autoscroll to the end if we are not paused.
        """
        #bytes = metaline.line.encode('utf-8')
        #end_iter = self.buffer.get_end_iter()
        #offset = end_iter.get_offset()
        #self.buffer.insert(end_iter, bytes)
        #self.apply_colours(metaline.fores, offset, len(metaline.line))
        #self.apply_colours(metaline.backs, offset, len(metaline.line))
        offset=DisplayView.show_metaline(self, metaline)
        if not self.paused:
            self.scroll_mark_onscreen(self.end_mark)
        else:
            self.gui.paused_label.set_markup("<span foreground='#FFFFFF' "
                                                   "background='#000000'>"
                                               "MORE - PAUSED</span>")
            #self.paused_scrolling_view.show_metaline(metaline)
            self.paused_scrolling_view.scroll_mark_onscreen(self.end_mark)
        #this is a bit naughty, we're bypassing the RLL's safety thingies
        #anyway, we need to store the offset that -begins- the chunk of text
        self.timestamps[offset] = datetime.now()

    

