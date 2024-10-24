import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            host=os.environ['PGHOST'],
            port=os.environ['PGPORT']
        )
        self.create_tables()

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
        with self.conn.cursor() as cur:
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

    def get_all_decks(self):
        return pd.read_sql("SELECT * FROM decks ORDER BY created_at DESC", self.conn)

    def get_deck_image(self, deck_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT image_data FROM decks WHERE id = %s", (deck_id,))
            return cur.fetchone()[0]

    def search_decks(self, query):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM decks 
                WHERE deck_name ILIKE %s 
                OR manufacturer ILIKE %s
                OR notes ILIKE %s
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            return cur.fetchall()

db = Database()
