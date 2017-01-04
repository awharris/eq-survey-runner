import logging

from app.authentication.authenticator import Authenticator

from app.globals import get_answer_store, get_completed_blocks, get_metadata
from app.questionnaire.navigator import Navigator
from app.utilities.schema import get_schema

from flask import redirect
from flask import request
from flask import session
from flask import Blueprint

from flask_login import current_user

from werkzeug.exceptions import NotFound

logger = logging.getLogger(__name__)


session_blueprint = Blueprint('session', __name__)


@session_blueprint.after_request
def add_cache_control(response):
    response.cache_control.no_cache = True
    return response


@session_blueprint.route('/session', methods=['GET'])
def login():
    """
    Initial url processing - expects a token parameter and then will authenticate this token. Once authenticated
    it will be placed in the users session
    :return: a 302 redirect to the next location for the user
    """

    # logging in again clears any session state
    if session:
        session.clear()

    authenticator = Authenticator()
    logger.debug("Attempting token authentication")

    authenticator.jwt_login(request)
    logger.debug("Token authenticated - linking to session")

    metadata = get_metadata(current_user)

    eq_id = metadata["eq_id"]
    form_type = metadata["form_type"]

    logger.debug("Requested questionnaire %s for form type %s", eq_id, form_type)

    if not eq_id or not form_type:
        logger.error("Missing EQ id %s or form type %s in JWT", eq_id, form_type)
        raise NotFound

    json, _ = get_schema(metadata)

    navigator = Navigator(json, metadata, get_answer_store(current_user))
    current_location = navigator.get_latest_location(get_completed_blocks(current_user))

    return redirect(current_location.url(metadata))