"Python server file containing routes and responses."
# pylint: disable=unused-import
import sys
from typing import Any
import uuid
import re
import mimetypes
from flask import Flask, flash, render_template, url_for, request, redirect
from flask import session, abort
from flask.typing import ResponseReturnValue
import dotenv
import os

from util import json_response
import data_handler as dh

dotenv.load_dotenv()

mimetypes.add_type('application/javascript', '.js')
app: Flask = Flask(__name__, static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1000 * 1000

app.secret_key = os.environ.get('FLASK_SECRET_KEY')


@app.route("/", \
           methods=["GET"])
def index() -> str:
    """Root route which displays all boards and cards.

    Methods
    -------
    get

    Returns
    -------
    str
        Renders index.html page
    """
    user = None
    logged_in = False
    if 'username' in session:
        if dh.users.check_if_user_exists(username=session['username']):
            user = dh.users.get_user_by_username(session['username'])[0]
            logged_in = True
        else:
            session.pop('username')
    return render_template('pages/index.html', logged_in=logged_in, user=user)


@app.route("/register", \
           methods=["POST"])
@json_response
def registration() -> Any:
    """Route to register a new user to database.

    Methods
    -------
    post
        save new user record into database

    Returns
    -------
    Any : bool
        confirmation on user registration
    """

    fields: list[str] = ["username", "first_name", "last_name", "email", "password"]
    new_user: dict[Any] = {}
    for item in fields:
        new_user[item] = request.json[item]
    return dh.users.register_new_user(new_user)


@app.route("/login", \
           methods=["POST"])
@json_response
def login() -> ResponseReturnValue:
    """Route for logging in a user and creating session.

    Methods
    -------
    post

    Returns
    -------
    ResponseReturnValue : dict[bool, str]
        JSON object
    """
    response = dh.users.validate_login(request.json)
    if response['success']:
        user = dh.users.get_user_by_email(request.json['email'])[0]
        session['username'] = user['username']
    return response


@app.route("/logout", \
           methods=["GET"])
def logout() -> ResponseReturnValue:
    """Route for logging out an user and clearing session data.

    Methods
    -------
    get

    Returns
    -------
    ResponseReturnValue
        redirection to home page
    """

    session.pop('username', None)
    return redirect(url_for("index"))


@app.route("/api/boards", \
           methods=["GET", "POST"])
@json_response
def public_boards() -> ResponseReturnValue:
    """Route for retrieving or creating public boards.

    Methods
    -------
    get
        retrieve all public boards
    post
        save a new record into boards database without owner info

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method == "POST":
        published_board = request.json
        if published_board.get('is_private'):
            if session.get('username'):
                if not dh.users.check_if_user_exists(username=session.get('username')):
                    return {'success': False, 'message': f"Couldn't find user {session.get('username')}"}
                user = dh.users.get_user_by_username(session.get('username'))[0]
                add_board_result = dh.boards.post_private_board(published_board['title'], user['id'])
                return {'success': True,
                        'message': f"Successfully added private board {add_board_result['title']} for user {user['username']}"}
            else:
                return {'success': False, 'message': 'Cannot add private board if not logged in!'}
        else:
            if session.get('username'):
                if dh.users.check_if_user_exists(username=session.get('username')):
                    user = dh.users.get_user_by_username(session.get('username'))[0]
                    dh.boards.post_public_board(published_board['title'], user['id'])
                    return {'success': True,
                            'message': f"Successfully added public board {published_board['title']} for user {user['username']}"}
                else:
                    return {'success': False,
                            'message': f"Request sent as logged in user: {session.get('username')}, but there is no such user"}
            else:
                dh.boards.post_public_board(published_board['title'])
                return {'success': True,
                        'message': f"Successfully added public board {published_board['title']} without owner"}
    else:
        username = session.get('username')
        if username is not None:
            if dh.users.check_if_user_exists(username=username):
                user = dh.users.get_user_by_username(username)[0]
                return dh.boards.get_all_user_accessible_boards(user['id'])
            else:
                session.pop('username')
        return dh.boards.get_all_public_boards()


@app.route("/api/boards/<int:board_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def public_board(board_id: int) -> ResponseReturnValue | None:
    """Get specified board from the database, change its property or delete
    entire record.

    Methods
    -------
    get, patch, delete

    Parameters
    ----------
    board_id : int
        id of the requested board

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """
    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            dh.boards.patch_board(board_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.boards.delete_board(board_id)
    else:
        return dh.boards.get_public_board(board_id)


@app.route("/api/users/<int:user_id>/boards", \
           methods=["GET"])
@json_response
def user_public_boards(user_id: int) -> ResponseReturnValue | None:
    """Get all boards owned by specified user from the database

    Method
    -------
    get

    Parameters
    ----------
    user_id : int
        id of the parent user

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    """
    return dh.boards.get_all_user_public_boards(user_id)


@app.route("/api/users/<int:user_id>/boards/<int:board_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def user_public_board(user_id: int, board_id: int) -> ResponseReturnValue | None:
    """Get specified board owned by specified user from the database, change
    it's property or delete entirely if the user is allowed to.

    Methods
    -------
    get, patch, delete

    Parameters
    ----------
    user_id : int
        id of the parent user
    board_id : int
        id of the requested board

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            dh.boards.patch_board(board_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.boards.delete_board(board_id)
    else:
        return dh.boards.get_user_public_board(user_id, board_id)


@app.route("/api/boards/<int:board_id>/cards", \
           methods=["GET", "POST"])
@json_response
def cards_public_board(board_id: int) -> ResponseReturnValue | None:
    """Get all cards belonging to specified public board from the database or
    create new card.

    Methods
    -------
    get, post

    Parameters
    ----------
    board_id : int
        id of parent board

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method == "POST":
        data: Any = request.json
        card = dh.cards.post_card(board_id, data["status_id"], data["title"])
        if card:
            return {'success': True, 'card': card}
        else:
            return {'success': False, 'message': "Couldn't add the card"}
    else:
        return dh.cards.get_all_cards_public_board(board_id)


@app.route("/api/boards/<int:board_id>/cards/<int:card_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def card_public_board(board_id: int, card_id: int) -> ResponseReturnValue | None:
    """Get specified card for a specified board from the database, change it's
    property or delete entire record.

    Methods
    -------
    get, patch, delete

    Parameters
    ----------
    board_id : int
        id of parent board
    card_id : int
        id of specified card

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            if "card_order" in data.keys():
                dh.cards.patch_card_order(card_id, data)
            else:
                dh.cards.patch_card(card_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.cards.delete_card(card_id)
    else:
        return dh.cards.get_card_public_board(board_id, card_id)


@app.route("/api/users/<int:user_id>/boards/<int:board_id>/cards", \
           methods=["GET", "POST"])
@json_response
def cards_user_public_board(
        user_id: int, board_id: int) -> ResponseReturnValue | None:
    """Get all cards belonging to specified user board from the database or
    create a new card on a private board.

    Methods
    -------
    get, post

    Parameters
    ----------
    user_id : int
        id of parent user
    board_id : int
        id of parent board

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method == "POST":
        data: Any = request.json
        dh.cards.post_card(board_id, data["status_id"], data["title"])
        flash(f"card {data['title']} created succesfuly!", "message")
    else:
        return dh.cards.get_all_cards_user_public_board(user_id, board_id)


@app.route("/api/users/<int:user_id>/boards/<int:board_id>/cards/<int:card_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def card_user_public_board(
        user_id: int, board_id: int, card_id: int) -> ResponseReturnValue | None:
    """Get all cards belonging to the specified user board from the database,
    change it's property or delete entire record.

    Methods
    -------
    get, patch, delete

    Parameters
    ----------
    user_id : int
        id of the parent user
    board_id : int
        id of the parent board
    card_id : int
        id of the requested card

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            dh.cards.patch_card(card_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.cards.delete_card(card_id)
    else:
        return dh.cards.get_card_user_public_board(
            user_id, board_id, card_id)


@app.route("/api/boards/<int:board_id>/statuses", \
           methods=["GET", "POST"])
@json_response
def statuses_public_board(board_id: int) -> ResponseReturnValue | None:
    if request.method == "POST":
        data: Any = request.json
        result: Any = dh.status.post_status(board_id, data["title"])
        flash(f"status {data['title']} created succesfuly!", "message")
        return result
    else:
        return dh.status.get_board_statuses(board_id)


@app.route("/api/boards/<int:board_id>/statuses/<int:status_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def status_public_board(board_id: int, status_id: int
                        ) -> ResponseReturnValue | None:
    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            if "status_order" in data.keys():
                dh.status.patch_status_order(status_id, data)
            else:
                dh.status.patch_status(status_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.status.delete_status(board_id, status_id)
    else:
        return dh.status.get_status(status_id)


@app.route("/api/users/<int:user_id>/boards/<int:board_id>/cards", \
           methods=["GET", "POST"])
@json_response
def statuses_user_public_board(board_id: int) -> ResponseReturnValue | None:
    if request.method == "POST":
        data: Any = request.json
        dh.status.post_status(board_id, data["title"])
        flash(f"status {data['title']} created succesfuly!", "message")
    else:
        return dh.status.get_board_statuses(board_id)


@app.route("/api/users/<int:user_id>/boards/<int:board_id>/statuses/<int:status_id>", \
           methods=["GET", "PATCH", "DELETE"])
@json_response
def status_user_public_board(board_id: int, status_id: int
                             ) -> ResponseReturnValue | None:
    if request.method != "GET":
        user: str = session.get("username", '')
        is_allowed: bool = dh.users.check_permission(user, board_id)
        if request.method == "PATCH" and is_allowed:
            data: Any = request.json
            dh.status.patch_status(status_id, data)
        if request.method == "DELETE" and is_allowed:
            dh.status.delete_status(board_id, status_id)
    else:
        return dh.status.get_status(status_id)


@app.route("/api/users", \
           methods=["GET", "POST"])
@json_response
def users() -> ResponseReturnValue | None:
    """Get all users from the database.

    Methods
    -------
    get, post

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    return dh.users.get_all_users()


@app.route("/api/users/<int:user_id>", \
           methods=["GET"])
@json_response
def get_user(user_id: int) -> ResponseReturnValue | None:
    """Get specified user profile from database.

    Methods
    -------
    get

    Parameters
    ----------
    user_id : int
        id of specified user

    Returns
    -------
    ResponseReturnValue : dict[str, ...]
        JSON object
    None
        flashed message
    """

    return dh.users.get_user(user_id)


def main() -> None:
    """Starts flask server listening on localhost:5000
    """

    app.run(debug=True, host='0.0.0.0', port=5000)

    # Serving the favicon
    with app.app_context():
        app.add_url_rule('/favicon.ico', redirect_to=url_for(
            'static', filename='favicon/favicon.ico'))


if __name__ == '__main__':
    main()
