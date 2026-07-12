"""PostgreSQL board queries module.

    Queries regarding boards.
"""
from typing import Any

from psycopg2.extras import RealDictRow

from . import connection_manager
from . import status_handler as sh


def get_all_public_boards() -> list[RealDictRow] | None:
    """Gather all public boards.

    Returns
    -------
    list[RealDictRow] | None
        list of board dictionaries
    """

    query: str = """
        SELECT *
        FROM boards
        WHERE is_private = FALSE
        """
    public_boards = connection_manager.execute_select(query)

    return public_boards


def get_all_user_accessible_boards(user_id: int) -> list[RealDictRow] | None:
    """
    Gather all boards that are accessible for specific user

    Parameters
    ----------
    user_id : int

    Returns
    -------
    list[RealDictRow] | None
        list of board dictionaries
    """
    query: str = """
        SELECT DISTINCT boards.id, boards.title, boards.is_private
        FROM boards
        LEFT JOIN user_boards
        ON user_boards.board_id = boards.id
        WHERE is_private = FALSE
        OR (is_private = TRUE AND user_id = %s)
        ORDER BY boards.id
    """
    return connection_manager.execute_select(query, [user_id])


def get_public_board(board_id: int) -> RealDictRow | None:
    """Gather public board with specified id.

    Parameters
    ----------
    board_id : int

    Returns
    -------
    RealDictRow | None
        single board dictionary
    """

    query: str = """
        SELECT *
        FROM boards
        WHERE id = %(id)s
        AND is_private = FALSE
        """
    public_board = connection_manager.execute_select(query, {"id": board_id}, False)

    return public_board


def get_all_user_public_boards(user_id: int) -> list[RealDictRow] | None:
    """Gather all public boards for a specified user.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    list[RealDictRow] | None
        list of board dictionaries
    """

    query: str = """
        SELECT b.*
        FROM boards AS b
        LEFT JOIN user_boards AS ub ON b.id = ub.board_id
        WHERE is_private = FALSE
        AND ub.user_id = %(id)s
        """
    public_boards = connection_manager.execute_select(query, {"id": user_id})

    return public_boards


def get_user_public_board(user_id: int, board_id: int) -> RealDictRow | None:
    """Gather specified public board for a specified user.

    Parameters
    ----------
    user_id : int
    board_id : int

    Returns
    -------
    RealDictRow | None
        single board dictionary
    """

    query: str = """
        SELECT b.*
        FROM boards AS b
        LEFT JOIN user_boards AS ub ON b.id = ub.board_id
        WHERE b.is_private = FALSE
        AND ub.user_id = %(user_id)s
        AND b.id = %(board_id)s
        """
    public_board = connection_manager.execute_select(query,
                                                          {"user_id": user_id, "board_id": board_id}, False)

    return public_board


def post_public_board(title: str, owner_id: int = 0) -> RealDictRow | None:
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
            '{"owner"}'
        )
        """
    board = connection_manager.execute_dml(query_boards, {"title": title}, 'one')
    if not board:
        return None
    if owner_id and owner_id > 0:
        connection_manager.execute_dml(query_user_boards, {"id": board['id'], "owner_id": owner_id})
    sh.add_default_statuses(board['id'])
    return board


def post_private_board(title: str, owner_id: int) -> RealDictRow | None:
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
    board = connection_manager.execute_dml(query_boards,
                                                {"title": title}, 'one')
    if not board:
        return None
    connection_manager.execute_dml(query_user_boards,
                                   {"id": board['id'], "owner_id": owner_id})
    sh.add_default_statuses(board['id'])
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

    query_cards: str = """
    DELETE FROM cards
    WHERE board_id = %(board_id)s
    """
    connection_manager.execute_dml(query_cards, {"board_id": board_id})
    deleted_statuses = connection_manager.execute_dml(query_board_statuses, {"board_id": board_id}, "all")
    
    if deleted_statuses:
        status_ids = tuple(row['status_id'] for row in deleted_statuses)
        query_cleanup: str = """
        DELETE FROM statuses
        WHERE id IN %(status_ids)s
        AND id NOT IN (SELECT status_id FROM board_statuses)
        """
        connection_manager.execute_dml(query_cleanup, {"status_ids": status_ids})

    connection_manager.execute_dml(query_user_boards, {"board_id": board_id})
    connection_manager.execute_dml(query_boards, {"board_id": board_id})


def patch_board(board_id: int, data: dict[str, Any]) -> None:
    query: str = """
        UPDATE boards
        SET title = %(title)s, is_private = %(is_private)s
        WHERE id = %(id)s
        """
    variables = {**data, "id": board_id}
    connection_manager.execute_dml(query, variables)
