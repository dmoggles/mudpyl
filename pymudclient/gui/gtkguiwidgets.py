'''
Created on Jul 25, 2015

@author: dmitry
'''

import gtk
import pango


class MapView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)
        self.buffer = self.get_buffer()
        
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0)) #sic
        self.modify_font(pango.FontDescription('monospace 8'))
        self._tags = {}
    
    def writeLines(self, lines):
        '''clear the screen and write new lines to it'''
        self.buffer.set_text("")
        for metaline in lines:
            bytes = metaline.line.encode('utf-8')
            end_iter = self.buffer.get_end_iter()
            offset = end_iter.get_offset()
            self.buffer.insert(end_iter, bytes)
            self.apply_colours(metaline.fores, offset, len(metaline.line))
            self.apply_colours(metaline.backs, offset, len(metaline.line))
            
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