import cosmosis
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock




RED_ON = "[color=ff0000]"
RED_OFF = "[/color]"

def red(text):
    return RED_ON + text + RED_OFF

def strip_red(text):
    return text.replace(RED_ON, "").replace(RED_OFF, "")

class KeyValueLabel(BoxLayout, TreeViewNode):
    key_text = StringProperty("")
    value_text = StringProperty("")

    def __init__(self, section, key_text="", value_text="", **kwargs):
        super(KeyValueLabel, self).__init__(**kwargs)
        self.key = key_text
        self.value = value_text
        self.ids["key_label"].text = key_text
        self.ids["value_label"].text = value_text
        self.section = section

    def on_touch_down(self, touch):
        app = App.get_running_app()
        app.display_help("params", self.section, self.key)

    def on_enter(self):
        self.value = self.ids["value_label"].text
        app = App.get_running_app()
        app.backend.set_param(self.section, self.key, self.value)

class ValuesLabel(BoxLayout, TreeViewNode):
    """
    Cell for a CosmoSIS value, which has three editable
    boxes for the min, value, and center.
    """
    key_text = StringProperty("")
    first_text = StringProperty("")
    second_text = StringProperty("")
    third_text = StringProperty("")

    def __init__(self, section, key_text, text, **kwargs):
        super(ValuesLabel, self).__init__(**kwargs)
        self.key = key_text
        values = text.split()
        if len(values) == 1:
            self.first = ""
            self.second = values[0]
            self.third = ""
        elif len(values) == 3:
            self.first = values[0]
            self.second = values[1]
            self.third = values[2]
        else:
            self.first = red(text)
            self.second = ""
            self.third = ""

        self.ids["key_label"].text = key_text
        self.ids["first_label"].text = self.first
        self.ids["second_label"].text = self.second
        self.ids["third_label"].text = self.third
        self.section = section

    def on_enter(self):
        self.first = self.ids["first_label"].text
        self.second = self.ids["second_label"].text
        self.third = self.ids["third_label"].text
        value = " ".join([self.first, self.second, self.third])
        app = App.get_running_app()
        app.backend.set_value(self.section, self.key, value)


class PriorsLabel(BoxLayout, TreeViewNode):
    """
    Cell for a CosmoSIS value, which has three editable
    boxes for the min, value, and center.
    """
    key_text = StringProperty("")
    kind_text = StringProperty("")
    second_text = StringProperty("")
    third_text = StringProperty("")

    def __init__(self, section, key_text, text, **kwargs):
        super(PriorsLabel, self).__init__(**kwargs)
        self.key = key_text
        values = text.split()
        if len(values) == 2:
            self.kind = values[0]
            self.second = values[1]
        elif len(values) == 3:
            self.kind = values[0]
            self.second = values[1]
            self.third = values[2]
        else:
            self.kind = "[color=ff0000]" +  text + "[/color]"
            self.second = ""
            self.third = ""

        if self.kind[:3] not in ["uni", "gau", "nor", "exp", "one", "tab", "loa"]:
            self.kind = "[color=ff0000]" +  self.kind + "[/color]"

        self.ids["key_label"].text = key_text
        self.ids["kind_label"].text = self.kind
        self.ids["second_label"].text = self.second
        self.ids["third_label"].text = self.third
        self.section = section

    def on_enter(self):
        self.kind = self.ids["kind_label"].text
        self.second = self.ids["second_label"].text
        self.third = self.ids["third_label"].text
        value = " ".join([self.kind, self.second, self.third])
        app = App.get_running_app()
        app.backend.set_prior(self.section, self.key, value)




class PipelinePanels(TabbedPanel):
    def set_params(self, ini: cosmosis.Inifile):
        self.ids["params_tab"].set_ini(ini, "params")

    def set_values(self, ini: cosmosis.Inifile):
        self.ids["values_tab"].set_ini(ini, "values")

    def set_priors(self, ini: cosmosis.Inifile):
        self.ids["priors_tab"].set_ini(ini, "priors")

    def on_current_tab(self, from_, to_):
        if to_.text == "Pipeline":
            Clock.schedule_once(lambda dt: to_.update_lines() and to_.ids["chart"].reposition(), 0)
        if to_.text != "Params":
            app = App.get_running_app()
            Clock.schedule_once(lambda dt: app.hide_info_panel(), 0)
            




class InifilePanel(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(InifilePanel, self).__init__(**kwargs)
        self.section_nodes = []

    def clear_tree(self, tv):
        tv: TreeView = self.ids["tv"]
        for node in self.section_nodes:
            tv.remove_node(node)
        tv.clear_widgets()
        self.section_nodes = []

    def set_ini(self, ini, kind):
        tv: TreeView = self.ids["tv"]
        self.clear_tree(tv)
        for section in ini.sections():
            section_node = tv.add_node(TreeViewLabel(text=section))
            self.section_nodes.append(section_node)
            for key, value in ini.items(section):
                if kind == "params":
                    node = KeyValueLabel(section, key_text=key, value_text=value)
                elif kind == "values":
                    node = ValuesLabel(section, key_text=key, text=value)
                elif kind == "priors":
                    node = PriorsLabel(section, key_text=key, text=value)
                else:
                    raise ValueError(f"Unknown kind {kind}")
                tv.add_node(node, section_node)
                    