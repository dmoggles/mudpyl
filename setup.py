from setuptools import setup, find_packages
import os

#we need to execute __init__.py because that's where our version number lives.
#fortunately, it has barely any code in it. This -should- work under normal
#conditions, because everything is unzipped anyway for installation.
edict = {}
execfile(os.path.join('pymudclient', '__init__.py'), edict)
setup(name = "pymudclient",
      version = edict['__version__'],
      author = 'Dmitry Mogilevsky',
      author_email = 'dmitry.mogilevsky@gmail.com',
      url = 'https://github.com/dmoggles/pymudclient',
      description = "Python MUD client",
      long_description = open("README").read(),
      classifiers = [
          "Development Status :: 3 - Alpha",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Topic :: Communications :: Chat",
          "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
          "Topic :: Terminals :: Telnet"
          ],
      license = 'GNU GPL v2 or later',
      install_requires = ['Twisted', 'argparse', 'ordereddict','requests'],
      extras_require = {'rifttracker': ['peak.util.extremes'],
                        'gtkgui': ['pygtk']
                        },
      test_suite = 'nose.collector',
      packages = find_packages(),
      scripts = ['pymudclient/mudconnect.py'],
)
