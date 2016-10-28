import logging

from app.templating.metadata_template_preprocessor import MetaDataTemplatePreprocessor

logger = logging.getLogger(__name__)


class QuestionnaireTemplatePreprocessor(object):

    def build_view_data(self, schema, state_items, previous_location):

        metadata_template_preprocessor = MetaDataTemplatePreprocessor()
        render_data = {
            "meta": metadata_template_preprocessor.build_metadata(schema),
            "content": state_items[0],
            "previous_location": previous_location,
        }

        logger.debug("Rendering data is %s", render_data)

        return render_data
