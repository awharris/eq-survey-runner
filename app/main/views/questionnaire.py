import logging

from app.authentication.session_manager import session_manager
from app.globals import get_answer_store, get_answers, get_completed_blocks, get_metadata, get_questionnaire_store
from app.questionnaire.navigator import Navigator
from app.questionnaire.questionnaire_manager import get_questionnaire_manager
from app.submitter.submitter import SubmitterFactory
from app.templating.introduction_context import get_introduction_context
from app.templating.metadata_context import build_metadata_context
from app.templating.schema_context import build_schema_context
from app.templating.summary_context import build_summary_rendering_context
from app.templating.template_renderer import renderer
from app.utilities.schema import get_schema

from flask import redirect
from flask import request
from flask import Blueprint
from flask import g
from flask import url_for

from flask_login import current_user
from flask_login import login_required

from flask_themes2 import render_theme_template


logger = logging.getLogger(__name__)


questionnaire_blueprint = Blueprint(name='questionnaire',
                                    import_name=__name__,
                                    url_prefix='/questionnaire/<eq_id>/<form_type>/<collection_id>/')


@questionnaire_blueprint.before_request
@login_required
def check_survey_state():
    g.schema_json, g.schema = get_schema()
    values = request.view_args

    if not _same_survey(values['eq_id'], values['form_type'], values['collection_id']):
        return redirect(url_for('root.information', message_identifier='multiple-surveys'))


@questionnaire_blueprint.after_request
def add_cache_control(response):
    response.cache_control.no_cache = True
    return response


@questionnaire_blueprint.route('<group_id>/<int:group_instance>/<block_id>', methods=["GET"])
@login_required
def get_block(eq_id, form_type, collection_id, group_id, group_instance, block_id):
    get_questionnaire_manager(g.schema, g.schema_json).build_state(block_id, get_answers(current_user))

    return _render_template(block_id, get_questionnaire_manager(g.schema, g.schema_json).state, template='questionnaire')


@questionnaire_blueprint.route('<group_id>/<int:group_instance>/<block_id>', methods=["POST"])
@login_required
def post_block(eq_id, form_type, collection_id, group_id, group_instance, block_id):
    navigator = Navigator(g.schema_json, get_answer_store(current_user))
    q_manager = get_questionnaire_manager(g.schema, g.schema_json)

    this_block = {
        'group_id': group_id,
        'group_instance': group_instance,
        'block_id': block_id,
    }

    valid_location = this_block in navigator.get_location_path()
    valid_data = q_manager.process_incoming_answers(this_block, request.form)

    if not valid_location or not valid_data:
        return _render_template(block_id, q_manager.state, template='questionnaire')

    next_location = navigator.get_next_location(current_group_id=group_id, current_iteration=group_instance, current_block_id=block_id)
    metadata = get_metadata(current_user)

    next_block_id = None if next_location is None else next_location['block_id']
    next_group_id = None if next_location is None else next_location['group_id']
    next_group_instance = None if next_location is None else next_location['group_instance']

    logger.info("Redirecting user to next location %s with tx_id=%s", str(next_location), metadata["tx_id"])

    return redirect_to_block(eq_id, form_type, collection_id, next_group_id, next_group_instance, next_block_id)


@questionnaire_blueprint.route('introduction', methods=["GET"])
@login_required
def get_introduction(eq_id, form_type, collection_id):
    metadata = get_metadata(current_user)
    answers = get_answers(current_user)
    schema_json = _render_schema(g.schema_json, answers, metadata)
    return _render_template('introduction', get_introduction_context(schema_json), rendered_schema_json=schema_json)


@questionnaire_blueprint.route('summary', methods=["GET"])
@login_required
def get_summary(eq_id, form_type, collection_id):
    navigator = Navigator(g.schema_json, get_answer_store(current_user))

    answer_store = get_answer_store(current_user)
    latest_location = navigator.get_latest_location(get_completed_blocks(current_user))

    if latest_location['block_id'] is 'summary':
        metadata = get_metadata(current_user)
        answers = get_answers(current_user)
        schema_json = _render_schema(g.schema_json, answers, metadata)
        summary_context = build_summary_rendering_context(schema_json, answer_store)
        return _render_template('summary', summary_context, rendered_schema_json=schema_json)

    return redirect_to_block(eq_id, form_type, collection_id, latest_location['group_id'], latest_location['group_instance'], latest_location['block_id'])


@questionnaire_blueprint.route('<location>', methods=["POST"])
@login_required
def post_interstitial(eq_id, form_type, collection_id, location):
    navigator = Navigator(g.schema_json, get_answer_store(current_user))
    q_manager = get_questionnaire_manager(g.schema, g.schema_json)

    this_block = {
        'block_id': location,
        'group_id': navigator.get_first_group_id(),
        'group_instance': 0,
    }

    valid_location = this_block in navigator.get_location_path()
    q_manager.process_incoming_answers(this_block, request.form)

    # Don't care if data is valid because there isn't any for interstitial
    if not valid_location:
        return _render_template(location, q_manager.state, template='questionnaire')

    next_location = navigator.get_next_location(current_block_id=location, current_iteration=0, current_group_id=this_block['group_id'])
    metadata = get_metadata(current_user)

    next_block_id = None if next_location is None else next_location['block_id']
    next_group_id = None if next_location is None else next_location['group_id']
    next_group_instance = None if next_location is None else next_location['group_instance']

    logger.info("Redirecting user to next location %s with tx_id=%s", str(next_location), metadata["tx_id"])

    return redirect_to_block(eq_id, form_type, collection_id, next_group_id, next_group_instance, next_block_id)


@questionnaire_blueprint.route('thank-you', methods=["GET"])
@login_required
def get_thank_you(eq_id, form_type, collection_id):
    if not _same_survey(eq_id, form_type, collection_id):
        return redirect("/information/multiple-surveys")

    thank_you_page = _render_template('thank-you', get_questionnaire_manager(g.schema, g.schema_json).state)
    # Delete user data on request of thank you page.
    _delete_user_data()
    return thank_you_page


@questionnaire_blueprint.route('submit-answers', methods=["POST"])
@login_required
def submit_answers(eq_id, form_type, collection_id):
    q_manager = get_questionnaire_manager(g.schema, g.schema_json)
    # check that all the answers we have are valid before submitting the data
    is_valid, invalid_location = q_manager.validate_all_answers()

    if is_valid:
        submitter = SubmitterFactory.get_submitter()
        submitter.send_answers(get_metadata(current_user), g.schema, get_answers(current_user))
        return redirect_to_thank_you(eq_id, form_type, collection_id)
    else:
        return redirect_to_block(eq_id, form_type, collection_id,
                                 invalid_location['group_id'],
                                 invalid_location['group_instance'],
                                 invalid_location['block_id'])


def _delete_user_data():
    get_questionnaire_store(current_user.user_id, current_user.user_ik).delete()
    session_manager.clear()


def redirect_to_introduction(eq_id, form_type, collection_id):
    return redirect(url_for('.get_introduction',
                            eq_id=eq_id,
                            form_type=form_type,
                            collection_id=collection_id,
                            ))


def redirect_to_summary(eq_id, form_type, collection_id):
    return redirect(url_for('.get_summary',
                            eq_id=eq_id,
                            form_type=form_type,
                            collection_id=collection_id))


def redirect_to_thank_you(eq_id, form_type, collection_id):
    return redirect(url_for('.get_thank_you',
                            eq_id=eq_id,
                            form_type=form_type,
                            collection_id=collection_id))


def redirect_to_block(eq_id, form_type, collection_id, group_id, group_instance, block_id):
    if block_id == 'summary':
        return redirect_to_summary(eq_id, form_type, collection_id)
    elif block_id == 'introduction':
        return redirect_to_introduction(eq_id, form_type, collection_id)
    elif block_id == 'thank-you':
        return redirect_to_thank_you(eq_id, form_type, collection_id)

    return redirect(url_for('.get_block',
                            eq_id=eq_id,
                            form_type=form_type,
                            collection_id=collection_id,
                            group_id=group_id,
                            group_instance=group_instance,
                            block_id=block_id))


def _same_survey(eq_id, form_type, collection_id):
    metadata = get_metadata(current_user)
    current_survey = eq_id + form_type + collection_id
    metadata_survey = metadata["eq_id"] + metadata["form_type"] + metadata["collection_exercise_sid"]
    return current_survey == metadata_survey


def _render_template(location, context, rendered_schema_json=None, template=None):
    metadata = get_metadata(current_user)
    answers = get_answers(current_user)
    metadata_context = build_metadata_context(metadata)
    navigator = Navigator(g.schema_json, get_answer_store(current_user))
    previous_location = navigator.get_previous_location(current_block_id=location)
    schema_json = rendered_schema_json or _render_schema(g.schema_json, answers, metadata)

    previous_location = None if previous_location is None else previous_location['block_id']

    try:
        theme = schema_json['theme']
        logger.debug("Theme selected: {} ".format(theme))
    except KeyError:
        logger.info("No theme set ")
        theme = None

    template = '{}.html'.format(template or location)

    return render_theme_template(theme, template, meta=metadata_context,
                                 content=context,
                                 previous_location=previous_location,
                                 schema=schema_json)


def _render_schema(schema_json, answers, metadata):
    schema_context = build_schema_context(metadata, g.schema.aliases, answers)
    return renderer.render(schema_json, **schema_context)
