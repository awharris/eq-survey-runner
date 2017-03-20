import json

from tests.integration.integration_test_case import IntegrationTestCase


class TestQuestionnaireInterstitial(IntegrationTestCase):

    def setUp(self):
        super().setUp()
        self.launchSurvey('test', 'interstitial_page', roles=['dumper'])
        self.assertInPage('Your response is legally required')
        self.first_url = self.last_url

    def test_form_not_processed_with_no_csrf_token(self):
        self.last_csrf_token = None
        self.post(action='start_questionnaire')
        self.assertStatusForbidden()
        self.assertEqualUrl(self.first_url)

    def test_given_on_introduction_page_when_submit_invalid_token_then_forbidden(self):
        self.last_csrf_token = 'made-up-token'
        self.post(action='start_questionnaire')
        self.assertStatusForbidden()
        self.assertEqualUrl(self.first_url)

    def test_given_on_introduction_page_when_submit_valid_token_then_redirect_to_next_page(self):
        self.post(action='start_questionnaire')
        self.assertStatusOK()
        self.assertInPage('What is your favourite breakfast food')

    def test_given_answered_question_when_change_answer_with_invalid_csrf_token_then_answers_not_saved(self):
        # Given
        self.post()
        post_data = {
            'favourite-breakfast': 'Muesli',
        }
        self.post(post_data=post_data)

        # When
        post_data = {
            'favourite-breakfast': 'Pancakes'
        }
        self.last_csrf_token = 'made-up-token'
        self.post(post_data=post_data)

        # Then
        self.assertStatusForbidden()
        self.get('/dump/answers')
        answers = json.loads(self.last_response.get_data(True))
        self.assertEqual('Muesli', answers['answers'][0]['value'])

    def test_given_valid_answers_on_household_composition_when_answer_with_invalid_csrf_token_then_answers_not_saved(self):
        # Given
        self.launchSurvey('census', 'household', roles=['dumper'])
        post_data = {
            'first_name': 'Joe'
        }

        # When
        self.last_csrf_token = 'made-up-token'
        self.post(url='/questionnaire/census/household/789/who-lives-here/0/household-composition', post_data=post_data)

        # Then
        self.assertStatusForbidden()
        self.get('/dump/answers')
        answers = json.loads(self.last_response.get_data(True))
        self.assertEqual(0, len(answers['answers']))

    def test_given_valid_answers_when_save_and_sign_out_with_invalid_csrf_token_then_answers_not_saved(self):
        # Given
        self.post()
        post_data = {
            'favourite-breakfast': 'Muesli',
            'action[save_sign_out]': ''
        }

        # When
        self.last_csrf_token = 'made-up-token'
        self.post(post_data=post_data)

        # Then
        self.assertStatusForbidden()
        self.get('/dump/answers')
        answers = json.loads(self.last_response.get_data(True))
        self.assertEqual(0, len(answers['answers']))

    def test_given_csrf_attack_when_refresh_then_on_question(self):
        # Given
        self.post()
        post_data = {
            'favourite-breakfast': 'Pancakes'
        }
        self.last_csrf_token = 'made-up-token'
        self.post(post_data=post_data)

        # When
        self.get(self.last_url)

        # Then
        self.assertEqual(self.last_response.status_code, 200)
        self.get('/dump/answers')
        answers = json.loads(self.last_response.get_data(True))
        self.assertEqual(0, len(answers['answers']))

    def test_given_csrf_attack_when_submit_new_answers_then_answers_saved(self):
        # Given
        self.post()
        post_data = {
            'favourite-breakfast': 'Pancakes',
            'csrf_token': 'made-up-token'
        }
        self.post(post_data=post_data)

        # When
        post_data = {
            'favourite-breakfast': 'Pancakes'
        }
        self.post(post_data=post_data)

        # Then
        self.assertStatusOK()
        self.get('/dump/answers')
        answers = json.loads(self.last_response.get_data(True))
        self.assertEqual('Pancakes', answers['answers'][0]['value'])
