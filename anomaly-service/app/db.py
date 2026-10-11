from contextlib import contextmanager
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings


pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=3,
    kwargs={"row_factory": dict_row},
    open=False,
)


@contextmanager
def get_connection():
    with pool.connection() as conn:
        yield conn

