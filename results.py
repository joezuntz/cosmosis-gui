import cosmosis
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanelItem
from plyer import filechooser
from kivy.graphics import Line
import numpy as np
from kivy.properties import NumericProperty, ListProperty, ColorProperty
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode


class ResultsLabel(TreeViewLabel):
    def on_touch_down(self, touch):
        key = self.text.strip()
        section = self.parent_node.text
        app = App.get_running_app()
        app.selected_result_node(section, key)


class ResultsView(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(ResultsView, self).__init__(**kwargs)
        self.section_nodes = []
        

    def clear_nodes(self):
        tv: TreeView = self.ids["results_tree"]
        for node in self.section_nodes:
            tv.remove_node(node)
        self.section_nodes = []

    def select_node(self, node):
        print(node.text)

        

    def set_block(self, block: cosmosis.DataBlock):
        self.clear_nodes()

        tv: TreeView = self.ids["results_tree"]
        for section in block.sections():
            node = ResultsLabel(text=section)
            self.section_nodes.append(node)
            tv.add_node(node)
            for _, key in block.keys(section):
                label = ResultsLabel(text = f"{key}")
                tv.add_node(label, node)
