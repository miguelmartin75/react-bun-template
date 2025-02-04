"""
this is an example python script to populate a SQLite DB,
which is then used in JS/TS with a bun backend
"""

import sqlite3
from dataclasses import dataclass

from scripts.db import DbCtx, uniq, pk, create_db_metadata

@dataclass
class Sample:
    id: int = pk()
    path: str = None
    annotation: dict = None
    tags: list[str] = None

Tables = [Sample]
TablesMetadata = create_db_metadata(Tables)

samples = [
    Sample(
        path="https://i.imgur.com/ZVsTgFW.mp4",
        annotation={
            "captions": ["It said edible!"],
        },

    ),
    Sample(
        path="https://i.imgur.com/ZVsTgFW.mp4",
        annotation={
            "questions": ["What TV show is this video from?"],
            "answers": ["The Simpsons"],
            "captions": ["Interrupt dumping"],
        },

    ),
    Sample(
        path="https://i.imgur.com/2QF3yfo.mp4",
        annotation={
            "captions": ["so little yet so fiesty"],
        },
    ),
    Sample(
        path="https://www.youtube.com/watch?v=CiZO38P_3Y8",
        annotation={
            "captions": ["hello world"],
        },
    ),
]

ctx = DbCtx("dataset.sqlite3", tables_meta=TablesMetadata)
ctx.create_tables_if_dne()

ctx.insert_many(samples, upsert=True, get_pk=True)
