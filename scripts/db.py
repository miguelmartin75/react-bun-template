import json
import sqlite3
from collections import defaultdict
from dataclasses import fields, field
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, Dict


DEFAULT_DATE_FORMAT_STR: str = "%Y-%m-%d %H:%M:%S"

def pk():
    return field(metadata={"pk": True}, default=None)

def uniq():
    return field(metadata={"uniq": True}, default=None)

def is_pk(f):
    return f.metadata.get("pk")

def is_uniq(f):
    return f.metadata.get("uniq")

def get_pk(x):
    for f in fields(x):
        if is_pk(f):
            return f
    return None

def _get_cols(x, tables_meta):
    cols = {}
    for f in fields(x):
        if f.type in tables_meta:
            cols[f] = {
                "name": f.name + "_" + tables_meta[f.type]["pk"].name,
                "type": tables_meta[f.type]["pk"].type,
                "is_pk": is_pk(f),
                "is_uniq": is_uniq(f),
                "is_fk": True,
            }
        else:
            cols[f] = {
                "name": f.name,
                "type": f.type,
                "is_pk": is_pk(f),
                "is_uniq": is_uniq(f),
                "is_fk": False,
            }
    return cols


def create_db_metadata(tables):
    result = {
        x: {"pk": get_pk(x)}
        for x in tables
    }
    for x in tables:
        result[x]["cols"] = _get_cols(x, result)
    return result

def _encode_field_sqlite(value: Any, field, field_col_meta, tables_meta) -> Any:  # pyre-ignore
    name = field_col_meta["name"]
    datatype = field.type
    if field_col_meta["is_fk"]:
        pk_field_name = tables_meta[datatype]["pk"].name
        return getattr(value, pk_field_name)
    else:
        if value is None:
            return None
        elif datatype in (list, dict, defaultdict):
            # TODO: recursive
            return json.dumps(value)
        elif datatype == datetime:
            assert isinstance(
                value, datetime
            ), f"{name} class: {value.__class__}, expected: datetime"
            return int(value.replace(tzinfo=timezone.utc).timestamp())
        elif isinstance(value, Fraction):
            assert datatype == float
            return float(value)
        else:  # catch-all for otherwise
            assert isinstance(
                value, (str, float, int, bool)
            ), f"{name} class: {value.__class__}, expected: (bool, float, int, str)"
            return value

def encode_dataclass_sqlite(x: Any, tables_meta) -> Dict[str, Any]:  # pyre-ignore
    assert x.__class__ in tables_meta
    result = tuple(
        _encode_field_sqlite(
            x.__dict__[f.name],
            f,
            meta,
            tables_meta,
        )
        for f, meta in tables_meta[x.__class__]["cols"].items()
    )
    return result

def pytype_to_sqlitetype(x):
    if x in (int, bool, datetime):
        return "INTEGER"
    elif x == float:
        return "REAL"
    elif x == str:
        return "TEXT"
    elif x in (list, dict, defaultdict):
        return "BLOB"
    else:
        return ""

def row_dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

class DbCtx:
    def __init__(self, db_shard, tables_meta=None):
        self.tables_meta = tables_meta
        self.db_shard = db_shard
        self.con = sqlite3.connect(db_shard)
        self.con.row_factory = row_dict_factory

    def __exit__(self):
        self.con.close()

    def query_all_dict(self, query: str):
        cur = self.con.execute(query)
        return list(cur)

    def insert_many(self, xs, get_pk=False, upsert=False, debug=False):
        clazz = xs[0].__class__
        assert clazz in self.tables_meta

        pk_field_name = self.tables_meta[clazz]["pk"].name

        serialized = [encode_dataclass_sqlite(x, self.tables_meta) for x in xs]
        query = "INSERT "
        query += f"INTO {clazz.__name__} VALUES\n"
        query += "(" + ",".join(["?" for _ in serialized[0]]) + ")\n"
        if upsert:
            cols = self.tables_meta[clazz]["cols"]
            query += f"ON CONFLICT DO UPDATE SET "
            for i, meta in enumerate(cols.values()):
                query += f"{meta['name']}=excluded.{meta['name']}"
                if i + 1 < len(cols):
                    query += ", "

        if get_pk:
            query += f"\nRETURNING {pk_field_name}"
        if debug:
            print(query)
        if get_pk:
            for x, sx in zip(xs, serialized):
                cur = self.con.execute(query, sx)
                temp = cur.fetchone()
                pk_val = temp[pk_field_name]
                assert pk_val is not None, f"{pk_field_name} is None - perhaps you need to mark this as type int?"
                setattr(x, pk_field_name, pk_val)
            self.con.commit()
        else:
            cur = self.con.executemany(query, serialized)
            self.con.commit()

    def insert(self, x, get_pk=False, upsert=False):
        self.insert_many([x], get_pk=get_pk, upsert=upsert)

    def create_tables_if_dne(self):
        for query in self._create_tables_queries_if_dne():
            self.con.execute(query)
        return self.con.commit()

    def _create_tables_queries_if_dne(self):
        result = []
        for clazz, meta in self.tables_meta.items():
            create_table_query = f"CREATE TABLE IF NOT EXISTS {clazz.__name__}"
            create_table_query += "("  # )
            cols = meta["cols"]
            for i, (f, col) in enumerate(cols.items()):
                create_table_query += col["name"] 
                create_table_query += " "
                create_table_query += pytype_to_sqlitetype(col["type"])
                if col["is_pk"]:
                    create_table_query += " PRIMARY KEY"
                elif col["is_uniq"]:
                    create_table_query += " UNIQUE"
                if i + 1 < len(cols):
                    create_table_query += ", "
            create_table_query += ")"
            result.append(create_table_query)
        return result
