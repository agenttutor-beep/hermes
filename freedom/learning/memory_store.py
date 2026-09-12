#!/usr/bin/env python3

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "memory" / "freedom.db"


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    db.executescript("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT,
        source_type TEXT,
        retrieved_at TEXT NOT NULL,
        content TEXT,
        UNIQUE(url)
    );

    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        claim TEXT NOT NULL,
        evidence TEXT NOT NULL,
        confidence REAL DEFAULT 0.5,
        created_at TEXT NOT NULL,
        FOREIGN KEY(source_id) REFERENCES sources(id)
    );

    CREATE TABLE IF NOT EXISTS beliefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statement TEXT NOT NULL,
        confidence REAL DEFAULT 0.5,
        status TEXT DEFAULT 'tentative',
        reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson TEXT NOT NULL,
        context TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        priority REAL DEFAULT 0.5,
        status TEXT DEFAULT 'open',
        created_at TEXT NOT NULL
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS memory_search USING fts5(
        kind,
        text,
        source,
        content=''
    );
    """)

    return db


def remember_lesson(lesson, context=""):
    db = connect()
    t = now()

    db.execute(
        "INSERT INTO lessons (lesson, context, created_at) VALUES (?, ?, ?)",
        (lesson, context, t)
    )

    db.execute(
        "INSERT INTO memory_search (kind, text, source) VALUES (?, ?, ?)",
        ("lesson", lesson, context)
    )

    db.commit()
    db.close()


def ask_question(question, priority=0.5):
    db = connect()
    t = now()

    db.execute(
        "INSERT INTO questions (question, priority, created_at) VALUES (?, ?, ?)",
        (question, priority, t)
    )

    db.execute(
        "INSERT INTO memory_search (kind, text, source) VALUES (?, ?, ?)",
        ("question", question, "self-generated")
    )

    db.commit()
    db.close()


def remember_belief(statement, confidence=0.5, reason=""):
    db = connect()
    t = now()

    db.execute(
        """
        INSERT INTO beliefs
        (statement, confidence, status, reason, created_at, updated_at)
        VALUES (?, ?, 'tentative', ?, ?, ?)
        """,
        (statement, confidence, reason, t, t)
    )

    db.execute(
        "INSERT INTO memory_search (kind, text, source) VALUES (?, ?, ?)",
        ("belief", statement, reason)
    )

    db.commit()
    db.close()


def search_memory(query, limit=10):
    db = connect()

    rows = db.execute(
        """
        SELECT kind, text, source
        FROM memory_search
        WHERE memory_search MATCH ?
        LIMIT ?
        """,
        (query, limit)
    ).fetchall()

    db.close()
    return rows


if __name__ == "__main__":
    db = connect()
    db.close()

    print(f"Freedom memory initialized: {DB}")
