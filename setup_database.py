import psycopg2
import bcrypt
import os
import time
import sys

# Database connection parameters
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'streaming_service'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'port': os.environ.get('DB_PORT', '5432')
}

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready"""
    print(f"Waiting for database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("Database is ready")
            return True
        except psycopg2.OperationalError:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries} - Database not ready, waiting {delay}s...")
                time.sleep(delay)
            else:
                print("Error: Database connection timeout")
                return False
    return False

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_tables(conn):
    """Create all database tables"""
    cur = conn.cursor()
    
    print("\nCreating tables...")
    
    # Drop existing tables (for clean setup)
    cur.execute("""
        DROP TABLE IF EXISTS viewing_history CASCADE;
        DROP TABLE IF EXISTS wishlist CASCADE;
        DROP TABLE IF EXISTS episodes CASCADE;
        DROP TABLE IF EXISTS seasons CASCADE;
        DROP TABLE IF EXISTS media_files CASCADE;
        DROP TABLE IF EXISTS content_genres CASCADE;
        DROP TABLE IF EXISTS genres CASCADE;
        DROP TABLE IF EXISTS content CASCADE;
        DROP TABLE IF EXISTS profiles CASCADE;
        DROP TABLE IF EXISTS accounts CASCADE;
        DROP TABLE IF EXISTS subscriptions CASCADE;
        DROP TABLE IF EXISTS admins CASCADE;
    """)
    
    # Create subscriptions table
    cur.execute("""
        CREATE TABLE subscriptions (
            subscription_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            monthly_price DECIMAL(10, 2) NOT NULL,
            max_profiles INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created subscriptions table")
    
    # Create accounts table
    cur.execute("""
        CREATE TABLE accounts (
            account_id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            subscription_id INTEGER REFERENCES subscriptions(subscription_id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created accounts table")
    
    # Create profiles table
    cur.execute("""
        CREATE TABLE profiles (
            profile_id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            age_rating_pref VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created profiles table")
    
    # Create content table
    cur.execute("""
        CREATE TABLE content (
            content_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            type VARCHAR(10) NOT NULL CHECK (type IN ('Movie', 'Show')),
            description TEXT,
            release_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created content table")
    
    # Create genres table
    cur.execute("""
        CREATE TABLE genres (
            genre_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE
        )
    """)
    print("Created genres table")
    
    # Create content_genres junction table
    cur.execute("""
        CREATE TABLE content_genres (
            content_id INTEGER REFERENCES content(content_id) ON DELETE CASCADE,
            genre_id INTEGER REFERENCES genres(genre_id) ON DELETE CASCADE,
            PRIMARY KEY (content_id, genre_id)
        )
    """)
    print("Created content_genres table")
    
    # Create media_files table
    cur.execute("""
        CREATE TABLE media_files (
            media_id SERIAL PRIMARY KEY,
            content_id INTEGER NOT NULL REFERENCES content(content_id) ON DELETE CASCADE,
            resolution VARCHAR(20) NOT NULL,
            language VARCHAR(50) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created media_files table")
    
    # Create seasons table
    cur.execute("""
        CREATE TABLE seasons (
            season_id SERIAL PRIMARY KEY,
            content_id INTEGER NOT NULL REFERENCES content(content_id) ON DELETE CASCADE,
            season_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (content_id, season_number)
        )
    """)
    print("Created seasons table")
    
    # Create episodes table
    cur.execute("""
        CREATE TABLE episodes (
            episode_id SERIAL PRIMARY KEY,
            season_id INTEGER NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            episode_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (season_id, episode_number)
        )
    """)
    print("Created episodes table")
    
    # Create wishlist table
    cur.execute("""
        CREATE TABLE wishlist (
            profile_id INTEGER REFERENCES profiles(profile_id) ON DELETE CASCADE,
            content_id INTEGER REFERENCES content(content_id) ON DELETE CASCADE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (profile_id, content_id)
        )
    """)
    print("Created wishlist table")
    
    # Create viewing_history table
    cur.execute("""
        CREATE TABLE viewing_history (
            profile_id INTEGER REFERENCES profiles(profile_id) ON DELETE CASCADE,
            content_id INTEGER REFERENCES content(content_id) ON DELETE CASCADE,
            last_timestamp INTEGER NOT NULL,
            watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (profile_id, content_id)
        )
    """)
    print("Created viewing_history table")
    
    # Create admins table
    cur.execute("""
        CREATE TABLE admins (
            admin_id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created admins table")
    
    conn.commit()
    cur.close()

def populate_seed_data(conn):
    """Populate initial seed data"""
    cur = conn.cursor()
    
    print("\nPopulating seed data...")
    
    # Create subscription plans
    subscriptions = [
        ('Basic', 9.99, 1),
        ('Standard', 15.99, 2),
        ('Premium', 19.99, 4)
    ]
    
    for name, price, max_profiles in subscriptions:
        cur.execute(
            "INSERT INTO subscriptions (name, monthly_price, max_profiles) VALUES (%s, %s, %s)",
            (name, price, max_profiles)
        )
    print("Created subscription plans")
    
    # Create default admin account (username: admin, password: admin123)
    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        ('admin', admin_password.decode('utf-8'))
    )
    print("Created admin account (username: admin, password: admin123)")
    
    # Create sample genres
    genres = [
        'Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi',
        'Romance', 'Thriller', 'Documentary', 'Animation', 'Fantasy'
    ]
    
    for genre in genres:
        cur.execute("INSERT INTO genres (name) VALUES (%s)", (genre,))
    print("Created sample genres")
    
    # Create sample movies
    movies = [
        ('The Space Odyssey', 'Movie', 'An epic journey through space and time', 2023),
        ('Midnight Laughter', 'Movie', 'A hilarious comedy about late night adventures', 2022),
        ('The Last Stand', 'Movie', 'An action-packed thriller', 2024),
    ]
    
    for title, content_type, description, year in movies:
        cur.execute(
            "INSERT INTO content (title, type, description, release_year) VALUES (%s, %s, %s, %s)",
            (title, content_type, description, year)
        )
    print("Created sample movies")
    
    # Create sample TV show
    cur.execute(
        "INSERT INTO content (title, type, description, release_year) VALUES (%s, %s, %s, %s) RETURNING content_id",
        ('Cosmic Adventures', 'Show', 'A thrilling sci-fi series', 2023)
    )
    show_content_id = cur.fetchone()[0]
    
    # Add seasons to the show
    cur.execute(
        "INSERT INTO seasons (content_id, season_number) VALUES (%s, %s) RETURNING season_id",
        (show_content_id, 1)
    )
    season1_id = cur.fetchone()[0]
    
    cur.execute(
        "INSERT INTO seasons (content_id, season_number) VALUES (%s, %s) RETURNING season_id",
        (show_content_id, 2)
    )
    season2_id = cur.fetchone()[0]
    
    # Add episodes to season 1
    episodes_s1 = [
        ('Pilot', 1),
        ('The Discovery', 2),
        ('New Horizons', 3),
    ]
    
    for title, ep_num in episodes_s1:
        cur.execute(
            "INSERT INTO episodes (season_id, title, episode_number) VALUES (%s, %s, %s)",
            (season1_id, title, ep_num)
        )
    
    # Add episodes to season 2
    episodes_s2 = [
        ('Return Journey', 1),
        ('The Awakening', 2),
    ]
    
    for title, ep_num in episodes_s2:
        cur.execute(
            "INSERT INTO episodes (season_id, title, episode_number) VALUES (%s, %s, %s)",
            (season2_id, title, ep_num)
        )
    
    print("Created sample TV show with seasons and episodes")
    
    # Link some content to genres
    cur.execute("SELECT content_id FROM content LIMIT 4")
    content_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT genre_id FROM genres WHERE name IN ('Sci-Fi', 'Action', 'Comedy')")
    genre_ids = [row[0] for row in cur.fetchall()]
    
    if content_ids and genre_ids:
        # Link first movie to Sci-Fi
        cur.execute(
            "INSERT INTO content_genres (content_id, genre_id) VALUES (%s, %s)",
            (content_ids[0], genre_ids[0])
        )
        # Link second movie to Comedy
        if len(content_ids) > 1 and len(genre_ids) > 2:
            cur.execute(
                "INSERT INTO content_genres (content_id, genre_id) VALUES (%s, %s)",
                (content_ids[1], genre_ids[2])
            )
        # Link third movie to Action
        if len(content_ids) > 2 and len(genre_ids) > 1:
            cur.execute(
                "INSERT INTO content_genres (content_id, genre_id) VALUES (%s, %s)",
                (content_ids[2], genre_ids[1])
            )
        # Link show to Sci-Fi
        if len(content_ids) > 3:
            cur.execute(
                "INSERT INTO content_genres (content_id, genre_id) VALUES (%s, %s)",
                (content_ids[3], genre_ids[0])
            )
    
    print("Linked content to genres")
    
    # Add sample media files
    cur.execute("SELECT content_id FROM content LIMIT 3")
    content_ids = [row[0] for row in cur.fetchall()]
    
    for content_id in content_ids:
        # Add HD version
        cur.execute(
            "INSERT INTO media_files (content_id, resolution, language, file_path) VALUES (%s, %s, %s, %s)",
            (content_id, '1080p', 'English', f'/media/content_{content_id}_1080p_en.mp4')
        )
        # Add SD version
        cur.execute(
            "INSERT INTO media_files (content_id, resolution, language, file_path) VALUES (%s, %s, %s, %s)",
            (content_id, '720p', 'English', f'/media/content_{content_id}_720p_en.mp4')
        )
    
    print("Added sample media files")
    
    conn.commit()
    cur.close()

def create_indexes(conn):
    """Create database indexes for performance"""
    cur = conn.cursor()
    
    print("\nCreating indexes...")
    
    cur.execute("CREATE INDEX idx_accounts_email ON accounts(email)")
    cur.execute("CREATE INDEX idx_profiles_account_id ON profiles(account_id)")
    cur.execute("CREATE INDEX idx_content_type ON content(type)")
    cur.execute("CREATE INDEX idx_content_release_year ON content(release_year)")
    cur.execute("CREATE INDEX idx_wishlist_profile_id ON wishlist(profile_id)")
    cur.execute("CREATE INDEX idx_viewing_history_profile_id ON viewing_history(profile_id)")
    
    print("Created performance indexes")
    
    conn.commit()
    cur.close()

def main():
    """Main setup function"""
    print("=" * 60)
    print("STREAMING SERVICE DATABASE SETUP")
    print("=" * 60)
    print(f"\nConnecting to database '{DB_CONFIG['database']}' at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    
    # Wait for database to be ready
    if not wait_for_db():
        print("\nError: Failed to connect to database")
        print("\nTroubleshooting:")
        print("  1. Make sure Docker is running")
        print("  2. Start PostgreSQL: docker-compose up -d")
        print("  3. Check logs: docker-compose logs postgres")
        return 1
    
    try:
        conn = get_connection()
        print("Connected successfully\n")
        
        create_tables(conn)
        populate_seed_data(conn)
        create_indexes(conn)
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nDefault Admin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nSubscription Plans Created:")
        print("  - Basic: $9.99/month (1 profile)")
        print("  - Standard: $15.99/month (2 profiles)")
        print("  - Premium: $19.99/month (4 profiles)")
        print("\nDatabase Connection Info:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print("\n" + "=" * 60)
        
    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL Docker container is running")
        print("  2. Database exists")
        print("  3. Connection credentials are correct")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())