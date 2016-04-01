"""Implementes triggers, which run code if the MUD's text matches certain
criteria.
"""
from collections import deque
from pymudclient.matchers import BindingPlaceholder, NonbindingPlaceholder, \
                            make_decorator, ProtoMatcher, BaseMatchingRealm
from pymudclient.metaline import iadjust
from pymudclient.aliases import AliasMatchingRealm
import re
from pymudclient.tagged_ml_parser import taggedml
import time

class RegexTrigger(ProtoMatcher):
    """A single trigger, that matches simply on a regex."""

    def match(self, metaline):
        """Test to see if the trigger's regex matches."""
        if self.regex is not None:
            if isinstance(self.regex, list):
                for r in self.regex:
                    if re.match(r, metaline.line):
                        return re.finditer(r, metaline.line)
                
                return []
            else:
                return re.finditer(self.regex, metaline.line)
        else:
            return []

binding_trigger = make_decorator(RegexTrigger, BindingPlaceholder,True)
non_binding_trigger = make_decorator(RegexTrigger, NonbindingPlaceholder,True)

class LineAlterer(object):
    """Caches the changes made to a Metaline so triggers don't step on each
    others' feet.
    """

    def __init__(self):
        self._changes = deque()

    def delete(self, start, end):
        """Delete a span of text."""
        self._changes.append(('delete', start, end))

    def insert(self, start, text):
        """Insert text."""
        self._changes.append(('insert', start, text))

    def change_fore(self, start, end, colour):
        """Change a span's foreground."""
        self._changes.append(('change_fore', start, end, colour))

    def insert_metaline(self, start, metaline):
        """Insert a coloured metaline."""
        self._changes.append(("insert_metaline", start, metaline))

    def change_back(self, start, end, colour):
        """Change a span's background."""
        self._changes.append(('change_back', start, end, colour))

    def _alter(self, start, adj):
        """Change the indices to account for deletions and insertions."""
        for ind, change in enumerate(self._changes):
            if change[0] == 'delete':
                meth, mstart, mend = change
                self._changes[ind] = (meth, iadjust(mstart, start, adj), 
                                      iadjust(mend, start, adj))
            elif change[0] in ('insert', 'insert_metaline'):
                meth, mstart, text = change
                self._changes[ind] = (meth, iadjust(mstart, start, adj), text)
            elif change[0] in ('change_fore', 'change_back'):
                meth, mstart, mend, colour = change
                self._changes[ind] = (meth, iadjust(mstart, start, adj), 
                                      iadjust(mend, start, adj), colour)

    def apply(self, metaline):
        """Apply our changes to a metaline.

        This LineAlterer is no good after doing this, so copy it if it needs
        to be reused. The metaline passed in, however, is left pristine.
        """
        if self._changes:
            metaline = metaline.copy()
        for change in self._changes:
            meth = change[0]
            args = change[1:]
            if meth == 'delete':
                start, end = args
                #we want the adjustment to be negative
                self._alter(start, start - end)
            elif meth == 'insert':
                start, text = args
                self._alter(start, len(text))
            elif meth == "insert_metaline":
                start, ins_metaline = args
                self._alter(start, len(ins_metaline.line))
            getattr(metaline, meth)(*args)
        return metaline


class TriggerBlockMatchingRealm(BaseMatchingRealm):
    """This is like trigger matching realm, but it operates on an entire block"""
    def __init__(self, block, root, parent, display_group=True):
        BaseMatchingRealm.__init__(self, root, parent)
        self.block=block
        self.alterers=[LineAlterer() for i in xrange(len(self.block))]
        self.display_lines = [display_group]*len(self.block)
        self.display_group = True
        
        self.line_index=0
        
    @property
    def metaline(self):
        return self.block[self.line_index]
    @metaline.setter
    def metaline(self, value):
        self.block[self.line_index]=value
        
    @property
    def alterer(self):
        return self.alterers[self.line_index]
    @alterer.setter
    def alterer(self, value):
        self.alterers[self.line_index]=value
        
    @property
    def display_line(self):
        return self.display_lines[self.line_index]
    @display_line.setter
    def display_line(self, value):
        self.display_lines[self.line_index]=value
      
      
    def process(self):
        """Do our main thing."""
        channels=[]
        f = open(r'c:\temp\debug_pymudclient.txt','w')
        f.write("# of triggers: %d\n"%len(self.root.triggers))
        f.write("# of lines: %d\n"%len(self.block))
        t0 = time.clock()
        for ml in self.block:
            self._match_generic(ml, self.root.triggers,f)
            '''triggers can set a different channel to write the text to, and we need to respect that'''
            channels.append(self.root.active_channels)
            self.line_index+=1
        t1 = time.clock()
        f.write('Total Process: '+str(t1-t0)+'\n')    
        #for module in self.root.modules:
        #    module.on_prompt(self)
        for indx, alterer in enumerate(self.alterers):
            metaline = alterer.apply(self.block[indx])
            '''Apply the channels that were set when actually writing'''
            self.root.setActiveChannels(channels[indx])
            if self.display_lines[indx] and self.display_group:
                self.parent.write(metaline)
            self._write_after(indx)
        t2 = time.clock()
        f.write('Total Post Process: '+str(t2-t1)+'\n')
        f.close()  
        
    def _write_after(self, indx):
        """Write everything we've been waiting to."""
        writing_after_indx=[(line, sls) for (line, i, sls) in self._writing_after if i == indx]
        for noteline, sls in writing_after_indx:
            self.parent.write(noteline, sls)
    

    def write(self, line, soft_line_start = False):
        """Write a line to the screen.

        This buffers until the original line has been displayed or echoed.
        """
        self._writing_after.append((line, self.line_index, soft_line_start))
        
    def send(self, line, echo = False):
        """Send a line to the MUD."""
        #need to spin a new realm out here to make sure that the writings from
        #the alias go after ours.
        realm = AliasMatchingRealm(line, echo, parent = self, root = self.root)
        realm.process()
        
        
class TriggerMatchingRealm(BaseMatchingRealm):
    """A realm representing the matching of triggers.
    
    This has several things that triggers can twiddle:
     
    .alterer - a LineAlterer instance that triggers must use if they want to
    fiddle with the metaline.
    
    .display_line, which indicates whether the line should be displayed on
    screen or not.
    
    There are also several attributes which should not be altered by triggers,
    but which may be read or something:
    
    .metaline, which is the Metaline that the trigger matched against.
    
    .root, which is the RootRealm.
    
    .parent, which is the Realm up one level from this one.
    """

    def __init__(self, metaline, root, parent, display_line):
        BaseMatchingRealm.__init__(self, root, parent)
        self.metaline = metaline
        self.alterer = LineAlterer()
        self.display_line = display_line
        self.display_group = True
        self.block=[metaline]
        self.line_index=0
    def process(self):
        """Do our main thing."""
        self._match_generic(self.metaline, self.root.triggers)
        metaline = self.alterer.apply(self.metaline)
        if self.display_line:
            self.parent.write(metaline)
        self._write_after()

    def send(self, line, echo = False):
        """Send a line to the MUD."""
        #need to spin a new realm out here to make sure that the writings from
        #the alias go after ours.
        realm = AliasMatchingRealm(line, echo, parent = self, root = self.root)
        realm.process()
