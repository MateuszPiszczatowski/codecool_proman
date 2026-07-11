"""PostgreSQL status queries module.

    Queries regarding statuses.
"""
from typing import Any
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


def get_status(status_id: int) -> Any:
    query: str = """
    SELECT title
    FROM statuses
    WHERE id = %(id)s
    """
    matching_status: Any = connection_manager.execute_select(query, {"id": status_id})

    return matching_status


def get_board_statuses(board_id: int) -> Any:
    query: str = """
    SELECT *
    FROM board_statuses AS bs
    LEFT JOIN statuses AS s ON s.id = bs.status_id
    WHERE bs.board_id = %(id)s
    """
    matching_statuses: Any = connection_manager.execute_select(query, {"id": board_id})

    return matching_statuses


def post_status(board_id: int, title: str) -> Any:
    query_select_status: str = """
    SELECT id FROM statuses
    WHERE title = %s
    """
    query_statuses: str = """
    INSERT INTO statuses (title)
    VALUES(
        %(title)s
    )
    RETURNING id
    """
    query_status_order: str = """
    SELECT
            (MAX(status_order) + 1) AS status_order
            FROM board_statuses
            WHERE board_id = %(board_id)s
            """
    query_board_statuses: str = """
    INSERT INTO board_statuses (status_id, board_id, status_order)
    VALUES (
        %(status_id)s, %(board_id)s, %(status_order)s
        
    )
    """
    status = connection_manager.execute_select(query_select_status, [title], False)
    status: Any = status if status is not None else connection_manager.execute_dml(query_statuses, {"title": title}, 'one')
    status_order = connection_manager.execute_select(query_status_order, variables={'board_id': board_id}, fetchall=False)
    connection_manager.execute_dml(query_board_statuses,
                                   {"status_id": status["id"], "board_id": board_id,
                              "status_order": status_order['status_order'] if status_order['status_order'] is not None else 1})
    return status


def patch_status(status_id: int, data: dict[str, Any]) -> None:
    query: str = """
        UPDATE statuses
        SET title = %(title)s
        WHERE id = %(id)s
        """
    data.update({"id": status_id})
    connection_manager.execute_dml(query, data)


def patch_status_order(status_id: int, data: dict[str, Any]) -> None:


    query: str = """
        UPDATE board_statuses
        SET status_order = %(status_order)s
        WHERE status_id = %(id)s
    """
    data.update({"id": status_id})
    connection_manager.execute_dml(query, data)


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
