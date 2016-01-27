'''
Created on Jul 24, 2015

@author: dmitry
'''
import re
import colours
from pymudclient.metaline import RunLengthList, Metaline
from pymudclient.colours import fg_code,bg_code, WHITE, BLACK

def taggedml(line, default_fg=WHITE, default_bg=BLACK):
    pattern=r'(<(?:\w|\*)+(?::\w+){0,1}>)'
    matches=re.findall(pattern, line)
    new_line=""
    tag_length=0
    index=0
    fg=RunLengthList([(0,fg_code(default_fg,False))])
    bg=RunLengthList([(0,bg_code(default_bg))])
    for m in matches:
        color_tag=m[1:-1].split(':')
        fg_color_str=color_tag[0]
        if '*' in fg_color_str:
            bold=True
            fg_color_str=fg_color_str.replace('*','')
        else:
            bold=False
        if len(color_tag)==2:
            bg_color_str=color_tag[1]
        else:
            bg_color_str=None
        if not hasattr(colours, fg_color_str.upper()):
            continue
        if bg_color_str!=None and not hasattr(colours, bg_color_str.upper()):
            continue
        m_idx=line.find(m,index)
        new_line=new_line+line[index:m_idx]
       
        try:
            
            fg_color=getattr(colours, fg_color_str.upper())
            if bg_color_str!=None:
                bg_color=getattr(colours, bg_color_str.upper())
            else:
                bg_color=default_bg
        except TypeError:
            return line
        fg.add_change(m_idx-tag_length, fg_code(fg_color,bold))
        if bg_color!=None:
            bg.add_change(m_idx-tag_length, bg_code(bg_color))
        
        
        index=line.find(m,index)+len(m)
        tag_length+=len(m)
        
    new_line=new_line+line[index:]    
    return Metaline(new_line, fg,bg)
        