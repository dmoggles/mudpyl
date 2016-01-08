"""The predefined keybindings for the GUI."""
from pymudclient.gui.keychords import from_string
from pymudclient.aliases import binding_alias

gui_macros = {}

def enter_pressed(realm):
    """Submit the line to the realm."""
    realm.gui.command_line.submit_line()

gui_macros[from_string('<Enter>')] = enter_pressed
gui_macros[from_string('<Return>')] = enter_pressed

def escape_pressed(realm):
    """Escape's been pressed. Store the current line in the history, and then
    clear the entry area.
    """
    realm.gui.command_line.escape_pressed()

gui_macros[from_string('<Escape>')] = escape_pressed

def tab_pressed(realm):
    """Complete the current word in the buffer."""
    realm.gui.command_line.tab_complete()

gui_macros[from_string('<Tab>')] = tab_pressed

def up_pressed(realm):
    """Go back one command in the history."""
    realm.gui.command_line.history_up()

gui_macros[from_string('<Up>')] = up_pressed

def down_pressed(realm):
    """Go forward one command into the history (ie, more recent)."""
    realm.gui.command_line.history_down()

gui_macros[from_string('<Down>')] = down_pressed

def pause_toggle(realm):
    """Toggle the output screen's pausing."""
    output_window = realm.gui.output_window
    if output_window.paused:
        output_window.unpause()
    else:
        output_window.pause()

gui_macros[from_string('<Pause>')] = pause_toggle

def reload_profile(realm):
    realm.reload_client()
    #realm.write("Main Module reloaded!")
    
gui_macros[from_string('C-r')]= reload_profile

