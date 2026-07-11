"Database utility functions."
# pylint: disable=no-name-in-module, unused-import
# pyright: reportOptionalContextManager=false, reportOptionalSubscript=false
import os
from typing import Any
from psycopg2._psycopg import connection
from psycopg2.extras import RealDictCursor, RealDictRow
import psycopg2


def establish_connection(connection_data: dict[str, Any] | None=None) \
    -> connection | None:
    """
    Create a database connection based on the :connection_data: parameter
    :connection_data: Connection string attributes
    :returns: psycopg2.connection
    """
    if connection_data is None:
        connection_data = get_connection_data()
    try:
        # connect_str: str = f'postgresql://{user_name}:{password}@{host}/{database_name}
        connect_str: str = f"dbname={connection_data['dbname']}\
            user={connection_data['user']} host={connection_data['host']}\
            password={connection_data['password']}"
        conn: connection = psycopg2.connect(connect_str)
        conn.autocommit = True
    except psycopg2.DatabaseError as error:
        print("Cannot connect to database.")
        print(error)
    else:
        return conn


def get_connection_data(db_name: str | None=None) -> dict[str, Any] | None:
    """
    Give back a properly formatted dictionary based on the
    environment variables values which are started with :MY__PSQL_: prefix
    :db_name: optional parameter. By default it uses the 
    environment variable value.
    """
    if db_name is None:
        db_name = os.environ.get('MY_PSQL_DBNAME')

    return {
        'dbname': db_name,
        'user': os.environ.get('MY_PSQL_USER'),
        'host': os.environ.get('MY_PSQL_HOST'),
        'password': os.environ.get('MY_PSQL_PASSWORD')
    }


def execute_select(
        statement: str,
        variables: dict[str, Any] | list[Any] | None=None,
        fetchall: bool=True)\
        -> list[RealDictRow] | RealDictRow | None:
    """Execute SELECT sql statement, optionally parameterized.

    Parameters
    ----------
    statement : str
        SQL query
    variables : dict[str, Any] | None, optional
        safe query string formatting key: value pairs, by default None
        >>> execute_select('SELECT %(title)s; FROM shows',
            variables={'title': 'Codecool'})
    fetchall : bool, optional
        should the function return all records `True` or just one `False`,
        by default True

    Returns
    -------
    list[RealDictRow] | RealDictRow | None
        list of dictionary like objects or None
    """

    result_set: list[RealDictRow] | RealDictRow | None = []
    with establish_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(statement, variables)
            result_set = cursor.fetchall() if fetchall else cursor.fetchone()

    return result_set


def execute_dml(statement: str,
        variables: dict[str, Any] | list[Any],
        returning: Any = False)\
    -> RealDictRow | None:
    """Execute INSERT sql statement, optionally parameterized.

    Parameters
    ----------
    statement : str
        SQL query
    variables : dict[str, Any] | list[Any]
        safe query string formatting key: value pairs
        >>> execute_dml('INSERT INTO shows (title, score)
            VALUES (%(title)s, %(score)s)',
            variables={'title': 'Codecool', 'score': 6.9})
        >>> execute_dml('DELETE FROM shows \\
            WHERE title = %(title)s',
            variables={'title': 'Codenormie'})
        >>> execute_dml('UPDATE shows SET title = %s, \\
            genre = %s WHERE id = %s',
            variables=["How to exit vim?", "horror", 2137])
    returning : Any, optional
        if the query has a RETURNING statement,
        set to "All" for multiple results,
        set to "One" for single result,
        by default False = no results

    Returns
    -------
    RealDictRow | None
        dictionary like object or None
    """

    result: Any | None = None
    with establish_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(statement, variables)
            if returning is False:
                return result
            else:
                if returning.casefold() == "all":
                    result = cursor.fetchall()
                elif returning.casefold() == "one":
                    result = cursor.fetchone()
    return result