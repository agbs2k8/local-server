import datetime
from typing import Optional
from pydantic import BaseModel
import psycopg


def write_to_db(conn: psycopg.Connection, table: str, data: dict):
    columns = ', '.join(data.keys())
    values = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
    with conn.cursor() as cur:
        cur.execute(query, tuple(data.values()))
    conn.commit()