"""PostgreSQL status queries module.

    Queries regarding statuses.
"""
from typing import Any

from psycopg2.extras import RealDictRow

from . import connection_manager

DEFAULT_STATUSES = ['new', 'in progress', 'testing', 'done']


def add_default_statuses(board_id: int) -> None:
    """
        Add default statuses to a board

    Parameters
    ----------
    board_id : int
        id of the board to add the statuses to
    """
    for status in DEFAULT_STATUSES:
        post_status(board_id, status)


def get_status(status_id: int) -> RealDictRow | None:
    query: str = """
        SELECT title
        FROM statuses
        WHERE id = %(id)s
    """
    matching_status: Any = connection_manager.execute_select(query, {"id": status_id}, fetchall=False)

    return matching_status


def get_board_statuses(board_id: int) -> list[RealDictRow]:
    query: str = """
        SELECT *
        FROM board_statuses AS bs
        LEFT JOIN statuses AS s ON s.id = bs.status_id
        WHERE bs.board_id = %(id)s
    """
    matching_statuses: Any = connection_manager.execute_select(query, {"id": board_id})

    return matching_statuses


def post_status(board_id: int, title: str) -> RealDictRow | None:
    query_statuses: str = """
        INSERT INTO statuses (title)
        VALUES (%(title)s)
        RETURNING id
    """
    query_status_order: str = """
        SELECT (MAX(status_order) + 1) AS status_order 
        FROM board_statuses
        WHERE board_id = %(board_id)s
    """
    query_board_statuses: str = """
        INSERT INTO board_statuses (status_id, board_id, status_order)
        VALUES (%(status_id)s, %(board_id)s, %(status_order)s)
    """
    status = connection_manager.execute_dml(query_statuses, {"title": title}, 'one')
    if not status or isinstance(status,list):
        return None
    status_order = 1
    status_order_result = connection_manager.execute_select(query_status_order, variables={'board_id': board_id}, fetchall=False)
    if status_order_result and status_order_result.get('status_order'):
        status_order = status_order_result['status_order']
    connection_manager.execute_dml(query_board_statuses, {"status_id": status["id"], "board_id": board_id,
                                                          "status_order": status_order})
    return status


def patch_status(status_id: int, data: dict[str, Any]) -> None:
    query: str = """
        UPDATE statuses
        SET title = %(title)s
        WHERE id = %(id)s
    """
    variables = {**data, "id": status_id}
    connection_manager.execute_dml(query, variables)


def patch_status_order(status_id: int, data: dict[str, Any]) -> None:


    query: str = """
        UPDATE board_statuses
        SET status_order = %(status_order)s
        WHERE status_id = %(id)s
    """
    variables = {**data, "id": status_id}
    connection_manager.execute_dml(query, variables)


def delete_status(board_id: int, status_id: int) -> None:
    query_statuses: str = """
        DELETE FROM statuses
        WHERE id = %(status_id)s
    """
    query_board_statuses: str = """
        DELETE FROM board_statuses
        WHERE status_id = %(status_id)s
        AND board_id = %(board_id)s
    """
    query_cards: str = """
        DELETE FROM cards
        WHERE status_id = %(status_id)s
    """
    connection_manager.execute_dml(query_cards, {"status_id": status_id})
    connection_manager.execute_dml(query_board_statuses,
                                   {"status_id": status_id, "board_id": board_id})
    connection_manager.execute_dml(query_statuses, {"status_id": status_id})
