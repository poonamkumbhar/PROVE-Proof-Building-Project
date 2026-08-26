import json
import sqlite3    # SQLite stores the proof artifacts in a local database file.
import uuid       # Generate a unique ID for every saved proof artifact.
from pathlib import Path

DATABASE_PATH = Path("data/proof_builder.db")  # Path to store SQLite database

def initialize_database():
    # Create the data folder if it does not already exist.
    #
    # `parents=True` creates missing parent folders.
    # `exist_ok=True` prevents an error if the folder already exists.
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Open a connection to the SQLite database.
    # SQLite automatically creates the database file if it does not exist.
    #
    # `with` automatically closes the connection after the work is completed.
    with sqlite3.connect(DATABASE_PATH) as connection:

        # Create the proof_artifacts table if it does not already exist.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS proof_artifacts (
                id TEXT PRIMARY KEY,
                artifact_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_artifact(artifact):
    initialize_database()  
    artifact_id = str(uuid.uuid4())                        # Generate a unique ID for the new proof artifact.
    with sqlite3.connect(DATABASE_PATH) as connection:    # Open the database connection.
         # Insert the artifact ID and JSON data into the database.
         # json.dumps converts the artifact dictionary into JSON text.`ensure_ascii=False` preserves normal Unicode characters.
        connection.execute(
            "INSERT INTO proof_artifacts (id, artifact_json) VALUES (?, ?)",
            (artifact_id, json.dumps(artifact, ensure_ascii=False)),
        )

     # Return the generated ID so it can be added to the final result.
    return artifact_id

