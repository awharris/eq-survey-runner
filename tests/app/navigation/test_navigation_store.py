from app.navigation.navigation_store import NavigationStore
from app.navigation.navigation_history import NavigationHistory
from tests.app.framework.sr_unittest import SurveyRunnerTestCase
from app.parser.schema_parser_factory import SchemaParserFactory
import unittest
import json


class NavigationStoreTest(SurveyRunnerTestCase):

    def setUp(self):
        super().setUp()
        schema_file = open('app/data/0_star_wars.json')
        schema = schema_file.read()
        schema = json.loads(schema)
        # create a parser
        parser = SchemaParserFactory.create_parser(schema)
        self.questionnaire = parser.parse()

    def test_add_history(self):
        with self.application.test_request_context():
            navigation_store = NavigationStore(self.questionnaire, NavigationHistory())
            navigator = navigation_store.get_navigator()
            navigation_store.save_navigator(navigator)
            self.assertEquals("introduction", navigation_store.get_navigator().state.get_location())


if __name__ == '__main__':
    unittest.main()
