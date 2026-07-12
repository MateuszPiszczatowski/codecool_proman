"""PostgreSQL users queries module.

    Queries regarding users.
"""
import datetime

import bcrypt
from typing import Any
from psycopg2.extras import RealDictRow
from . import connection_manager
from util import regex_validate

VALIDATION_REGEXS: dict[str] = {'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9])(?=.{8,}).*$',
                                'username': r'^[a-zA-Z0-9]{3,}$',
                                'email': r'^[a-zA-Z0-9\.]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+$'}


def check_if_user_exists(username: str | None = None, email: str | None = None) -> bool:
    """Check if user with provided data exists

    Parameters
    ----------
    username : str
        username of searched user

    email: str
        e-mail address of searched user

    Returns
    -------
    bool
    """
    username_user_id = None
    email_user_id = None
    if username:
        user = get_user_by_username(username)
        if user:
            username_user_id = user['id']
        else:
            return False
    if email:
        user = get_user_by_email(email)
        if user:
            email_user_id = user['id']
        else:
            return False
    if username and email:
        if username_user_id == email_user_id:
            return True
        else:
            return False
    return True

def validate_registration_data(user: dict[str, Any]) -> dict[str, Any]:
    """Check if the provided registration data fulfill registration criteria.

    Parameters
    ----------
    user : dict[Any]
        dictionary containing registration information

    Returns
    -------
    Any
        JSON object
    """
    response: dict[str | bool, str] = {'success': True, 'message': ''}
    # Check if user already exists
    if get_user_by_email(user['email']):
        response['success'] = False
        response['message'] = 'User with given e-mail address already exists!'
    if response['success']:
        if get_user_by_username(user['username']):
            response['success'] = False
            response['message'] = 'User with given username already exists!'
    # Check if provided data are in proper format
    if response['success']:
        for key in VALIDATION_REGEXS:
            if not regex_validate(VALIDATION_REGEXS[key], user[key]):
                response['success'] = False
                response['message'] += ('\n' if response['message'] == '' else '') + \
                                       f'Improper {key} value'
    # If validation process was successful set the message accordingly
    if response['success']:
        response['message'] = f'Everything went OK, user {user["username"]} has been registered!'
    return response


def register_new_user(user: dict[str, Any]) -> dict[str, Any]:
    """Register new user if provided data is correct.

    Parameters
    ----------
    user : dict[Any]
        dictionary containing registration information

    Returns
    -------
    Any
        JSON object
    """
    response: dict[str | bool, str] = validate_registration_data(user)
    if response['success']:
        user['password'] = bcrypt.hashpw(user['password'].encode('UTF-8'), bcrypt.gensalt()).decode()
        user['registration_date'] = datetime.datetime.utcnow()
        try:
            db_response = connection_manager.execute_dml("""
            INSERT INTO users (username, first_name, last_name, registration_date, password, email) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *;""", [user['username'], user['first_name'], user['last_name'], user['registration_date'],
                              user['password'],
                              user['email']],
                                                   'one')
            if db_response is None:
                response['success'] = False
                response['message'] = 'An error occurred during communication with the database.'
        except ValueError:
            response['success'] = False
            response['message'] = 'An error occurred during communication with the database'
    return response


def validate_login(login_data: dict[str, Any]) -> dict[str, Any]:
    """Validate login information.

    Parameters
    ----------
    login_data : dict[str]
        dictionary containing login information

    Returns
    -------
    Any
        JSON object
    """
    email = login_data['email']
    password = login_data['password'].encode('UTF-8')
    user = get_user_by_email(email)
    if user:
        if bcrypt.checkpw(password, user['password'].encode()):
            return {'success': True, 'message': f'Successfully logged in as {user["username"]}'}
        else:
            return {'success': False, 'message': 'Wrong password'}
    else:
        return {'success': False, 'message': 'No user with such e-mail address'}


def get_all_users() -> list[RealDictRow] | None:
    """Gather all users list.

    Returns
    -------
    Any
        JSON object
    """
    query: str = """
        SELECT id, username, first_name AS name, last_name AS surname,
            registration_date AS registered
        FROM users
        """
    users = connection_manager.execute_select(query)

    return users


def get_user(user_id: int) -> RealDictRow | None:
    """Gather specified user profile.

    Parameters
    ----------
    user_id : int
        id of specified users
    
    Returns
    -------
    Any
        JSON object
    """
    query: str = """
        SELECT id, username, first_name AS name, last_name AS surname, email,
            registration_date AS registered
        FROM users
        WHERE id = %(id)s
        """
    user = connection_manager.execute_select(query, {"id": user_id}, fetchall=False)

    return user


def get_user_by_username(username: str) -> RealDictRow | None:
    query: str = """
    SELECT id, username
    FROM users
    WHERE username = %(username)s
    """
    user = connection_manager.execute_select(query, {"username": username}, fetchall=False)

    return user


def check_permission(username: str, board_id: int = 0) -> bool:
    """
    Check if user is allowed to modify or delete the board.
    Grants permission if the board is public, or if the board
    is private and the user is its owner.

    Parameters
    ----------
    username : str
        Username of the user attempting the action
    board_id : int, optional
        ID of the board to check, by default 0

    Returns
    -------
    bool
        True if user is allowed to modify the board, False otherwise
    """
    if board_id <= 0:
        return False

    query: str = """
        SELECT EXISTS (
            SELECT 1
            FROM boards b
            LEFT JOIN user_boards ub ON b.id = ub.board_id
            LEFT JOIN users u ON u.id = ub.user_id
            WHERE b.id = %(board_id)s
            AND (b.is_private = FALSE OR u.username = %(username)s)
        ) AS is_allowed;
    """
    
    result = connection_manager.execute_select(query, {"board_id": board_id, "username": username}, fetchall=False)
    
    if result:
        return result['is_allowed']
    return False


def get_user_by_email(user_email: str) -> RealDictRow | None:
    """Gather specified user profile.

    Parameters
    ----------
    user_email : str
        e-mail address of specified user

    Returns
    -------
    Any
        JSON object
    """
    query: str = """
        SELECT id, username, first_name AS name, last_name AS surname, email,
            registration_date AS registered, password
        FROM users
        WHERE email = %(email)s
        """
    user = connection_manager.execute_select(query, {"email": user_email}, fetchall=False)

    return user
