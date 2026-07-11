"""PostgreSQL card queries module.

    Queries regarding
"""
from typing import Any
import data_manager


def get_all_cards_public_board(board_id: int) -> Any:
    """Gather all cards for a specified board.

    Parameters
    ----------
    board_id : int

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT c.*
        FROM cards AS c
        LEFT JOIN boards AS b ON b.id = c.board_id
        WHERE c.board_id = %(id)s
        AND b.is_private = FALSE
        """
    matching_cards: Any = data_manager.execute_select(query,
                                                      {"id": board_id})

    return matching_cards


def get_card_public_board(board_id: int, card_id: int) -> Any:
    """Gather specified card for a specified board.

    Parameters
    ----------
    board_id : int

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT c.*
        FROM cards AS c
        LEFT JOIN boards AS b ON b.id = c.board_id
        WHERE c.board_id = %(board_id)s
        AND c.id = %(card_id)s
        AND b.is_private = FALSE
        """
    matching_card: Any = data_manager.execute_select(query,
                                                     {"board_id": board_id, "card_id": card_id})

    return matching_card


def get_all_cards_user_public_board(user_id: int, board_id: int) -> Any:
    """Gather all cards for a specified user board.

    Parameters
    ----------
    user_id : int
        id of parent user
    board_id : int
        id of parent board

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT c.*
        FROM cards AS c
        LEFT JOIN user_boards AS ub ON ub.board_id = c.board_id
        LEFT JOIN boards AS b ON b.id = c.board_id
        WHERE b.is_private = FALSE
        AND ub.user_id = %(user_id)s
        AND b.id = %(board_id)s
        """
    matching_cards: Any = data_manager.execute_select(query,
                                                      {"user_id": user_id, "board_id": board_id})

    return matching_cards


def get_card_user_public_board(user_id: int, board_id: int, card_id: int) -> Any:
    """Gather specified card for a specified user board.

    Parameters
    ----------
    user_id : int
        id of parent user
    board_id : int
        id of parent board
    card_id : int
        id of requested card

    Returns
    -------
    Any
        JSON object
    """

    query: str = """
        SELECT c.*
        FROM cards AS c
        LEFT JOIN user_boards AS ub ON ub.board_id = c.board_id
        LEFT JOIN boards AS b ON b.id = c.board_id
        WHERE b.is_private = FALSE
        AND ub.user_id = %(user_id)s
        AND b.id = %(board_id)s
        AND c.id = %(card_id)s
        """
    matching_card: Any = data_manager.execute_select(query,
                                                     {"user_id": user_id, "board_id": board_id, "card_id": card_id})

    return matching_card


def delete_card(card_id: int) -> None:
    query: str = """
        DELETE FROM cards
        WHERE id = %(id)s
    """
    data_manager.execute_dml(query, {"id": card_id})


def patch_card(card_id: int, data: dict[str, Any]) -> None:
    allowed_keys = {'title', 'body'}
    update_data = {k: v for k, v in data.items() if k in allowed_keys}
    
    if not update_data:
        return
        
    set_clause = ", ".join([f"{k} = %({k})s" for k in update_data.keys()])
    
    query: str = f"""
        UPDATE cards 
        SET {set_clause}
        WHERE id = %(id)s
    """
    
    update_data["id"] = card_id
    data_manager.execute_dml(query, update_data)


def patch_card_order(card_id: int, data: dict[str, Any]) -> None:
    allowed_keys = {'card_order', 'status_id'}
    update_data = {k: v for k, v in data.items() if k in allowed_keys}
    
    if not update_data:
        return
        
    set_clause = ", ".join([f"{k} = %({k})s" for k in update_data.keys()])
    
    query: str = f"""
        UPDATE cards
        SET {set_clause}
        WHERE id = %(id)s
    """
    
    update_data["id"] = card_id
    data_manager.execute_dml(query, update_data)


def post_card(board_id: int, status_id: int, title: str) -> Any:
    query_order: str = """
    SELECT
                (MAX(card_order) + 1) as card_order
                FROM cards
                WHERE board_id = %(board_id)s
                """
    query_cards: str = """
        INSERT INTO cards (board_id, status_id, title, body, card_order)
        VALUES (
            %s, %s, %s, '', %s
        )
        RETURNING *
        """
    card_order = data_manager.execute_select(query_order, variables={'board_id': board_id}, fetchall=False)
    return data_manager.execute_dml(query_cards,
                                    [board_id, status_id, title,
                                     card_order['card_order'] if card_order['card_order'] else 1], 'one')
