import sqlite_utils

def get_db(db_path="rgf.db", schema_path="schema.sql"):
    """
    Returns a sqlite_utils.Database instance and ensures the schema is loaded.
    """
    db = sqlite_utils.Database(db_path)
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    db.conn.executescript(schema_sql)
    return db