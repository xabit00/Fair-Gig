from collections.abc import Generator

from psycopg import Connection
from psycopg_pool import ConnectionPool

from .config import settings


pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=3,
    timeout=10,
    check=ConnectionPool.check_connection,
    open=False,
)


def get_connection() -> Generator[Connection, None, None]:
    with pool.connection() as connection:
        yield connection
