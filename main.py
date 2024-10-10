import cosmosis
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.lang import Builder
from kivy.uix.widget import Widget
from plyer import filechooser
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Line
import numpy as np

from ini_panels import *
from pipeline import *
from results import *

from kivy.properties import NumericProperty, ListProperty, ColorProperty, BooleanProperty
from kivy.clock import Clock
import contextlib
import os
import threading
from cosmosis.runtime import callbacks

BLOCK_LOG_READ = "READ-OK"
BLOCK_LOG_WRITE = "WRITE-OK"
BLOCK_LOG_READ_FAIL = "READ-FAIL"
BLOCK_LOG_WRITE_FAIL = "WRITE-FAIL"
BLOCK_LOG_READ_DEFAULT = "READ-DEFAULT"
BLOCK_LOG_REPLACE = "REPLACE-OK"
BLOCK_LOG_REPLACE_FAIL = "REPLACE-FAIL"
BLOCK_LOG_CLEAR = "CLEAR"
BLOCK_LOG_DELETE = "DELETE"
BLOCK_LOG_START_MODULE = "MODULE-START"
BLOCK_LOG_COPY = "COPY"

@contextlib.contextmanager
def change_directory(new_dir):
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(old_dir)


def print_callback(event, details):
    print(event, details)



root_dir = "/Users/jzuntz/src/cosmosis/cosmosis-standard-library"


class Backend:
    def __init__(self, app):
        self.app = app
        self.params = None
        self.values = None
        self.priors = None
        self.pipeline = None
        self.results = None
        self.pipeline_log = None

    def open_file(self, filename):
        with change_directory(root_dir):
            self.params = cosmosis.Inifile(filename)
            self.params.set("pipeline", "timing", "T")
            modules = self.params.get("pipeline", "modules")
            modules = modules.replace("eboss16_elg_1", "")
            modules = " ".join(modules.split())
            self.params.set("pipeline", "modules", modules)    
            self.values = cosmosis.Inifile(root_dir + "/" + self.params["pipeline", "values"])
            priors_file = root_dir + "/" + self.params.get("pipeline", "priors", fallback="")
            if priors_file:
                self.priors = cosmosis.Inifile(priors_file)
            else:
                # empty file, so we can add them later
                self.priors = cosmosis.Inifile(None)
        threading.Thread(target=self.open_pipeline).start()

    def modules(self):
        return self.params.get("pipeline", "modules").split()

    def pipeline_opened(self):
        print("pipeline opened")
        self.app.setup_pipeline_tab()

    def help_for_parameter(self, section, key):

        module = self.pipeline.get_module(section)

        if module is None:
            print("no module")
            return ""
        doc = module.doc
        if doc is None:
            print("no doc")
            return ""
        try:
            info = doc["params"][key]
        except KeyError:
            print("no params or key")
            return ""
        try:
            meaning = info["meaning"]
            default = str(info["default"])
            val_type = info["type"]
            if default.strip():
                default = f"Default = {default}"
            else:
                default = "Required parameter."

            return f"{val_type}. {default}\n{meaning})"
        except Exception as e:
            print(f"error {e}")
            return ""

    def set_param(self, section, key, value):
        print(f"Setting param {section} {key} to {value}")
        self.params.set(section, key, value)
    
    def set_value(self, section, key, value):
        print(f"Setting value {section} {key} to {value}")
        self.values.set(section, key, value)

    def set_prior(self, section, key, value):
        print(f"Setting prior {section} {key} to {value}")
        self.priors.set(section, key, value)

    def pipeline_callback(self, event, details):
        if event == callbacks.MODULE_RUN_SUCCESS:
            self.app.update_pipeline_tab(details["module"].name, "success")
        elif event == callbacks.MODULE_RUN_FAIL:
            self.app.update_pipeline_tab(details["module"].name, "failure")
        else:
            print(event, details)

    def open_pipeline(self):
        with change_directory(root_dir):
            self.pipeline = cosmosis.LikelihoodPipeline(self.params, values=self.values, priors=self.priors,callback=self.pipeline_callback)
        Clock.schedule_once(lambda dt: self.pipeline_opened(), 0)

    def run_pipeline(self):
        if self.pipeline is None:
            return
        v = self.pipeline.start_vector()
        self.results = self.pipeline.run_results(v)
        block = self.results.block
        self.pipeline_log = []
        for i in range(block.get_log_count()):
            entry = block.get_log_entry(i)
            self.pipeline_log.append(entry)
        Clock.schedule_once(lambda dt: self.app.display_results(), 0)


    def get_info_for_quantity(self, section, key):
        if self.results is None:
            return None
        # get the logs of the block to find out when this was made etc
        info = []
        module = "Sampler"
        for entry in self.pipeline_log:
            if entry.logtype == BLOCK_LOG_START_MODULE:
                module = entry.section
            if module == "Results":
                continue
            if entry.section == section and entry.name == key:
                if entry.logtype == BLOCK_LOG_READ:
                    info.append(f"{module} read this value")
                elif entry.logtype == BLOCK_LOG_WRITE:
                    info.append(f"{module} wrote this value")
                elif entry.logtype == BLOCK_LOG_READ_FAIL:
                    info.append(f"{module} tried to read this value but failed")
                elif entry.logtype == BLOCK_LOG_WRITE_FAIL:
                    info.append(f"{module} tried to write this value but failed")
                elif entry.logtype == BLOCK_LOG_READ_DEFAULT:
                    info.append(f"{module} read the default value")
                elif entry.logtype == BLOCK_LOG_REPLACE:
                    info.append(f"{module} replaced this value")
                elif entry.logtype == BLOCK_LOG_REPLACE_FAIL:
                    info.append(f"{module} tried to replace this value but failed")
                else:
                    info.append(f"{module} unknown log type {entry.logtype}")
        return info
                






class CosmosisApp(App):
    showInfoPanel = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(CosmosisApp, self).__init__(*args, **kwargs)
        self._backend = Backend(self)

    def show_info_panel(self):
        self.showInfoPanel = True

    def hide_info_pane(self):
        self.showInfoPanel = False

    @property
    def backend(self):
        return self._backend
        
    def setup_pipeline_tab(self):
        tab = self.root.ids["pipeline_panel"].ids["pipeline_tab"]
        Clock.schedule_once(lambda dt: tab.draw_pipeline(self.backend.modules()), 0)

    def update_pipeline_tab(self, module, update):
        tab = self.root.ids["pipeline_panel"].ids["pipeline_tab"]
        Clock.schedule_once(lambda dt: tab.update_module(module, update), 0)

    def display_results(self):
        tab = self.root.ids["pipeline_panel"].ids["results_tab"]
        tab.set_block(self.backend.results.block)

    def open_file(self, filenames):
        if not filenames:
            return
        filename = filenames[0]
        self.backend.open_file(filename)
        panel = self.root.ids["pipeline_panel"]
        panel.set_params(self.backend.params)
        panel.set_values(self.backend.values)
        panel.set_priors(self.backend.priors)

    def start_open_file(self):
        filechooser.open_file(on_selection=self.open_file)
    
    def run_pipeline(self):
        threading.Thread(target=self.backend.run_pipeline).start()

    def reset_pipeline(self):
        self.backend.results = None
        tab = self.root.ids["pipeline_panel"].ids["pipeline_tab"]
        tab.reset_colours()

    def display_help(self, kind, section, key):
        if kind == "params":
            info = self.backend.help_for_parameter(section, key)
            pane = self.root.ids["info_pane_text"]
            pane.text = info
            self.show_info_panel()

    def selected_result_node(self, section, key):
        info = self.backend.get_info_for_quantity(section, key)
        self.root.ids["pipeline_panel"].ids["results_tab"].ids["text_detail"].text = "\n".join(info)

        


if __name__ == '__main__':
    app = CosmosisApp()
    Builder.load_file("keyvaluelabel.kv")
    Builder.load_file("valueslabel.kv")
    Builder.load_file("priorslabel.kv")
    Builder.load_file("inifilepanel.kv")
    Builder.load_file("pipelineview.kv")
    Builder.load_file("pipelinepanels.kv")
    Builder.load_file("cosmosis.kv")
    # Clock.schedule_once(lambda dt: app.open_file(["/Users/jzuntz/src/cosmosis/cosmosis-standard-library/examples/bao.ini"]), 0)
    app.run()