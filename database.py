import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import time
from datetime import datetime
import uuid

class Database:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.conn = None
        self.connect()
        self.init_migrations()
        
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
                return
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                    
        raise Exception(f"Failed to connect to database after {self.max_retries} attempts. Last error: {last_error}")

    def init_migrations(self):
        """Initialize migrations table and system"""
        with self.conn.cursor() as cur:
            # Create migrations table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'pending',
                    rollback_sql TEXT
                )
            """)
            self.conn.commit()
            
            # Check current version
            cur.execute("SELECT MAX(version) FROM schema_migrations WHERE status = 'completed'")
            current_version = cur.fetchone()[0] or 0
            
            # Define migrations
            migrations = [
                {
                    'version': 1,
                    'name': 'initial_schema',
                    'up': """
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
                    """,
                    'down': "DROP TABLE IF EXISTS decks"
                },
                {
                    'version': 2,
                    'name': 'add_wishlist',
                    'up': """
                        CREATE TABLE IF NOT EXISTS wishlist (
                            id SERIAL PRIMARY KEY,
                            deck_name VARCHAR(255) NOT NULL,
                            manufacturer VARCHAR(255) NOT NULL,
                            expected_price DECIMAL(10,2),
                            priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                            notes TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """,
                    'down': "DROP TABLE IF EXISTS wishlist"
                },
                {
                    'version': 3,
                    'name': 'add_market_values',
                    'up': """
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
                    """,
                    'down': "DROP TABLE IF EXISTS market_values"
                },
                {
                    'version': 4,
                    'name': 'add_uuid_extension',
                    'up': """
                        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                    """,
                    'down': """
                        DROP EXTENSION IF EXISTS "uuid-ossp";
                    """
                },
                {
                    'version': 5,
                    'name': 'add_shared_collections',
                    'up': """
                        CREATE TABLE IF NOT EXISTS shared_collections (
                            id SERIAL PRIMARY KEY,
                            share_id UUID DEFAULT uuid_generate_v4(),
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            deck_ids INTEGER[] NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP,
                            is_public BOOLEAN DEFAULT false,
                            UNIQUE(share_id)
                        )
                    """,
                    'down': """
                        DROP TABLE IF EXISTS shared_collections;
                    """
                }
            ]
            
            # Apply pending migrations
            for migration in migrations:
                if migration['version'] > current_version:
                    try:
                        # Start migration
                        cur.execute(
                            "INSERT INTO schema_migrations (version, name, status, rollback_sql) VALUES (%s, %s, %s, %s)",
                            (migration['version'], migration['name'], 'pending', migration['down'])
                        )
                        
                        # Apply migration
                        cur.execute(migration['up'])
                        
                        # Mark as completed
                        cur.execute(
                            "UPDATE schema_migrations SET status = 'completed', applied_at = %s WHERE version = %s",
                            (datetime.now(), migration['version'])
                        )
                        
                        self.conn.commit()
                    except Exception as e:
                        self.conn.rollback()
                        # Mark as failed
                        cur.execute(
                            "UPDATE schema_migrations SET status = 'failed' WHERE version = %s",
                            (migration['version'],)
                        )
                        self.conn.commit()
                        raise Exception(f"Migration {migration['version']} failed: {str(e)}")

    def rollback_migration(self, version):
        """Rollback a specific migration version"""
        with self.conn.cursor() as cur:
            try:
                # Get rollback SQL
                cur.execute("SELECT rollback_sql FROM schema_migrations WHERE version = %s", (version,))
                result = cur.fetchone()
                if not result:
                    raise Exception(f"Migration version {version} not found")
                
                rollback_sql = result[0]
                
                # Execute rollback
                cur.execute(rollback_sql)
                
                # Remove migration record
                cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
                
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Rollback failed for version {version}: {str(e)}")

    def ensure_connection(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self.connect()
            self.init_migrations()

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

    def get_current_schema_version(self):
        """Get the current schema version"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            cur.execute("SELECT MAX(version) FROM schema_migrations WHERE status = 'completed'")
            return cur.fetchone()[0] or 0

    def create_shared_collection(self, name, deck_ids, description=None, expires_at=None, is_public=False):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO shared_collections (name, description, deck_ids, expires_at, is_public)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING share_id
                """, (name, description, deck_ids, expires_at, is_public))
                self.conn.commit()
                return cur.fetchone()[0]
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Failed to create shared collection: {str(e)}")

    def get_shared_collection(self, share_id):
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                # Get shared collection details
                cur.execute("""
                    SELECT * FROM shared_collections 
                    WHERE share_id = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (share_id,))
                collection = cur.fetchone()
                
                if not collection:
                    return None
                
                # Get associated decks
                deck_ids = collection['deck_ids']
                if deck_ids:
                    cur.execute("""
                        SELECT id, deck_name, manufacturer, release_year, condition, 
                               purchase_date, notes, created_at
                        FROM decks 
                        WHERE id = ANY(%s)
                    """, (deck_ids,))
                    collection['decks'] = cur.fetchall()
                else:
                    collection['decks'] = []
                
                return collection
            except Exception as e:
                raise Exception(f"Failed to fetch shared collection: {str(e)}")

    def get_active_shared_collections(self):
        self.ensure_connection()
        try:
            return pd.read_sql("""
                SELECT * FROM shared_collections
                WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
            """, self.conn)
        except Exception as e:
            raise Exception(f"Failed to fetch shared collections: {str(e)}")

db = Database()
