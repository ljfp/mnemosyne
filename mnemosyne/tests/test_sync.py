#
# test_sync.py <Peter.Bienstman@UGent.be>
#

import os
from threading import Thread
from openSM2sync.server import Server
from openSM2sync.client import Client
from openSM2sync.log_entry import EventTypes

from mnemosyne.libmnemosyne import Mnemosyne
from mnemosyne.libmnemosyne.ui_components.main_widget import MainWidget

class Widget(MainWidget):
    
    def status_bar_message(self, message):
        print message
        
    def information_box(self, info):
        print info
        
    def error_box(self, error):
        print error

        
class MyServer(Server, Thread):

    program_name = "Mnemosyne"
    program_version = "test"
    capabilities = "TODO"

    stop_after_sync = True

    def __init__(self):
        Thread.__init__(self)
        os.system("rm -fr dot_sync_server")
        self.mnemosyne = Mnemosyne()
        self.mnemosyne.components.insert(0, ("mnemosyne.libmnemosyne.translator",
                             "GetTextTranslator"))
        self.mnemosyne.components.append(("test_sync", "Widget"))
        self.mnemosyne.components.append(\
            ("mnemosyne.libmnemosyne.ui_components.dialogs", "ProgressDialog"))
     
    def authorise(self, login, password):
        return login == "user" and password == "pass"

    def open_database(self, database_name):
        self.database = self.mnemosyne.database()

    def run(self):
        # We only open the database connection inside the thread to prevent
        # access problems, as a single connection can only be used inside a
        # single thread.
        self.mnemosyne.initialise(os.path.abspath(os.path.join(os.getcwdu(),
                                  "dot_sync_server")))
        self.fill_server_database()
        Server.__init__(self, "127.0.0.1", 8000, self.mnemosyne.main_widget())
        # Because we stop_after_sync is True, serve_forever will actually stop
        # after one sync.
        self.serve_forever()
        # Also running the actual tests we need to do inside this thread and
        # not in the main thread, again because of sqlite access restrictions.
        # However, if the asserts fail in this thread, nose won't flag them as
        # failures in the main thread, so we communicate failure back to the
        # main thread using self.passed_tests.
        self.passed_tests = False
        self.test_server(self)
        self.passed_tests = True
        
    def fill_server_database(self):
        pass

    def test(self):
        raise NotImplementedError


class MyClient(Client):
    
    program_name = "Mnemosyne"
    program_version = "test"
    capabilities = "TODO"
    
    def __init__(self):
        os.system("rm -fr dot_sync_client")
        self.mnemosyne = Mnemosyne()
        self.mnemosyne.components.insert(0, ("mnemosyne.libmnemosyne.translator",
                             "GetTextTranslator"))
        self.mnemosyne.components.append(("test_sync", "Widget"))
        self.mnemosyne.components.append(\
            ("mnemosyne.libmnemosyne.ui_components.review_widget", "ReviewWidget"))
        self.mnemosyne.components.append(\
            ("mnemosyne.libmnemosyne.ui_components.dialogs", "ProgressDialog"))
        self.mnemosyne.initialise(os.path.abspath(os.path.join(os.getcwdu(),
                                  "dot_sync_client")))
        self.mnemosyne.review_controller().reset()        
        Client.__init__(self, self.mnemosyne.database(),
                        self.mnemosyne.main_widget())
        
    def do_sync(self):
        self.sync("http://127.0.0.1:8000", "user", "pass")
        self.mnemosyne.finalise()


class TestSync(object):

    def teardown(self):
        assert self.server.passed_tests == True
        
    def test_add_tag(self):

        self.tag_name = unichr(40960) + u"abcd"

        def test_server(self):
            db = self.mnemosyne.database()
            tag = db.get_or_create_tag_with_name(unichr(40960) + u'>&<abcd')
            assert tag.id == self.client_tag_id
            assert tag.name == unichr(40960) + u">&<abcd"
            sql_res = db.con.execute("select * from log where event_type=?",
               (EventTypes.ADDED_TAG, )).fetchone()
            assert self.tag_added_timestamp == sql_res["timestamp"]            
        self.server = MyServer()
        self.server.test_server = test_server
        self.server.start()

        self.client = MyClient()
        tag = self.client.mnemosyne.database().\
              get_or_create_tag_with_name(unichr(40960) + u">&<abcd")
        self.server.client_tag_id = tag.id
        sql_res = self.client.mnemosyne.database().con.execute(\
            "select * from log where event_type=?", (EventTypes.ADDED_TAG,
             )).fetchone()
        self.server.tag_added_timestamp = sql_res["timestamp"]
        self.client.mnemosyne.controller().file_save()
        self.client.do_sync()
        
    #def test_add_cards(self):

    #    def test_server(self):
    #        db = self.mnemosyne.database()
    #        assert db.fact_count() == 1
    #        assert db.card_count() == 1
    #        card = db.get_card(self.client_card.id, id_is_internal=False)
    #        assert card.question() == self.client_card.question()

    #    self.server = MyServer()
    #    self.server.test_server = test_server
    #    self.server.start()

    #    self.client = MyClient()
    #    fact_data = {"q": "question",
    #                 "a": "answer"}
    #    card_type = self.client.mnemosyne.card_type_by_id("1")
    #    card = self.client.mnemosyne.controller().create_new_cards(fact_data,
    #        card_type, grade=-1, tag_names=["default"])[0]
    #    self.server.client_card = card
    #    self.client.mnemosyne.controller().file_save()
    #    self.client.do_sync()

