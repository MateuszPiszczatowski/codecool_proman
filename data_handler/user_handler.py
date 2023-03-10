"""PostgreSQL users queries module.

    Queries regarding users.
"""
import datetime

import bcrypt
from typing import Any
import data_manager
from util import regex_validate

VALIDATION_REGEXS: dict[str] = {'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9])(?=.{8,}).*$',
                                'username': r'^[a-zA-Z0-9]{3,}$',
                                'email': r'^[a-zA-Z0-9\.]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+$'}


def validate_registration_data(user: dict[Any]) -> dict[str | bool, str]:
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
    if len(get_user_by_email(user['email'])) != 0:
        response['success'] = False
        response['message'] = 'User with given e-mail address already exists!'
    if response['success']:
        if len(get_user_by_username(user['username'])) != 0:
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


def register_new_user(user: dict[Any]) -> dict[str | bool, str]:
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
            db_response = data_manager.execute_insert("""
            INSERT INTO users (username, first_name, last_name, registration_date, password, email) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *;""", [user['username'], user['first_name'], user['last_name'], user['registration_date'],
                              user['password'],
                              user['email']],
                                                      True)
            if db_response is None:
                response['success'] = False
                response['message'] = 'An error occured during communication with the database: ' + db_response
        except ValueError:
            response['success'] = False
            response['message'] = 'An error occured during communication with the database'
    return response


def validate_login(login_data: dict[str]):
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
    print(email)
    password = login_data['password'].encode('UTF-8')
    user = get_user_by_email(email)
    if len(user) > 0:
        user = user[0]
        if bcrypt.checkpw(password, user['password'].encode()):
            return {'success': True, 'message': f'Successfully logged in as {user["username"]}'}
        else:
            return {'success': False, 'message': 'Wrong password'}
    else:
        return {'success': False, 'message': 'No user with such e-mail address'}


def get_all_users() -> Any:
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
    users: Any = data_manager.execute_select(query)

    return users


def get_user(user_id: int) -> Any:
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
    user: Any = data_manager.execute_select(query, {"id": user_id})

    return user


def get_user_by_username(username: str) -> Any:
    query: str = """
    SELECT id, username
    FROM users
    WHERE username = %(username)s
    """
    user: Any = data_manager.execute_select(query, {"username": username})

    return user


def check_permission(user: str, board_id: int = 0) -> bool:
    # if user and board_id > 0:
    #     return True
    # return False
    return True


def get_user_by_email(user_email: str) -> Any:
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
    user: Any = data_manager.execute_select(query, {"email": user_email})

    return user
