"""Private SQLite objects and a hash-linked, append-only event journal."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .schema import canonical, content_hash, require


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        private = self.root / ".local"
        require(not private.is_symlink(), "unsafe_storage_path", "storage")
        private.mkdir(mode=0o700, exist_ok=True)
        os.chmod(private, 0o700)
        self.path = private / "reviews.sqlite3"
        require(not self.path.is_symlink(), "unsafe_storage_path", "storage")
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        os.chmod(self.path, 0o600)
        db = self.connect()
        try:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS objects(ref TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, body TEXT NOT NULL, hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS head(singleton INTEGER PRIMARY KEY CHECK(singleton=1), seq INTEGER NOT NULL, hash TEXT NOT NULL);
                INSERT OR IGNORE INTO head VALUES(1,0,'');
                CREATE TRIGGER IF NOT EXISTS objects_no_update BEFORE UPDATE ON objects BEGIN SELECT RAISE(ABORT,'immutable object'); END;
                CREATE TRIGGER IF NOT EXISTS objects_no_delete BEFORE DELETE ON objects BEGIN SELECT RAISE(ABORT,'immutable object'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
            ''')
        finally:
            db.close()

    def connect(self):
        return sqlite3.connect(self.path, timeout=5, isolation_level=None)

    def verify(self, db):
        objects = {}
        for ref, body in db.execute("SELECT ref,body FROM objects"):
            value = json.loads(body)
            require(content_hash(value) == ref, "object_tampered", "storage")
            objects[ref] = value
        previous = ""
        count = 0
        for seq, body, digest in db.execute("SELECT seq,body,hash FROM events ORDER BY seq"):
            event = json.loads(body)
            count += 1
            require(seq == count and event["seq"] == seq and event["previous"] == previous
                    and content_hash(event) == digest, "event_tampered", "storage")
            require(all(ref in objects for ref in event["refs"]), "missing_reference", "storage")
            previous = digest
        require(db.execute("SELECT seq,hash FROM head WHERE singleton=1").fetchone() == (count, previous),
                "journal_head_mismatch", "storage")
        return count

    @contextmanager
    def transaction(self, expected=None):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            version = self.verify(db)
            require(expected is None or expected == version, "concurrent_change", "version")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def put(self, db, value):
        ref = content_hash(value)
        body = canonical(value).decode()
        old = db.execute("SELECT body FROM objects WHERE ref=?", (ref,)).fetchone()
        require(old is None or old[0] == body, "object_identity_collision", "storage")
        db.execute("INSERT OR IGNORE INTO objects VALUES(?,?)", (ref, body))
        return ref

    def get(self, db, ref):
        row = db.execute("SELECT body FROM objects WHERE ref=?", (ref,)).fetchone()
        require(row is not None, "missing_reference", "storage")
        value = json.loads(row[0])
        require(content_hash(value) == ref, "object_tampered", "storage")
        return value

    def events(self, db):
        return [json.loads(row[0]) for row in db.execute("SELECT body FROM events ORDER BY seq")]

    def append(self, db, kind, actor, data, refs=()):
        require(type(actor) is str and bool(actor.strip()), "reviewer_required", "actor")
        seq, previous = db.execute("SELECT seq,hash FROM head WHERE singleton=1").fetchone()
        event = dict(seq=seq + 1, previous=previous, kind=kind, actor=actor,
                     identity="self_declared_unverified", at=utc_now(), data=data, refs=list(refs))
        digest = content_hash(event)
        db.execute("INSERT INTO events VALUES(?,?,?)", (seq + 1, canonical(event).decode(), digest))
        db.execute("UPDATE head SET seq=?,hash=? WHERE singleton=1", (seq + 1, digest))
        return event

    def version(self):
        with self.transaction() as db:
            return self.verify(db)
