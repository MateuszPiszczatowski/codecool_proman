"""PostgreSQL board queries module.

    Queries regarding boards.
"""
import sys
from typing import Any
from functools import reduce
import data_manager
import data_handler.main_handler as dh


def get_all_public_boards() -> Any:
    """Gather all public boards.

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT *
        FROM boards
        WHERE is_private = FALSE
        """
    public_boards: Any = data_manager.execute_select(query)

    return public_boards


def get_all_user_accessible_boards(user_id: int) -> Any:
    """
    Gather all boards that are accessible for specific user

    Parameters
    ----------
    user_id : int

    Returns
    -------
    Any
        JSON object
    """
    query: str = """
        SELECT boards.id, boards.title, boards.is_private
        FROM boards
        LEFT JOIN user_boards
        ON user_boards.board_id = boards.id
        WHERE is_private = FALSE
        OR (is_private = TRUE AND user_id = %s)
        ORDER BY boards.id
    """
    return data_manager.execute_select(query, [user_id])


def get_public_board(board_id: int) -> Any:
    """Gather public board with specified id.

    Parameters
    ----------
    board_id : int

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT *
        FROM boards
        WHERE id = %(id)s
        AND is_private = FALSE
        """
    public_board: Any = data_manager.execute_select(query, {"id": board_id}, False)

    return public_board


def get_all_user_public_boards(user_id: int) -> Any:
    """Gather all public boards for a specified user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT b.*
        FROM boards AS b
        LEFT JOIN user_boards AS ub ON b.id = ub.board_id
        WHERE is_private = FALSE
        AND ub.user_id = %(id)s
        """
    public_boards: Any = data_manager.execute_select(query, {"id": user_id})

    return public_boards


def get_user_public_board(user_id: int, board_id: int) -> Any:
    """Gather specified public board for a specified user.

    Parameters
    ----------
    user_id : int
    board_id : int

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT b.*
        FROM boards AS b
        LEFT JOIN user_boards AS ub ON b.id = ub.board_id
        WHERE b.is_private = FALSE
        AND ub.user_id = %(user_id)s
        AND b.id = %(board_id)s
        """
    public_board: Any = data_manager.execute_select(query,
                                                    {"user_id": user_id, "board_id": board_id}, False)

    return public_board


def post_public_board(title: str, owner_id: int = 0) -> None:
    """Create new public board.

    Parameters
    ----------
    title : str
        new board title
    owner_id : int, optional
        if >0 binds the board to the specified user, by default 0
    """

    query_boards: str = """
        INSERT INTO boards (title)
        VALUES (
            %(title)s
        )
        RETURNING *
        """
    query_user_boards: str = """
        INSERT INTO user_boards (board_id, user_id, user_role)
        VALUES (
            %(id)s,
            %(owner_id)s,
            '{"owner_id"}'
        )
        """
    board: Any = data_manager.execute_dml(query_boards, {"title": title}, 'one')
    if owner_id > 0:
        data_manager.execute_dml(query_user_boards, {"id": board['id'], "owner_id": owner_id})
    dh.status.add_default_statuses(board['id'])
    return board


def post_private_board(title: str, owner_id: int) -> Any | None:
    """Create new private board.

    Parameters
    ----------
    title : str
        new board title
    owner_id : int
        user to bind board to
    """

    query_boards: str = """
        INSERT INTO boards (title, is_private)
        VALUES (
            %(title)s, TRUE
        )
        RETURNING *
        """
    query_user_boards: str = """
        INSERT INTO user_boards (board_id, user_id, user_role)
        VALUES (
            %(id)s,
            %(owner_id)s,
            '{"owner"}'
        )
        """
    board: Any = data_manager.execute_dml(query_boards,
                                          {"title": title}, 'one')
    data_manager.execute_dml(query_user_boards,
                             {"id": board['id'], "owner_id": owner_id})
    dh.status.add_default_statuses(board['id'])
    return board


def delete_board(board_id: int) -> None:
    query_boards: str = """
    DELETE FROM boards
    WHERE id = %(board_id)s
    """
    query_user_boards: str = """
    DELETE FROM user_boards
    WHERE board_id = %(board_id)s
    """
    query_board_statuses: str = """
    DELETE FROM board_statuses
    WHERE board_id = %(board_id)s
    RETURNING status_id"""

    query_statuses: str = """
    DELETE FROM statuses
    WHERE id = %(status_id)s"""

    query_cards: str = """
    DELETE FROM cards
    WHERE board_id = %(board_id)s
    """
    data_manager.execute_dml(query_cards, {"board_id": board_id})
    statuses_to_remove: Any = data_manager.execute_dml(query_board_statuses,
                                                       {"board_id": board_id}, "All")
    print(statuses_to_remove, file=sys.stderr)
    for status in statuses_to_remove:
        data_manager.execute_dml(query_statuses, {"status_id": int(status["status_id"])})
    data_manager.execute_dml(query_user_boards,
                             {"board_id": board_id})
    data_manager.execute_dml(query_boards, {"board_id": board_id})


def patch_board(board_id: int, data: dict[str, Any]) -> None:
    query: str = """
        UPDATE boards
        SET title = %(title)s, is_private = %(is_private)s
        WHERE id = %(id)s
        """
    data_manager.execute_dml(query, data)
