import logging

from app.data_model.answer_store import AnswerStore

logger = logging.getLogger(__name__)


def evaluate_rule(rule, answer_value):
    """
    Determine whether a rule will be satisfied based on a given answer
    :param rule:
    :param answer_value:
    :return:
    """
    when = rule['when']
    match_value = when['value']
    condition = when['condition']

    # Evaluate the condition on the routing rule
    if condition == 'equals' and match_value == answer_value:
        return True
    elif condition == 'not equals' and match_value != answer_value:
        return True
    return False


def evaluate_goto(goto_rule, answers):
    """
    Determine whether a goto rule will be satisfied based on a given answer
    :param goto_rule:
    :param answers:
    :return:
    """
    if 'when' in goto_rule.keys():
        answer_index = goto_rule['when']['id']
        filtered = answers.filter(answer_index)
        if len(filtered) == 1:
            answer = filtered[0]
            if evaluate_rule(goto_rule, answer['value']):
                return True
        else:
            return False
    elif 'id' in goto_rule.keys():
        return True
    return None


def evaluate_repeat(repeat_rule, answers):
    """
    Returns the number of times repetition should occur based on answers
    :param repeat_rule:
    :param answers:
    :return: The number of times to repeat
    """
    if 'answer_id' in repeat_rule:
        repeat_index = repeat_rule['answer_id']
        filtered = answers.filter(repeat_index)
        if len(filtered) == 1:
            return int(filtered[0]['value'])
    return 1


class Navigator:
    PRECEEDING_INTERSTITIAL_PATH = ['introduction']
    CLOSING_INTERSTITIAL_PATH = ['summary', 'thank-you']

    def __init__(self, survey_json, answer_store=None):
        self.answer_store = answer_store or AnswerStore()
        self.survey_json = survey_json
        self.first_block_id = self.get_first_block_id()

    def build_path(self, blocks, block_id, path):
        """
        Recursive method which visits all the blocks and returns path taken
        given a list of answers

        :param blocks: A list containing all blocks in the survey
        :param block_id: The block id to visit
        :param path: The known path as a list which has been visited already
        :return: A list of block ids followed through the survey
        """
        if block_id in self.CLOSING_INTERSTITIAL_PATH:
            return path

        path.append(block_id)

        # Get blocks to be visited and a count of previous visits to this block in path
        block_ids = [index for (index, b) in enumerate(blocks) if b["id"] == block_id]
        no_of_previous_visits = path.count(block_id)

        # Return the index of the block id to be visited
        block_id_index = block_ids[no_of_previous_visits - 1]

        if 'routing_rules' in blocks[block_id_index] and len(blocks[block_id_index]['routing_rules']) > 0:
            for rule in blocks[block_id_index]['routing_rules']:
                if 'goto' in rule:
                    should_go = evaluate_goto(rule['goto'], self.answer_store)
                    if should_go is True:
                        return self.build_path(blocks, rule['goto']['id'], path)
                    elif should_go is False:
                        return path
        elif block_id_index != len(blocks) - 1:
            next_block_id = blocks[block_id_index + 1]['id']
            return self.build_path(blocks, next_block_id, path)
        return path

    def get_routing_path(self):
        """
        Returns a list of the block ids visited based on answers provided
        :return: List of block ids
        """
        routing_path = []
        blocks = self.get_blocks()

        return self.build_path(blocks, self.first_block_id, routing_path)

    def can_reach_summary(self, routing_path=None):
        """
        Determines whether the end of a given routing path can be reached given
        a set of answers
        :param routing_path:
        :return:
        """
        blocks = self.get_blocks()
        routing_path = routing_path or self.build_path(blocks, self.first_block_id, [])
        last_routing_block_id = routing_path[-1]

        if blocks[-1]['id'] == last_routing_block_id:
            return True

        routing_block_id_index = next(index for (index, b) in enumerate(blocks) if b["id"] == last_routing_block_id)

        last_routing_block = blocks[routing_block_id_index]

        if 'routing_rules' in last_routing_block:
            for rule in last_routing_block['routing_rules']:
                goto_rule = rule['goto']
                if 'id' in goto_rule.keys() and goto_rule['id'] == 'summary':
                    return evaluate_goto(goto_rule, self.answer_store)
        return False

    def get_location_path(self):
        """
        Returns a list of url locations visited based on answers provided
        :return:
        """
        blocks = self.get_blocks()
        routing_path = self.build_path(blocks, self.first_block_id, [])

        can_reach_summary = self.can_reach_summary(routing_path)

        # Make sure we don't update original
        location_path = list(Navigator.PRECEEDING_INTERSTITIAL_PATH)
        location_path.extend(routing_path)

        if can_reach_summary:
            location_path.extend(Navigator.CLOSING_INTERSTITIAL_PATH)

        return location_path

    def get_first_block_id(self):
        return self.survey_json['groups'][0]['blocks'][0]['id']

    def get_blocks(self):
        blocks = []
        for group in self.survey_json['groups']:
            group_blocks = [block for block in group['blocks']]
            blocks.extend(group_blocks)
            if 'routing_rules' in group:
                for rule in group['routing_rules']:
                    if 'repeat' in rule.keys():
                        no_of_times = evaluate_repeat(rule['repeat'], self.answer_store)
                        for i in range(no_of_times - 1):
                            blocks.extend(group_blocks)
        return blocks

    def block_in_path_count(self, block_id):
        blocks = [b['id'] for b in self.get_blocks()]

        return blocks.count(block_id)

    @classmethod
    def get_first_location(cls):
        return cls.PRECEEDING_INTERSTITIAL_PATH[0]

    def get_next_location(self, current_location_id=None, current_iteration=None):
        """
        Returns the next 'location' to visit given a set of user answers
        :param current_location_id:
        :param current_iteration:
        :return:
        """
        current_iteration = current_iteration or 0
        location_path = self.get_location_path()

        if current_location_id in location_path:

            # Get blocks to be visited
            block_ids = [index for (index, bid) in enumerate(location_path) if bid == current_location_id]

            # Return the index of the block id to be visited
            current_location_index = block_ids[current_iteration]

            if current_location_index < len(location_path) - 1:
                return location_path[current_location_index + 1]

    def get_previous_location(self, current_location_id=None, current_iteration=None):
        """
        Returns the next 'location' to visit given a set of user answers
        :param current_location_id:
        :param current_iteration:
        :return:
        """
        current_iteration = current_iteration or 0
        location_path = self.get_location_path()

        if current_location_id in location_path:
            # Get blocks to be visited
            block_ids = [index for (index, bid) in enumerate(location_path) if bid == current_location_id]

            # Return the index of the block id to be visited
            current_location_index = block_ids[current_iteration]

            if current_location_index != 0:
                return location_path[current_location_index - 1]

    def get_latest_location(self, completed_blocks=None):
        """
        Returns the latest 'location' based on the location path and previously completed blocks

        :param completed_blocks:
        :return:
        """
        if completed_blocks:
            incomplete_blocks = [item for item in self.get_location_path() if item not in completed_blocks]

            if incomplete_blocks:
                return incomplete_blocks[0]

        return self.get_first_location()