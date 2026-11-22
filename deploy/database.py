import os

import psycopg


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10)


if __name__ == "__main__":
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mango_predictions (
                id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                created_at timestamptz NOT NULL DEFAULT now(),
                variety text NOT NULL,
                confidence double precision NOT NULL CHECK (confidence BETWEEN 0 AND 1)
            )
        """)
