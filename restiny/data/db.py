from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from restiny.data.sql import SQL_DIR


class DBManager:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionMaker = sessionmaker(
            bind=self.engine, autoflush=True, expire_on_commit=False
        )

        @event.listens_for(self.engine, 'connect')
        def _set_sqlite_pragmas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

    @contextmanager
    def session_scope(self):
        session = self.SessionMaker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def run_migrations(self) -> None:
        version_in_db = self._get_version()

        for sql_script in sorted(
            SQL_DIR.glob('[0-9]*_*.sql'),
            key=lambda path: int(path.stem.split('_', 1)[0]),
        ):
            version_in_script = int(sql_script.stem.split('_', 1)[0])
            if version_in_script <= version_in_db:
                continue

            self._run_migration(
                sql_migration=sql_script.read_text(encoding='utf-8'),
                new_version=version_in_script,
            )

    def _run_migration(self, sql_migration: str, new_version: int) -> None:
        with self.session_scope() as session:
            raw = session.connection().connection
            raw.executescript(sql_migration)
            raw.execute(f'PRAGMA user_version = {new_version}')

    def _get_version(self) -> int:
        with self.session_scope() as session:
            result = session.execute(text('PRAGMA user_version'))
            return int(result.scalar_one()) or 0
