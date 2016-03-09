'''
Created on Feb 24, 2016

@author: Dmitry
'''


from Tkinter import Frame, Tk, Entry, Event
from ttk import Style
from ScrolledText import ScrolledText
from Tkconstants import LEFT, BOTH, DISABLED, RAISED,X, BOTTOM, NONE, TOP


class EntryBox(Entry):
    def __init__(self, master=None, attach=BOTTOM):
        Entry.__init__(self, master, bg='Grey', relief=RAISED, borderwidth=2)
        self.bind('<KeyPress>',self.callback_press)
        self.bind('<KeyRelease>',self.callback_release)
        self.pack(side=attach,fill=X, expand=1)
        self.modifiers=set()
    
    def to_simple_string(self, key):
        if key=='Control_L' or key=='Control_R':
            return 'CTRL'
        if key=='Alt_L' or key=='Alt_R':
            return 'ALT'
        return key
        
    def callback_press(self, event):
        sym = self.to_simple_string(event.keysym)
        if sym == 'CTRL' or sym=='ALT':
            self.modifiers.add(sym)
        else:
            if len(self.modifiers)==0:
                print sym
            else:
                mods_s='-'.join(self.modifiers)
                print'%s-%s'%(mods_s, sym)
                
    def callback_release(self, event):
        sym = self.to_simple_string(event.keysym)
        if sym in self.modifiers:
            self.modifiers.remove(sym)
            
        
        
class ScrollingText(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, bg='Black', relief=RAISED, borderwidth=2)
        self.parent=master
        self.style=Style()
        self.style.theme_use('default')
        
        self.text = ScrolledText(self,   bg='Black')
        self.text.pack(side=LEFT, fill=BOTH, expand=1)
        self.text.config(state=DISABLED)
        self.pack(fill=BOTH, expand=1)
        
        
    
        
        
        
        
root = Tk()
w,h=root.winfo_screenwidth(),root.winfo_screenheight()
root.geometry('%(width)dx%(height)d+0+0'%{'width':w, 'height':h})
st = ScrollingText(root)
en = EntryBox(root, attach=TOP)


root.mainloop()