"Database utility functions."
# pylint: disable=no-name-in-module, unused-import
# pyright: reportOptionalContextManager=false, reportOptionalSubscript=false
import os
from typing import Any, Literal
from psycopg2._psycopg import connection
from psycopg2.extras import RealDictCursor, RealDictRow
import psycopg2
from psycopg2.pool import SimpleConnectionPool

_pool: SimpleConnectionPool | None = None
def _init_pool(connection_data: dict[str, Any] | None=None) -> None:
    global _pool
    if connection_data is None:
        connection_data = get_connection_data()
    try:
        _pool = SimpleConnectionPool(1, 10, **connection_data)
    except psycopg2.DatabaseError as error:
        print("Cannot connect to database.")
        raise error

def get_connection(connection_data: dict[str, Any] | None=None) -> connection:
    """Gets and returns opened connection from the pool."""
    global _pool
    if _pool is None:
        _init_pool(connection_data)
    assert _pool is not None
    conn: connection = _pool.getconn()
    conn.autocommit = True
    return conn


def get_connection_data(db_name: str | None=None) -> dict[str, Any]:
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
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(statement, variables)
            return cursor.fetchall() if fetchall else cursor.fetchone()
    finally:
        assert _pool is not None
        _pool.putconn(conn)


def execute_dml(statement: str,
        variables: dict[str, Any] | list[Any],
        returning: Literal['all', 'one'] | None = None)\
    -> list[RealDictRow] | RealDictRow | None:
    """Execute INSERT/UPDATE/DELETE sql statement, optionally parameterized.

    Parameters
    ----------
    statement : str
        SQL query
    variables : dict[str, Any] | list[Any]
        safe query string formatting key: value pairs
        >>> execute_dml('INSERT INTO shows (title, score) VALUES(%(title)s, %(score)s)',
        variables={'title': 'Codecool', 'score': 6.9})
    returning : Literal['all', 'one'] | None, optional
        if the query has a RETURNING statement,
        set to "all" for multiple results,
        set to "one" for single result,
        by default None = no results

    Returns
    -------
    list[RealDictRow] | RealDictRow | None
        dictionary like object, list of objects, or None
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(statement, variables)
            if returning is not None:
                if returning.casefold() == "all":
                    return cursor.fetchall()
                elif returning.casefold() == "one":
                    return cursor.fetchone()
            return None
    finally:
        assert _pool is not None
        _pool.putconn(conn)