from collections.abc import Generator

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings


pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=8,
    kwargs={"row_factory": dict_row},
    check=ConnectionPool.check_connection,
    open=False,
)


def get_connection() -> Generator[Connection, None, None]:
    with pool.connection() as connection:
        yield connection
