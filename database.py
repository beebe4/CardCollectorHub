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
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self.connect()

    def create_tables(self):
        with self.conn.cursor() as cur:
            # Create decks table
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
            
            # Create wishlist table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wishlist (
                    id SERIAL PRIMARY KEY,
                    deck_name VARCHAR(255) NOT NULL,
                    manufacturer VARCHAR(255) NOT NULL,
                    expected_price DECIMAL(10,2),
                    priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create market values table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_values (
                    id SERIAL PRIMARY KEY,
                    deck_id INTEGER REFERENCES decks(id),
                    market_price DECIMAL(10,2) NOT NULL,
                    source VARCHAR(255),
                    condition VARCHAR(50),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    UNIQUE(deck_id, source)
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

    def update_market_value(self, deck_id, market_data):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO market_values (deck_id, market_price, source, condition, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (deck_id, source)
                    DO UPDATE SET
                        market_price = EXCLUDED.market_price,
                        condition = EXCLUDED.condition,
                        notes = EXCLUDED.notes,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    deck_id,
                    market_data['market_price'],
                    market_data['source'],
                    market_data['condition'],
                    market_data.get('notes', '')
                ))
                self.conn.commit()
                return cur.fetchone()[0]
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Failed to update market value: {str(e)}")

    def get_market_values(self, deck_id=None):
        self.ensure_connection()
        try:
            query = """
                SELECT mv.*, d.deck_name, d.manufacturer, d.condition as deck_condition, d.purchase_price
                FROM market_values mv
                JOIN decks d ON mv.deck_id = d.id
            """
            params = []
            if deck_id:
                query += " WHERE mv.deck_id = %s"
                params.append(deck_id)
            query += " ORDER BY mv.updated_at DESC"
            
            return pd.read_sql(query, self.conn, params=params)
        except Exception as e:
            raise Exception(f"Failed to fetch market values: {str(e)}")

    def add_to_wishlist(self, wishlist_data):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO wishlist (deck_name, manufacturer, expected_price, priority, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    wishlist_data['deck_name'], wishlist_data['manufacturer'],
                    wishlist_data['expected_price'], wishlist_data['priority'],
                    wishlist_data['notes']
                ))
                self.conn.commit()
                return cur.fetchone()[0]
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Database error: {str(e)}")

    def remove_from_wishlist(self, wishlist_id):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM wishlist WHERE id = %s", (wishlist_id,))
                self.conn.commit()
                return True
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Failed to remove from wishlist: {str(e)}")

    def get_all_decks(self):
        self.ensure_connection()
        try:
            return pd.read_sql("""
                SELECT * FROM decks 
                ORDER BY created_at DESC
            """, self.conn)
        except Exception as e:
            raise Exception(f"Failed to fetch decks: {str(e)}")

    def get_wishlist(self):
        self.ensure_connection()
        try:
            return pd.read_sql("""
                SELECT * FROM wishlist
                ORDER BY priority DESC, created_at DESC
            """, self.conn)
        except Exception as e:
            raise Exception(f"Failed to fetch wishlist: {str(e)}")

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
