from app.schema.widgets.multiple_choice_widget import MultipleChoiceWidget

from app.libs.utils import ObjectFromDict


class CheckboxGroupWidget(MultipleChoiceWidget):
    def __init__(self, name):
        super().__init__(name)
        self.type = 'checkbox'

    def get_user_input(self, post_vars):
        # Returns an empty list
        return post_vars.getlist(self.name)

    def _build_options(self, answer_schema, answer_state):
        options = []

        if answer_schema.options:
            for option in answer_schema.options:
                option_selected = False
                if answer_state.input:
                    option_selected = option['value'] in answer_state.input
                options.append(ObjectFromDict({
                    'value': option['value'],
                    'label': option['label'],
                    'selected': option_selected,
                    'other': option['other'] if 'other' in option else None
                }))

        return options
