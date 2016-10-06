from app.libs.utils import ObjectFromDict
from app.schema.widgets.multiple_choice_widget import MultipleChoiceWidget


class RadioGroupWidget(MultipleChoiceWidget):
    def __init__(self, name):
        super().__init__(name)
        self.type = 'radio'

    def _build_options(self, answer_schema, answer_state):
        options = []

        if answer_schema.options:
            for option in answer_schema.options:
                options.append(ObjectFromDict({
                    'value': option['value'],
                    'label': option['label'],
                    'selected': option['value'] == answer_state.input,
                    'other': option['other'] if 'other' in option else None,
                    'othervalue': answer_state.other if hasattr(answer_state, 'other') else None,
                }))

        return options
