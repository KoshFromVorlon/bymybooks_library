import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()


def run_migration():
    """
    Adds the 'last_location' column to the 'books' table in PostgreSQL.
    This column will store the EPUB Reading System location string (CFI).
    """
    # Using the DATABASE_URL configured for your Render instance
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("Error: DATABASE_URL not found in .env file.")
        return

    try:
        # Establish connection to the PostgreSQL server
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Execute the schema update
        print("Migrating: Adding 'last_location' column to 'books' table...")
        cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS last_location VARCHAR;")

        # Finalize the transaction
        conn.commit()
        cursor.close()
        conn.close()
        print("Success: Database schema updated.")

    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    run_migration()