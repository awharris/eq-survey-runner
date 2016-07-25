from tests.integration.star_wars.star_wars_tests import StarWarsTestCase


class TestLightSidePath(StarWarsTestCase):

    def test_light_side_path(self):

        self.check_introduction_text()

        first_page = self.start_questionnaire()

        # Our answers
        form_data = {

            "6cf5c72a-c1bf-4d0c-af6c-d0f07bc5b65b": "234",
            "92e49d93-cbdc-4bcb-adb2-0e0af6c9a07c": "40",
            "pre49d93-cbdc-4bcb-adb2-0e0af6c9a07c": "1370",

            "a5dc09e8-36f2-4bf4-97be-c9e6ca8cbe0d": "Elephant",
            "7587eb9b-f24e-4dc0-ac94-66118b896c10": "Luke, I am your father",
            "9587eb9b-f24e-4dc0-ac94-66117b896c10":"[Luke Skywalker, Yoda, Qui-Gon Jinn]",

            "6fd644b0-798e-4a58-a393-a438b32fe637-day": "28",
            "6fd644b0-798e-4a58-a393-a438b32fe637-month": "05",
            "6fd644b0-798e-4a58-a393-a438b32fe637-year": "1983",

            "06a6a4b7-6ce4-4687-879d-3443cd8e2ff0-day": "29",
            "06a6a4b7-6ce4-4687-879d-3443cd8e2ff0-month": "05",
            "06a6a4b7-6ce4-4687-879d-3443cd8e2ff0-year": "1983",

            "action[save_continue]": "Save &amp; Continue"
        }

        # Form submission with no errors
        resp = self.submit_page(first_page, form_data)
        self.assertNotEquals(resp.headers['Location'], first_page)

        # Second page
        second_page = resp.headers['Location']
        resp = self.navigate_to_page(second_page)
        content = resp.get_data(True)

        # Pipe Test for section title
        self.assertRegexpMatches(content, 'On 2 June 1983 how many were employed?')

        # Textarea question
        self.assertRegexpMatches(content, 'Why doesn&#39;t Chewbacca receive a medal at the end of A New Hope?')
        self.assertRegexpMatches(content, '215015b1-f87c-4740-9fd4-f01f707ef558')

        # Our answers
        form_data = {
            # People in household
            "215015b1-f87c-4740-9fd4-f01f707ef558": "Wookiees don’t place value in material rewards and refused the medal initially", # NOQA
            # User Action
            "action[save_continue]": "Save &amp; Continue"
        }

        resp = self.submit_page(second_page, form_data)

        # There are no validation errors
        self.assertRegexpMatches(resp.headers['Location'], r'\/questionnaire\/0\/789\/summary$')

        summary_url = resp.headers['Location']

        resp = self.navigate_to_page(summary_url)

        # We are on the review answers page
        content = resp.get_data(True)
        self.assertRegexpMatches(content, '<title>Summary</title>')
        self.assertRegexpMatches(content, '>Star Wars</')
        self.assertRegexpMatches(content, '>Your responses<')
        self.assertRegexpMatches(content, '(?s)How old is Chewy?.*?234')
        self.assertRegexpMatches(content, '(?s)How many Octillions do Nasa reckon it would cost to build a death star?.*?£40')
        self.assertRegexpMatches(content, '(?s)How hot is a lightsaver in degrees C?.*?1370')
        self.assertRegexpMatches(content, '(?s)What animal was used to create the engine sound of the Empire\'s TIE fighters?.*?Elephant') # NOQA
        self.assertRegexpMatches(content, '(?s)Which of these Darth Vader quotes is wrong?.*?Luke, I am your father')
        self.assertRegexpMatches(content, '(?s)Which 3 have wielded a green lightsaber?.*?<li class="list__item">Y.*?o.*?d.*?a') # NOQA
        self.assertRegexpMatches(content, '(?s)Which 3 appear in any of the opening crawlers?')
        self.assertRegexpMatches(content, '(?s)When was The Empire Strikes Back released?.*?From: 28/05/1983.*?To: 29/05/1983') # NOQA
        self.assertRegexpMatches(content, '(?s)What was the total number of Ewokes?.*?')
        self.assertRegexpMatches(content, '(?s)Why doesn\'t Chewbacca receive a medal at the end of A New Hope?.*?Wookiees don’t place value in material rewards and refused the medal initially') # NOQA
        self.assertRegexpMatches(content, '>Please check carefully before submission<')
        self.assertRegexpMatches(content, '>Submit answers<')

        self.complete_survey(summary_url)
