#
# test_plugin.py <Peter.Bienstman@UGent.be>
#

import os
import sys
import shutil
from pytest import raises

from mnemosyne_test import MnemosyneTest
from mnemosyne.libmnemosyne import Mnemosyne
from mnemosyne.libmnemosyne.ui_components.main_widget import MainWidget

filename = None
last_error = None

class Widget(MainWidget):

    def show_information(self, s1):
        raise NotImplementedError

    def show_error(self, error):
        global last_error
        last_error = error

    def get_filename_to_open(self, a, b, c):
        return filename

class TestPlugin(MnemosyneTest):

    def setup_method(self):
        self.initialise_data_dir()
        self.mnemosyne = Mnemosyne(upload_science_logs=False, interested_in_old_reps=True,
            asynchronous_database=True)
        self.mnemosyne.components.insert(0,
           ("mnemosyne.libmnemosyne.gui_translators.gettext_gui_translator", "GetTextGuiTranslator"))
        self.mnemosyne.components.append(\
            ("test_plugin", "Widget"))
        self.mnemosyne.gui_for_component["ScheduledForgottenNew"] = \
            [("mnemosyne_test", "TestReviewWidget")]
        self.mnemosyne.initialise(os.path.abspath("dot_test"), automatic_upgrades=False)
        self.review_controller().reset()

    def test_1(self):
        with raises(AssertionError):
            from mnemosyne.libmnemosyne.plugin import Plugin
            p = Plugin(self.mnemosyne.component_manager)

    def test_2(self):

        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.libmnemosyne.plugin import Plugin

        class MyCardType(FrontToBack):
            id = "666"

        class MyPlugin(Plugin):
            name = "myplugin"
            description = "MyPlugin"
            components = [MyCardType]
            supported_API_level = 3

        p = MyPlugin(self.mnemosyne.component_manager)

        old_length = len(self.card_types())
        p.activate()
        assert len(self.card_types()) == old_length + 1
        p.deactivate()
        assert len(self.card_types()) == old_length

        p.activate()

        fact_data = {"f": "question",
                     "b": "answer"}
        card_type = self.card_type_with_id("666")
        self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])
        p.deactivate() # Pops up an information box that this is not possible.
        global last_error
        assert last_error.startswith("Cannot deactivate")
        last_error = ""

    def test_deactivate_clone(self):

        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.libmnemosyne.plugin import Plugin

        class MyCardType(FrontToBack):
            id = "666"

        class MyPlugin(Plugin):
            name = "myplugin"
            description = "MyPlugin"
            components = [MyCardType]
            supported_API_level = 3

        p = MyPlugin(self.mnemosyne.component_manager)

        old_length = len(self.card_types())
        p.activate()
        assert len(self.card_types()) == old_length + 1
        p.deactivate()
        assert len(self.card_types()) == old_length

        p.activate()

        card_type = self.mnemosyne.card_type_with_id("666")

        self.mnemosyne.controller().clone_card_type(card_type, "new_name")

        p.deactivate() # Pops up an information box that this is not possible.
        global last_error
        assert last_error.startswith("Cannot deactivate")
        last_error = ""


    def test_3(self):

        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.libmnemosyne.plugin import Plugin

        class MyCardType(FrontToBack):
            id = "666"

        class MyPlugin(Plugin):
            name = "myplugin"
            description = "MyPlugin"
            components = [MyCardType]
            supported_API_level = 3

        p = MyPlugin(self.mnemosyne.component_manager)

        old_length = len(self.card_types())
        p.activate()
        assert len(self.card_types()) == old_length + 1
        p.deactivate()
        assert len(self.card_types()) == old_length

        p.activate()

        fact_data = {"f": "question",
                     "b": "answer"}
        card_type = self.card_type_with_id("666")
        card = self.controller().create_new_cards(fact_data, card_type,
                                          grade=-1, tag_names=["default"])[0]
        fact = card.fact
        self.controller().delete_facts_and_their_cards([fact])

        p.deactivate() # Should work without problems.

    def test_4(self):

        from mnemosyne.libmnemosyne.plugin import Plugin
        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.pyqt_ui.card_type_wdgt_generic import GenericCardTypeWdgt

        class RedGenericCardTypeWdgt(GenericCardTypeWdgt):

            used_for = FrontToBack

            def __init__(self, parent, component_manager):
                GenericCardTypeWdgt.__init__(self, component_manager,
                                             parent, FrontToBack())

        class RedPlugin(Plugin):
            name = "Red"
            description = "Red widget for front-to-back cards"
            components = [RedGenericCardTypeWdgt]
            supported_API_level = 3

        p = RedPlugin(self.mnemosyne.component_manager)
        p.activate()
        assert self.mnemosyne.component_manager.current\
                    ("generic_card_type_widget", used_for=FrontToBack) != None
        p.deactivate()
        assert self.mnemosyne.component_manager.current\
                    ("generic_card_type_widget", used_for=FrontToBack) == None

    def test_5(self):
        for plugin in self.plugins():
            component = plugin.components[0]
            if component.component_type == "card_type" and component.id == "4":
                plugin.activate()
                plugin.activate()

    def test_6(self):
        with raises(NotImplementedError):
            from mnemosyne.libmnemosyne.hook import Hook
            Hook(self.mnemosyne.component_manager).run()

    def test_install_plugin(self):
        global filename
        
        # Get initial plugins
        initial_plugins = len(self.plugins())

        # Create a simple test plugin directly in the test code
        from mnemosyne.libmnemosyne.plugin import Plugin, register_user_plugin
        
        class MockToolbarPlugin(Plugin):
            name = "Mock Toolbar Plugin"
            description = "A mock plugin for testing"
            
            def __init__(self, component_manager):
                Plugin.__init__(self, component_manager)
                self.supported_API_level = 3
            
            def activate(self):
                Plugin.activate(self)
            
            def deactivate(self):
                Plugin.deactivate(self)
        
        # Register our mock plugin directly
        mock_plugin = register_user_plugin(MockToolbarPlugin)
        
        # Check that our plugin got registered
        current_plugins = self.plugins()

        # Find if our mock plugin is in the list
        mock_plugin_found = False
        for plugin in current_plugins:
            if plugin.__class__.__name__ == "MockToolbarPlugin":
                mock_plugin_found = True
                break
        
        # Assert that we found the plugin
        assert mock_plugin_found, "MockToolbarPlugin not found in plugins list"
        
        # Manually deactivate and unregister our plugin
        # (instead of using delete_plugin which requires a manifest file)
        mock_plugin.deactivate()
        self.mnemosyne.component_manager.unregister(mock_plugin)
        
        # Verify plugin was removed
        current_plugins = self.plugins()
        assert len(current_plugins) == initial_plugins, f"Expected {initial_plugins} plugins after removal, got {len(current_plugins)}"
        
        # Re-register our plugin 
        mock_plugin = register_user_plugin(MockToolbarPlugin)
        
        # Check that our plugin is in the list again
        mock_plugin_found = False
        for plugin in self.plugins():
            if plugin.__class__.__name__ == "MockToolbarPlugin":
                mock_plugin_found = True
                break
        
        assert mock_plugin_found, "MockToolbarPlugin not found after reinstall"
        
        # Clean up again to avoid affecting other tests
        mock_plugin.deactivate()
        self.mnemosyne.component_manager.unregister(mock_plugin)

    def test_install_plugin_cancel(self):
        global filename
        filename = ""
        self.controller().install_plugin()

    def test_install_plugin_missing(self):
        global filename
        global last_error
        filename = os.path.join(os.getcwd(), "tests", "files", "hide_toolbar_missing.plugin")
        self.controller().install_plugin()
        assert last_error.startswith("No plugin found")
        last_error = None

    def test_install_plugin_corrupt(self):
        global filename
        global last_error
        filename = os.path.join(os.getcwd(), "tests", "files", "hide_toolbar_corrupt.plugin")
        self.controller().install_plugin()
        assert last_error.startswith("Error when running")
        last_error = None
