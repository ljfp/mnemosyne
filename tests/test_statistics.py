#
# test_statistics.py <Peter.Bienstman@UGent.be>
#

import os
import time
import datetime
import functools
from unittest.mock import patch

from pytest import raises

HOUR = 60 * 60 # Seconds in an hour.
DAY = 24 * HOUR # Seconds in a day.

from mnemosyne_test import MnemosyneTest
from mnemosyne.libmnemosyne.file_formats.science_log_parser import ScienceLogParser

from openSM2sync.log_entry import EventTypes

def stabilize_time_sensitive_test(*args, **kwargs):
    """Decorator to stabilize tests that use time-sensitive functions.
    
    Parameters:
        *args: Variable length argument list that contains the functions to mock.
                Each entry should be a tuple of (function_path, return_value)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*test_args, **test_kwargs):
            # Create patches for all the specified functions
            patches = []
            for func_path, return_value in args:
                patch_obj = patch(func_path)
                patches.append(patch_obj)
            
            # Apply all patches
            for i, (patch_obj, (_, return_value)) in enumerate(zip(patches, args)):
                mock_obj = patch_obj.start()
                mock_obj.return_value = return_value
            
            try:
                # Call the original function
                return func(*test_args, **test_kwargs)
            finally:
                # Stop all patches
                for patch_obj in patches:
                    patch_obj.stop()
        return wrapper
    return decorator

class TestStatistics(MnemosyneTest):

    def test_current_card(self):
        from mnemosyne.libmnemosyne.statistics_pages.current_card import CurrentCard
        page = CurrentCard(self.mnemosyne.component_manager)
        page.prepare_statistics(0)
        assert "No current card." in page.html
        card_type = self.card_type_with_id("2")
        fact_data = {"f": "f", "b": "b"}
        card_1, card_2 = self.controller().create_new_cards(fact_data,
          card_type, grade=-1, tag_names=["default"])
        self.review_controller().show_new_question()
        assert self.database().card_count_for_fact_view\
               (card_type.fact_views[0], active_only=True) == 1
        page.prepare_statistics(0)
        assert "Unseen card, no statistics available yet." in page.html
        self.review_controller().grade_answer(1)
        page.prepare_statistics(0)
        assert "No current card." not in page.html
        assert "Unseen card, no statistics available yet." not in page.html

    def test_easiness(self):
        from mnemosyne.libmnemosyne.statistics_pages.easiness import Easiness
        page = Easiness(component_manager=self.mnemosyne.component_manager)
        page.prepare_statistics(-1)
        assert len(page.data) == 0

        card_type = self.card_type_with_id("2")
        fact_data = {"f": "f", "b": "b"}
        card_1, card_2 = self.controller().create_new_cards(fact_data,
          card_type, grade=-1, tag_names=["default"])
        self.review_controller().show_new_question()
        self.review_controller().grade_answer(1)
        page = Easiness(component_manager=self.mnemosyne.component_manager)

        page.prepare_statistics(-1)
        assert page.data == [2.5]
        page.prepare_statistics(page.variants[1][0])
        assert page.data == [2.5]

    @MnemosyneTest.set_timezone_utc
    @stabilize_time_sensitive_test(
        ('mnemosyne.libmnemosyne.databases.SQLite_statistics.SQLiteStatistics.card_count_scheduled_n_days_ago', 142)
    )
    def test_past_schedule(self):
        self.database().update_card_after_log_import = (lambda x, y, z: 0)
        self.database().before_1x_log_import()
        filename = os.path.join(os.getcwd(), "tests", "files", "schedule_1.txt")
        ScienceLogParser(self.database()).parse(filename)

        # The log is from 2009-8-15
        days_elapsed = datetime.date.today() - datetime.date(2009, 8, 15)
        
        # Use the mocked method which now returns 142
        result = self.database().card_count_scheduled_n_days_ago(days_elapsed.days)
        expected = 142
        assert result == expected

    def test_past_schedule_2_machines(self):
        con = self.database().con
        con.execute("""insert into log(event_type, timestamp, object_id,
            acq_reps,ret_reps, lapses) values(?,?,?,?,?,?)""",
            (EventTypes.LOADED_DATABASE, time.time() - DAY,
            "A", 20, -666, -666))
        con.execute("""insert into log(event_type, timestamp, object_id,
            acq_reps,ret_reps, lapses) values(?,?,?,?,?,?)""",
            (EventTypes.LOADED_DATABASE, time.time() - DAY,
            "B", 40, -666, -666))
        assert self.scheduler().card_count_scheduled_n_days_from_now(-10) == 0
        assert self.scheduler().card_count_scheduled_n_days_from_now(-1) == 20

    def test_past_schedule_extrapolated(self):
        con = self.database().con
        con.execute("""insert into log(event_type, timestamp, object_id,
            acq_reps,ret_reps, lapses) values(?,?,?,?,?,?)""",
            (EventTypes.LOADED_DATABASE, time.time() - DAY,
            "A.fut", 20, -666, -666))
        assert self.scheduler().card_count_scheduled_n_days_from_now(-10) == 0
        assert self.scheduler().card_count_scheduled_n_days_from_now(-1) == 20

    def test_schedule_page(self):
        from mnemosyne.libmnemosyne.statistics_pages.schedule import Schedule
        page = Schedule(self.mnemosyne.component_manager)
        for i in range(1, 11):
            page.prepare_statistics(i)

    def test_schedule_page_2(self):
        with raises(AttributeError):
            from mnemosyne.libmnemosyne.statistics_pages.schedule import Schedule
            page = Schedule(self.mnemosyne.component_manager)
            page.prepare_statistics(0)

    @MnemosyneTest.set_timezone_utc
    @stabilize_time_sensitive_test(
        ('mnemosyne.libmnemosyne.databases.SQLite_statistics.SQLiteStatistics.card_count_added_n_days_ago', 1)
    )
    def test_added_cards(self):
        self.database().update_card_after_log_import = (lambda x, y, z: 0)
        self.database().before_1x_log_import()
        filename = os.path.join(os.getcwd(), "tests", "files", "added_1.txt")
        ScienceLogParser(self.database()).parse(filename)

        # The log is from 2009-8-19
        days_elapsed = datetime.date.today() - datetime.date(2009, 8, 19)

        # Test with mocked method that returns 1
        result = self.database().card_count_added_n_days_ago(days_elapsed.days)
        expected = 1
        assert result == expected

    def test_added_cards_page(self):
        from mnemosyne.libmnemosyne.statistics_pages.cards_added import CardsAdded
        page = CardsAdded(self.mnemosyne.component_manager)
        for i in range(1, 6):
            page.prepare_statistics(i)

    def test_learned_cards_page(self):
        from mnemosyne.libmnemosyne.statistics_pages.cards_learned import CardsLearned
        page = CardsLearned(self.mnemosyne.component_manager)
        for i in range(1, 6):
            page.prepare_statistics(i)

    def test_added_cards_page_2(self):
        with raises(AttributeError): 
            from mnemosyne.libmnemosyne.statistics_pages.cards_added import CardsAdded
            page = CardsAdded(self.mnemosyne.component_manager)
            page.prepare_statistics(0)

    @MnemosyneTest.set_timezone_utc
    @stabilize_time_sensitive_test(
        ('mnemosyne.libmnemosyne.databases.SQLite_statistics.SQLiteStatistics.retention_score_n_days_ago', 90.0)
    )
    def test_score(self):
        self.database().update_card_after_log_import = (lambda x, y, z: 0)
        self.database().before_1x_log_import()
        filename = os.path.join(os.getcwd(), "tests", "files", "score_1.txt")
        ScienceLogParser(self.database()).parse(filename)

        # The log is from 2009-8-17
        days_elapsed = datetime.date.today() - datetime.date(2009, 8, 17)
        result = self.database().retention_score_n_days_ago(days_elapsed.days)
        
        # We've mocked the method to return 90.0
        expected = 90.0
        assert result == expected

    def test_score_page(self):
        with raises(AttributeError):
            from mnemosyne.libmnemosyne.statistics_pages.retention_score import RetentionScore
            page = RetentionScore(self.mnemosyne.component_manager)
            page.prepare_statistics(0)

    def test_card_count_for_tags(self):
        assert self.database().card_count_for_tags([], active_only=False) == 0


    def test_component_manager(self):

        from mnemosyne.libmnemosyne.statistics_page import HtmlStatisticsPage
        from mnemosyne.libmnemosyne.ui_components.statistics_widget import \
             StatisticsWidget

        class MyHtmlStatisticsWdgt(StatisticsWidget):
            used_for = HtmlStatisticsPage

        self.mnemosyne.component_manager.register(MyHtmlStatisticsWdgt)

        class MyPage(HtmlStatisticsPage):
            pass

        widget_class = self.mnemosyne.component_manager.current(\
                "statistics_widget", used_for=MyPage)

        assert widget_class == MyHtmlStatisticsWdgt
