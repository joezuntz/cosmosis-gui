from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from connector import Connector
from kivy.properties import NumericProperty, ListProperty, ColorProperty
from kivy.clock import Clock



class PipelineView(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(PipelineView, self).__init__(**kwargs)
        self.nodes = {}
        self.connectors = []

    def clear_pipeline(self):
        self.ids["chart"].clear_widgets()
        self.nodes = {}
        self.connectors = []

    def reposition(self):
        # we need to reposition all the nodes so that they are in the right place
        # and all the connectors so that they are in the right place
        chart = self.ids["chart"]
        chart.height = len(self.nodes) * 100
        height = chart.height
        print('chart pos size', chart.pos, chart.size)
        for i, node in enumerate(self.nodes.values()):
            # node.size = (chart.width, 50)
            # node.size
            node.pos[0] = chart.width/2 # - node.width/2
            node.pos[1] = height - (i+1) * 100
            # node.size = (chart.width, 50)
            print(node.pos)

    def draw_pipeline(self, modules):
        self.clear_pipeline()
        chart = self.ids["chart"]
        height = chart.height
        print("height", height)
        for i, module in enumerate(modules):
            box = Node(text=module)
            box.background_color = [0, 0, 1, 0.3]
            
            # box.size_hint = (0.3, 0.05)
            box.size_hint = (0.3, None)
            # box.height = 20
            # box.pos_hint = {"center_x": 0.5, "center_y": None}
            # box.pos_hint = 
            box.pos_y = height - (i+1) * 50
            chart.add_widget(box)
            if i > 0:
                # add a line between this widget and the previous one
                line = Connector(line_color=[1, 0, 0, 1], line_width=3)
                chart.add_widget(line)
                self.connectors.append(line)
                box.ancestors.append(last_box)
                box.ancestor_connectors.append(line)
                last_box.descendants.append(box)
                last_box.descendant_connectors.append(line)
            last_box = box
            self.nodes[module] = box
            Clock.schedule_once(lambda dt: self.reposition(), 0)

    def update_lines(self):
        for node in self.nodes.values():
            node.on_pos(0, 0)

    def reset_colours(self):
        for node in self.nodes.values():
            node.background_color = [0, 0, 1, 0.3]

    def update_module(self, module, update):
        node = self.nodes[module]
        if update == "success":
            node.background_color = [0, 1, 0, 0.3]
        elif update == "failure":
            node.background_color = [1, 0, 0, 0.3]




class BackgroundColor(Widget):
    pass


class Node(Label, BackgroundColor):
    """
    Flowchart node for the pipeline view
    """
    border_color = ColorProperty([0, 0, 0, 0])
    rect = ListProperty([0, 0, 0, 0])
    ancestors = ListProperty([])
    ancestor_connectors = ListProperty([])
    descendant_connectors = ListProperty([])
    descendants = ListProperty([])

    def on_touch_down(self, touch):
        return super().on_touch_down(touch)


    def on_pos(self, x, y):
        # we have moved to a new position.
        # we need to update the final coordinates of all our ancestor_connectors
        # and all the initial coordinates of all our descendant_connectors
        for connector in self.ancestor_connectors:
            connector.front = [self.center[0], self.center[1] + self.height/2]
        for connector in self.descendant_connectors:
            connector.back = [self.center[0], self.center[1] - self.height/2]
        

