import hashlib
import sqlite3
from pathlib import Path


class TranslationCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS translations (
                cache_key TEXT PRIMARY KEY, translation TEXT NOT NULL
            )""")

    def _connect(self):
        return sqlite3.connect(self.path)

    @staticmethod
    def make_key(text: str, source: str, target: str, provider_version: str = "v1") -> str:
        raw = "\0".join((text.strip(), source, target, provider_version))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT translation FROM translations WHERE cache_key=?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, translation: str) -> None:
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO translations VALUES (?, ?)", (key, translation))
