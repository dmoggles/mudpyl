from pymudclient.modules import load_file
f=open(r'c:\temp\connect_log.log','w')
import sys
f.write('sys path: %s'%sys.path)   
f.close()
import argparse
from pymudclient.modules import load_file
from twisted.internet import stdio
from pymudclient import __version__
from pymudclient.processor import MudProcessor

parser = argparse.ArgumentParser(version = "%(prog)s " + __version__, 
                                 prog = 'processconnect')
parser.add_argument("modulename", help = "The module to import")
#parser.add_argument('-d','--directory', help="Module directory", dest='module_directory', default="",type=str)
#parser.add_argument('-s','--settings', help='Settings directory', dest='settings_directory',default='',type=str)


def main():
    options = parser.parse_args()
    #if options.module_directory != "":
    #    directory = options.module_directory
    #    import sys
    #    sys.path.append(directory)
    from twisted.internet import reactor    
    #modclass = load_file(options.modulename)
    modclass = load_file(options.modulename)
    
    processor = MudProcessor()
    processor.reactor = reactor
    modinstance = processor.load_module(modclass)
        
    stdio.StandardIO(processor)
    reactor.run()
        
if __name__ == '__main__':
    main()