from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from aqt.addcards import AddCards
from aqt.gui_hooks import editor_did_init_buttons
from aqt.editor import Editor

from .consts import *
from .templates import add_template, delete_template, load_templates
from .gui import ChooseTemplate





"""  BUTTONS AND OTHER CALLBACKS  """   
def on_template_button(editor: Editor):
    """Callback for the 'template' button in the editor. Opens the template menu

    Args:
        editor (Editor): the currently open editor
    """    

    if not editor.addMode:
        showInfo("on_template_button called even though we're not in addMode. Wtf ?")

    parent = editor.parentWindow

    if not editor.note:
        showInfo("Could not get the note type in on_template_button (%s)" % __file__)
        return
    model = editor.note.model()

    mw.ct = ct = ChooseTemplate(parent, note_type=model["name"], editor=editor, add_template=add_template, delete_template=delete_template)
    ct.show()

def on_setup_editor_buttons(buttons, editor: Editor):
    """Adds the template button to the editor 

    Args:
        buttons (buttons): the editor buttons
        editor (Editor): the open editor

    Returns:
        buttons: the editor buttons (with the new button appended)
    """        
    if not isinstance(editor.parentWindow, AddCards): return # TODO: make it work for 'EditCurrent' and the browser

    conf = mw.addonManager.getConfig(__name__)
    hotkey = conf.get("hotkey", TM_HOTKEY) if conf else TM_HOTKEY
    icon = os.path.join(ICONS_PATH, "template.png")

    b = editor.addButton(
        icon = icon,
        cmd = "template",
        func = on_template_button,
        tip="{} ({})".format("Apply card template", hotkey),
        keys=hotkey,
        disables=False
    )

    buttons.append(b)
    return buttons


""" INITIAL SETUP """
editor_did_init_buttons.append(on_setup_editor_buttons)
try:
    load_templates()
except Exception as e:
    showInfo("<h2 style='color: red;'>Card templates: could not load templates from file.</h2>\nError (please include this in any error report):\n%s" % traceback.format_exc())
