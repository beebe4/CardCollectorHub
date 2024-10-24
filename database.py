import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import time

class Database:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.conn = None
        self.connect()
        
    def connect(self):
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                self.conn = psycopg2.connect(
                    dbname=os.environ['PGDATABASE'],
                    user=os.environ['PGUSER'],
                    password=os.environ['PGPASSWORD'],
                    host=os.environ['PGHOST'],
                    port=os.environ['PGPORT']
                )
                self.create_tables()
                return
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                    
        raise Exception(f"Failed to connect to database after {self.max_retries} attempts. Last error: {last_error}")

    def ensure_connection(self):
        try:
            # Try to execute a simple query to test the connection
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # If the connection is dead, reconnect
            self.connect()

    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS decks (
                    id SERIAL PRIMARY KEY,
                    deck_name VARCHAR(255) NOT NULL,
                    manufacturer VARCHAR(255) NOT NULL,
                    release_year INTEGER,
                    condition VARCHAR(50),
                    purchase_date DATE,
                    purchase_price DECIMAL(10,2),
                    notes TEXT,
                    image_data BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def add_deck(self, deck_data, image_data=None):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO decks (deck_name, manufacturer, release_year, condition,
                                     purchase_date, purchase_price, notes, image_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    deck_data['deck_name'], deck_data['manufacturer'],
                    deck_data['release_year'], deck_data['condition'],
                    deck_data['purchase_date'], deck_data['purchase_price'],
                    deck_data['notes'], image_data
                ))
                self.conn.commit()
                return cur.fetchone()[0]
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Database error: {str(e)}")

    def get_all_decks(self):
        self.ensure_connection()
        try:
            return pd.read_sql("""
                SELECT * FROM decks 
                ORDER BY created_at DESC
            """, self.conn)
        except Exception as e:
            raise Exception(f"Failed to fetch decks: {str(e)}")

    def get_deck_image(self, deck_id):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT image_data FROM decks WHERE id = %s", (deck_id,))
                result = cur.fetchone()
                return result[0] if result else None
            except Exception as e:
                raise Exception(f"Failed to fetch deck image: {str(e)}")

    def search_decks(self, query):
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("""
                    SELECT * FROM decks 
                    WHERE deck_name ILIKE %s 
                    OR manufacturer ILIKE %s
                    OR notes ILIKE %s
                """, (f'%{query}%', f'%{query}%', f'%{query}%'))
                return cur.fetchall()
            except Exception as e:
                raise Exception(f"Search failed: {str(e)}")

db = Database()
