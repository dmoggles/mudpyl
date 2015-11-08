'''
Created on Jul 25, 2015

@author: dmitry
'''

import gtk
import pango
from pymudclient.gui.gtkoutput import DisplayView


class UpdatingWidgetView(DisplayView):
    def __init__(self, gui):
        DisplayView.__init__(self, gui)
    
    def writeLines(self, lines):
        '''clear the screen and write new lines to it'''
        self.buffer.set_text("")
        for metaline in lines:
            self.show_metaline(metaline)