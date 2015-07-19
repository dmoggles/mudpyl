'''
Created on Jul 18, 2015

@author: Dmitry
'''
from pymudclient.matchers import make_decorator, NonbindingPlaceholder
from pymudclient.matchers import BindingPlaceholder
import traceback


class GmcpEvent:
    
    def __init__(self, tag = None, func = None, sequence = 0):
        if func is not None or not hasattr(self, 'func'):
            self.func = func
        if tag is not None or not hasattr(self, 'regex'):
            self.tag = tag
        self.sequence = sequence
        
        
    def match(self,gmcp_pair):
        gmcp_type,_=gmcp_pair
        return self.tag==gmcp_type
    
    def func(self, gmcp_data, realm):
        """Default, do-nothing function."""
        pass
     
    def __call__(self, gmcp_pair, realm):
        realm.trace_thunk(lambda: "%s matched!" % self)
        try:
            gmcp_type,gmcp_data=gmcp_pair
            if gmcp_type==self.tag:
                self.func(gmcp_data, realm)
        except Exception: #don't catch KeyboardInterrupt etc
            traceback.print_exc()

    

    def __str__(self):
        args = [type(self).__name__]
        #make it do the right thing for both strings and compiled patterns.
        if isinstance(self.tag, basestring):
            args.append(self.tag)
        else:
            args.append('(inactive)')
        #scrape our function's name, if it's interesting
        if self.func is not None and self.func.func_name != 'func':
            args.append(self.func.func_name)
        args.append('sequence = %d' % self.sequence)
        return '<%s>' % ' '.join(args)   

binding_gmcp_event = make_decorator(GmcpEvent, BindingPlaceholder,False)
non_binding_gmcp_event = make_decorator(GmcpEvent, NonbindingPlaceholder, False)

