import os
import json
from typing import Dict, List

from .consts import ADDON_PATH

"""
	Template json structure:
	{
		"created": "yyyy-mm-dd",
		"last_used": "yyyy-mm-dd",
		"fields": [
			"content of first field",
			"content of second field",
			...
		]
	}

	JSON path for a given template: json["templates"][note_type][template_name]

"""



class Template:
    def __init__(self, created, last_used, fields):
        self.created = created
        self.last_used = last_used
        self.fields = fields

    created =""
    last_used=""
    fields: List[str] = []



templates: Dict[str, Dict[str, Template]]

# Load the templates from the templates.json file
def load_templates(relative_path="user_files/templates.json"):
    global templates
    templates = dict()

    path = os.path.join(ADDON_PATH, relative_path)

    with open(path, 'r') as json_file:
        j = json.load(json_file)

        for card_type, type_templates in j["templates"].items():
            templates[card_type] = dict()
            for template_name, template in type_templates.items():
                nt = Template(template["created"], template["last_used"], template["fields"])
                templates[card_type][template_name] = nt

# Save the templates to the templates.json file
def save_templates(relative_path="user_files/templates.json"):
    path = os.path.join(ADDON_PATH, relative_path)

    data = {"templates": {}}
    for card_type, type_templates in templates.items():
        data["templates"][card_type] = {}
        for template_name, template in type_templates.items():
            data["templates"][card_type][template_name] = {
                "created": "2022-07-02", "last_used": "2022-07-02",
                "fields": templates[card_type][template_name].fields
            }
    

    with open(path, 'w') as json_file:
        json_file.write(json.dumps(data))


# Add a new template to the list
def add_template(card_type: str, template_name: str, new_template: Template):
    """Add a new template to the list

    Args:
        card_type (str): the note type of the new template
        template_name (str): the name of the new template
        new_template (Template): the new template
    """

    if not templates.get(card_type, None):
        templates[card_type] = {}
    templates[card_type][template_name] = new_template

# Remove a template from the list
def delete_template(card_type: str, template_name: str):
    if not templates[card_type]: return
    if not templates[card_type][template_name]: return
    templates[card_type].pop(template_name)



# Get all template names of the given note type (e.g. Basic or Cloze)
def get_template_names(card_type: str) -> List[str]:
    tps = templates.get(card_type, None)
    if not tps:
        return []
    return list(tps.keys())

# Get the requested template
def get_template(card_type: str, template_name: str) -> Template:
    tps = templates.get(card_type, None)
    if not tps:
        return []
    return tps.get(template_name)
