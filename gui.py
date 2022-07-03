import json

from aqt.utils import showInfo
from aqt.qt import *
from aqt.editor import Editor

from .templates import Template, get_template, get_template_names, load_templates, save_templates


def clamp(n, minimum, maximum): return max(minimum, min(n, maximum)) if maximum > minimum else minimum


""" The template dialog """
class ChooseTemplate(QDialog):

    def __init__(self, parent, note_type: str, editor: Editor, add_template: Callable[[str, str, Template], None], delete_template: Callable[[str, str], None]):
        QDialog.__init__(self)
        self.parent = parent
        self.note_type = note_type
        self.template_names = get_template_names(note_type)
        self.editor = editor
        self.add_template = add_template
        self.delete_template = delete_template

        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Choose a template")
        self.resize(480, 360)

        self.setup_ui()
        
    def setup_ui(self):
        " Setup the dialog UI "
        layout = QVBoxLayout()

        top_layout = QFormLayout()
        self.filter_field = filter_field = QLineEdit("", self); filter_field.setFocus()
        filter_field.textChanged.connect(self.on_filter_changed)
        top_layout.addRow("Name: ", filter_field)


        self.nlist = nlist = QListWidget()
        nlist.setSpacing(1)
        nlist.addItems(self.template_names)
        nlist.currentItemChanged.connect(self.on_selected_template_changed)
        
        self.selected_template = None
        if len(self.template_names) != 0:
            self.selected_template = self.template_names[0]
        nlist.setCurrentRow(0)
        self.shown_rows = [i for i in range(nlist.count())]


        button_box = QDialogButtonBox(Qt.Horizontal, self)
        button_box.setCenterButtons(False)

        close_btn = button_box.addButton("Close", QDialogButtonBox.RejectRole)
        add_btn = button_box.addButton("Add card as template", QDialogButtonBox.ActionRole)
        delete_btn = button_box.addButton("Delete selected", QDialogButtonBox.ActionRole)
        choose_btn = button_box.addButton("Choose", QDialogButtonBox.ActionRole)

        close_btn.setDefault(False); close_btn.setAutoDefault(False)
        add_btn.setDefault(False); close_btn.setAutoDefault(False)
        delete_btn.setDefault(False); close_btn.setAutoDefault(False)
        choose_btn.setDefault(True); close_btn.setAutoDefault(True)

        close_btn.setToolTip("Close this window")
        add_btn.setToolTip("Add the current card as a new template")
        delete_btn.setToolTip("Delete the selected template")
        choose_btn.setToolTip("Apply the selected template (Enter)")

        close_btn.clicked.connect(self.close)
        add_btn.clicked.connect(self.on_new_template)
        # TODO: be able to delete templates
        choose_btn.clicked.connect(self.on_choose_template)


        layout.addLayout(top_layout)
        layout.addWidget(self.nlist)
        layout.addWidget(button_box)

        self.setLayout(layout)

        " Setup shortcuts "
        QShortcut(QKeySequence("Enter"), self).activated.connect(self.on_choose_template)
        QShortcut(QKeySequence("up"), self).activated.connect(lambda: self.move_selection(-1))
        QShortcut(QKeySequence("down"), self).activated.connect(lambda: self.move_selection(1))

    # Refresh the template list (used when a template has been added/deleted)    
    def refresh_list(self):
        self.template_names = get_template_names(self.note_type)
        self.nlist.clear()
        self.nlist.addItems(self.template_names)
        self.selected_template = None
        if len(self.template_names) != 0:
            self.selected_template = self.template_names[0]
        self.nlist.setCurrentRow(0)
        self.shown_rows = [i for i in range(self.nlist.count())]


    # Callback of filter: update the list (only show name-filtered templates)
    def on_filter_changed(self):
        self.shown_rows = []
        for i in range(self.nlist.count()):
            item = self.nlist.item(i)
            if self.filter_field.text().lower() in item.text().lower():
                item.setHidden(False)
                self.shown_rows.append(i)
            else:
                item.setHidden(True)

        if len(self.shown_rows) == 0: return
        
        if self.nlist.currentRow() < 0 or self.nlist.currentRow() >= self.nlist.count() or self.nlist.currentItem().isHidden():
            self.nlist.setCurrentRow(clamp(self.shown_rows[0], 0, self.nlist.count()))

    # Move template selection up and down
    def move_selection(self, delta):
        delta = 1 if delta >= 0 else -1
        shown = list(set(self.shown_rows+[self.nlist.currentRow()]))
        try:
            nrow = shown[shown.index(self.nlist.currentRow())+delta]
        except (ValueError, IndexError):
            nrow = 0
        
        self.nlist.setCurrentRow(clamp(nrow, 0, self.nlist.count()-1))

    # Callback of list: update self.selected_template to match list selection
    def on_selected_template_changed(self):
        if not self.nlist.currentItem(): return
        self.selected_template = self.nlist.currentItem().text()


    # Callback of delete button: delete selected template
    def on_delete_template(self):
        note = self.editor.note
        if not note: return

        self.delete_template(note.model()["name"], self.selected_template)
        save_templates()
        load_templates()
        self.refresh_list()

    # Callback of template name QInputDialog: add the template with the given name
    def on_new_template_named(self, template_name: str):
        note = self.editor.note
        if not note: return
        if not template_name or template_name == "":
            showInfo(f"{__file__}::on_new_template_named: Invalid new template name")
            return

        self.add_template(note.model()["name"], template_name, Template("2022-07-02", "2022-07-02", note.values()))
        save_templates()
        load_templates()
        self.refresh_list()

    # Callback of add template button: ask for the new template name
    def on_new_template(self):
        note = self.editor.note
        if not note: return

        text, ok = QInputDialog.getText(self, 'New template name', 'New template name: ')
        if not ok or text.strip() == "":
            showInfo("Invalid template name. Cannot be empty.")
        
        self.on_new_template_named(text.strip())

    # Callback of choose button or Enter: apply the chosen template
    def on_choose_template(self):
        """ Apply the template to the edited card field by field """
        if not self.selected_template: return
        note = self.editor.note
        if not note: return

        template = get_template(self.note_type, self.selected_template)

        for i, content in enumerate(template.fields):
            self.editor.web.eval("focusField(%s);" % json.dumps(i))
            # Anki's HTML header seems to assume latin1 encoding instead of utf8 so we need to use that
            # Also we need to set 'extended' to true otherwise it removes html elements (and classes)
            self.editor.doPaste(content.encode("latin1").decode("utf8"), False, True)

        self.editor.web.eval("focusField(0);")
        self.close()


