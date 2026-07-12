"""PostgreSQL data handling package.
Provides a unified interface to access specific database handlers.

Example
-------
Use this package as a main reference point for database operations:
    >>> import data_handler as dh
And then reference specific tables/logic:
    >>> dh.cards.<function_name>()
    >>> dh.boards.<function_name>()
"""

from . import card_handler as cards
from . import board_handler as boards
from . import user_handler as users
from . import status_handler as status
from . import connection_manager

__all__ = ['cards', 'boards', 'users', 'status', 'connection_manager']