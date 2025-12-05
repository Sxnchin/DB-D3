from flask import Flask, request, jsonify
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import jwt
import sys

# Validate PyJWT (not the older jwt package)
if not (hasattr(jwt, 'encode') and hasattr(jwt, 'decode')):
    print("ERROR: The installed 'jwt' package is not PyJWT. This app requires PyJWT (pip install PyJWT==2.8.0).")
    print("You may have the 'jwt' package (jwt==1.x) installed which is incompatible. Please run:")
    print("  python -m pip uninstall jwt && python -m pip install PyJWT==2.8.0")
    sys.exit(3)

import bcrypt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'streaming_service'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        cursor_factory=RealDictCursor
    )
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_account_id = data['account_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_account_id, *args, **kwargs)
    
    return decorated

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if not data.get('is_admin'):
                return jsonify({'error': 'Admin access required'}), 403
            current_admin_id = data['admin_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_admin_id, *args, **kwargs)
    
    return decorated

# ==================== CUSTOMER ROUTES ====================

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT subscription_id, name, monthly_price, max_profiles FROM subscriptions ORDER BY subscription_id')
        subscriptions = cur.fetchall()
        return jsonify([dict(s) for s in subscriptions]), 200
    finally:
        cur.close()
        conn.close()

# ==================== AUTHENTICATION ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    subscription_id = data.get('subscription_id')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    if not subscription_id:
        return jsonify({'error': 'subscription_id required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if email exists
        cur.execute('SELECT account_id FROM accounts WHERE email = %s', (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Verify subscription exists
        cur.execute('SELECT subscription_id FROM subscriptions WHERE subscription_id = %s', (subscription_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert account with subscription
        cur.execute(
            'INSERT INTO accounts (email, password_hash, subscription_id) VALUES (%s, %s, %s) RETURNING account_id',
            (email, hashed_password.decode('utf-8'), subscription_id)
        )
        account_id = cur.fetchone()['account_id']
        conn.commit()
        
        # Generate token
        token = jwt.encode({
            'account_id': account_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'account_id': account_id,
            'email': email,
            'subscription_id': subscription_id,
            'token': token
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT account_id, email, password_hash, subscription_id FROM accounts WHERE email = %s',
            (email,)
        )
        account = cur.fetchone()
        
        if not account or not bcrypt.checkpw(password.encode('utf-8'), account['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'account_id': account['account_id'],
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'account_id': account['account_id'],
            'email': account['email'],
            'subscription_id': account['subscription_id'],
            'token': token
        }), 200
        
    finally:
        cur.close()
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_account_id):
    return jsonify({'message': 'Logged out'}), 200

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT account_id, email, subscription_id, created_at FROM accounts WHERE account_id = %s',
            (current_account_id,)
        )
        account = cur.fetchone()
        return jsonify(dict(account)), 200
    finally:
        cur.close()
        conn.close()

# ACCOUNT & SUBSCRIPTION
@app.route('/api/account', methods=['GET'])
@token_required
def get_account(current_account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT account_id, email, subscription_id, created_at FROM accounts WHERE account_id = %s',
            (current_account_id,)
        )
        account = cur.fetchone()
        return jsonify(dict(account)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/account', methods=['PUT'])
@token_required
def update_account(current_account_id):
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if email:
            cur.execute('UPDATE accounts SET email = %s WHERE account_id = %s', 
                       (email, current_account_id))
        
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute('UPDATE accounts SET password_hash = %s WHERE account_id = %s',
                       (hashed_password.decode('utf-8'), current_account_id))
        
        conn.commit()
        return jsonify({'message': 'Account updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/account/subscription', methods=['GET'])
@token_required
def get_subscription(current_account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT s.subscription_id, s.name, s.monthly_price, s.max_profiles
            FROM subscriptions s
            JOIN accounts a ON a.subscription_id = s.subscription_id
            WHERE a.account_id = %s
        ''', (current_account_id,))
        
        subscription = cur.fetchone()
        if not subscription:
            return jsonify({'error': 'No subscription found'}), 404
        
        return jsonify(dict(subscription)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/account/subscription', methods=['PUT'])
@token_required
def update_subscription(current_account_id):
    data = request.json
    subscription_id = data.get('subscription_id')
    
    if not subscription_id:
        return jsonify({'error': 'subscription_id required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify subscription exists
        cur.execute('SELECT subscription_id FROM subscriptions WHERE subscription_id = %s', 
                   (subscription_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Subscription not found'}), 404
        
        cur.execute('UPDATE accounts SET subscription_id = %s WHERE account_id = %s',
                   (subscription_id, current_account_id))
        conn.commit()
        
        return jsonify({'message': 'Subscription updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# PROFILES
@app.route('/api/profiles', methods=['GET'])
@token_required
def get_profiles(current_account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT profile_id, name, age_rating_pref FROM profiles WHERE account_id = %s',
            (current_account_id,)
        )
        profiles = cur.fetchall()
        return jsonify([dict(p) for p in profiles]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles', methods=['POST'])
@token_required
def create_profile(current_account_id):
    data = request.json
    name = data.get('name')
    age_rating_pref = data.get('age_rating_pref')
    
    if not name or not age_rating_pref:
        return jsonify({'error': 'name and age_rating_pref required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check profile limit
        cur.execute('''
            SELECT s.max_profiles, COUNT(p.profile_id) as current_profiles
            FROM accounts a
            LEFT JOIN subscriptions s ON a.subscription_id = s.subscription_id
            LEFT JOIN profiles p ON p.account_id = a.account_id
            WHERE a.account_id = %s
            GROUP BY s.max_profiles
        ''', (current_account_id,))
        
        result = cur.fetchone()
        if result and result['max_profiles'] and result['current_profiles'] >= result['max_profiles']:
            return jsonify({'error': 'Profile limit reached'}), 400
        
        cur.execute(
            'INSERT INTO profiles (account_id, name, age_rating_pref) VALUES (%s, %s, %s) RETURNING profile_id',
            (current_account_id, name, age_rating_pref)
        )
        profile_id = cur.fetchone()['profile_id']
        conn.commit()
        
        return jsonify({
            'profile_id': profile_id,
            'name': name,
            'age_rating_pref': age_rating_pref
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>', methods=['GET'])
@token_required
def get_profile(current_account_id, profile_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT profile_id, name, age_rating_pref FROM profiles WHERE profile_id = %s AND account_id = %s',
            (profile_id, current_account_id)
        )
        profile = cur.fetchone()
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify(dict(profile)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>', methods=['PUT'])
@token_required
def update_profile(current_account_id, profile_id):
    data = request.json
    name = data.get('name')
    age_rating_pref = data.get('age_rating_pref')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        if name:
            cur.execute('UPDATE profiles SET name = %s WHERE profile_id = %s',
                       (name, profile_id))
        
        if age_rating_pref:
            cur.execute('UPDATE profiles SET age_rating_pref = %s WHERE profile_id = %s',
                       (age_rating_pref, profile_id))
        
        conn.commit()
        return jsonify({'message': 'Profile updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
@token_required
def delete_profile(current_account_id, profile_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Profile not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Profile deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# CONTENT BROWSING
@app.route('/api/content', methods=['GET'])
def get_content():
    content_type = request.args.get('type')
    genre = request.args.get('genre')
    year = request.args.get('year')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = 'SELECT content_id, title, type, description, release_year FROM content WHERE 1=1'
        params = []
        
        if content_type:
            query += ' AND type = %s'
            params.append(content_type)
        
        if genre:
            query += ''' AND content_id IN (
                SELECT cg.content_id FROM content_genres cg
                JOIN genres g ON cg.genre_id = g.genre_id
                WHERE g.name = %s
            )'''
            params.append(genre)
        
        if year:
            query += ' AND release_year = %s'
            params.append(int(year))
        
        cur.execute(query, params)
        content = cur.fetchall()
        return jsonify([dict(c) for c in content]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/content/<int:content_id>', methods=['GET'])
def get_content_by_id(content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT content_id, title, type, description, release_year FROM content WHERE content_id = %s',
            (content_id,)
        )
        content = cur.fetchone()
        
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        return jsonify(dict(content)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/content/<int:content_id>/media', methods=['GET'])
def get_content_media(content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT media_id, resolution, language, file_path FROM media_files WHERE content_id = %s',
            (content_id,)
        )
        media = cur.fetchall()
        return jsonify([dict(m) for m in media]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/content/<int:content_id>/genres', methods=['GET'])
def get_content_genres(content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT g.genre_id, g.name
            FROM genres g
            JOIN content_genres cg ON g.genre_id = cg.genre_id
            WHERE cg.content_id = %s
        ''', (content_id,))
        genres = cur.fetchall()
        return jsonify([dict(g) for g in genres]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/content/<int:content_id>/seasons', methods=['GET'])
def get_content_seasons(content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT season_id, season_number FROM seasons WHERE content_id = %s ORDER BY season_number',
            (content_id,)
        )
        seasons = cur.fetchall()
        return jsonify([dict(s) for s in seasons]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/seasons/<int:season_id>/episodes', methods=['GET'])
def get_season_episodes(season_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT episode_id, title, episode_number FROM episodes WHERE season_id = %s ORDER BY episode_number',
            (season_id,)
        )
        episodes = cur.fetchall()
        return jsonify([dict(e) for e in episodes]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/episodes/<int:episode_id>', methods=['GET'])
def get_episode(episode_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT episode_id, title, episode_number FROM episodes WHERE episode_id = %s',
            (episode_id,)
        )
        episode = cur.fetchone()
        
        if not episode:
            return jsonify({'error': 'Episode not found'}), 404
        
        return jsonify(dict(episode)), 200
    finally:
        cur.close()
        conn.close()

# WISHLIST
@app.route('/api/profiles/<int:profile_id>/wishlist', methods=['GET'])
@token_required
def get_wishlist(current_account_id, profile_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute('''
            SELECT c.content_id, c.title
            FROM content c
            JOIN wishlist w ON c.content_id = w.content_id
            WHERE w.profile_id = %s
        ''', (profile_id,))
        wishlist = cur.fetchall()
        return jsonify([dict(w) for w in wishlist]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>/wishlist/<int:content_id>', methods=['POST'])
@token_required
def add_to_wishlist(current_account_id, profile_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute(
            'INSERT INTO wishlist (profile_id, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
            (profile_id, content_id)
        )
        conn.commit()
        return jsonify({'message': 'Added to wishlist'}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>/wishlist/<int:content_id>', methods=['DELETE'])
@token_required
def remove_from_wishlist(current_account_id, profile_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute('DELETE FROM wishlist WHERE profile_id = %s AND content_id = %s',
                   (profile_id, content_id))
        conn.commit()
        return jsonify({'message': 'Removed from wishlist'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# VIEWING HISTORY
@app.route('/api/profiles/<int:profile_id>/history', methods=['GET'])
@token_required
def get_history(current_account_id, profile_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute(
            'SELECT content_id, last_timestamp FROM viewing_history WHERE profile_id = %s',
            (profile_id,)
        )
        history = cur.fetchall()
        return jsonify([dict(h) for h in history]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>/history/<int:content_id>', methods=['GET'])
@token_required
def get_history_item(current_account_id, profile_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute(
            'SELECT content_id, last_timestamp FROM viewing_history WHERE profile_id = %s AND content_id = %s',
            (profile_id, content_id)
        )
        history = cur.fetchone()
        
        if not history:
            return jsonify({'error': 'History not found'}), 404
        
        return jsonify(dict(history)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>/history/<int:content_id>', methods=['PUT'])
@token_required
def update_history(current_account_id, profile_id, content_id):
    data = request.json
    last_timestamp = data.get('last_timestamp')
    
    if last_timestamp is None:
        return jsonify({'error': 'last_timestamp required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute('''
            INSERT INTO viewing_history (profile_id, content_id, last_timestamp)
            VALUES (%s, %s, %s)
            ON CONFLICT (profile_id, content_id)
            DO UPDATE SET last_timestamp = EXCLUDED.last_timestamp
        ''', (profile_id, content_id, last_timestamp))
        
        conn.commit()
        return jsonify({'message': 'History updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/profiles/<int:profile_id>/history/<int:content_id>', methods=['DELETE'])
@token_required
def delete_history(current_account_id, profile_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verify profile ownership
        cur.execute('SELECT profile_id FROM profiles WHERE profile_id = %s AND account_id = %s',
                   (profile_id, current_account_id))
        if not cur.fetchone():
            return jsonify({'error': 'Profile not found'}), 404
        
        cur.execute('DELETE FROM viewing_history WHERE profile_id = %s AND content_id = %s',
                   (profile_id, content_id))
        conn.commit()
        return jsonify({'message': 'History removed'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ==================== ADMIN ROUTES ====================

# ADMIN AUTHENTICATION
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT admin_id, username, password_hash FROM admins WHERE username = %s',
            (username,)
        )
        admin = cur.fetchone()
        
        if not admin or not bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'admin_id': admin['admin_id'],
            'is_admin': True,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'admin_id': admin['admin_id'],
            'token': token
        }), 200
        
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/logout', methods=['POST'])
@admin_token_required
def admin_logout(current_admin_id):
    return jsonify({'message': 'Logged out'}), 200

# SUBSCRIPTION PLAN MANAGEMENT
@app.route('/api/admin/subscriptions', methods=['GET'])
@admin_token_required
def get_admin_subscriptions(current_admin_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT subscription_id, name, max_profiles, monthly_price FROM subscriptions')
        subscriptions = cur.fetchall()
        return jsonify([dict(s) for s in subscriptions]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/subscriptions', methods=['POST'])
@admin_token_required
def create_subscription(current_admin_id):
    data = request.json
    name = data.get('name')
    max_profiles = data.get('max_profiles')
    monthly_price = data.get('monthly_price')
    
    if not name or max_profiles is None or monthly_price is None:
        return jsonify({'error': 'name, max_profiles, and monthly_price required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO subscriptions (name, max_profiles, monthly_price) VALUES (%s, %s, %s) RETURNING subscription_id',
            (name, max_profiles, monthly_price)
        )
        subscription_id = cur.fetchone()['subscription_id']
        conn.commit()
        
        return jsonify({'subscription_id': subscription_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/subscriptions/<int:subscription_id>', methods=['GET'])
@admin_token_required
def get_subscription_by_id(current_admin_id, subscription_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT subscription_id, name, max_profiles, monthly_price FROM subscriptions WHERE subscription_id = %s',
            (subscription_id,)
        )
        subscription = cur.fetchone()
        
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404
        
        return jsonify(dict(subscription)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/subscriptions/<int:subscription_id>', methods=['PUT'])
@admin_token_required
def update_subscription_plan(current_admin_id, subscription_id):
    data = request.json
    name = data.get('name')
    max_profiles = data.get('max_profiles')
    monthly_price = data.get('monthly_price')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if name:
            cur.execute('UPDATE subscriptions SET name = %s WHERE subscription_id = %s',
                       (name, subscription_id))
        
        if max_profiles is not None:
            cur.execute('UPDATE subscriptions SET max_profiles = %s WHERE subscription_id = %s',
                       (max_profiles, subscription_id))
        
        if monthly_price is not None:
            cur.execute('UPDATE subscriptions SET monthly_price = %s WHERE subscription_id = %s',
                       (monthly_price, subscription_id))
        
        conn.commit()
        return jsonify({'message': 'Subscription plan updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/subscriptions/<int:subscription_id>', methods=['DELETE'])
@admin_token_required
def delete_subscription_plan(current_admin_id, subscription_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM subscriptions WHERE subscription_id = %s', (subscription_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Subscription not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Subscription plan deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ACCOUNT MANAGEMENT
@app.route('/api/admin/accounts', methods=['GET'])
@admin_token_required
def get_all_accounts(current_admin_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT account_id, email, subscription_id, created_at FROM accounts')
        accounts = cur.fetchall()
        return jsonify([dict(a) for a in accounts]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/accounts/<int:account_id>', methods=['GET'])
@admin_token_required
def get_account_by_id(current_admin_id, account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT account_id, email, subscription_id, created_at FROM accounts WHERE account_id = %s',
            (account_id,)
        )
        account = cur.fetchone()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        return jsonify(dict(account)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/accounts/<int:account_id>', methods=['PUT'])
@admin_token_required
def admin_update_account(current_admin_id, account_id):
    data = request.json
    email = data.get('email')
    subscription_id = data.get('subscription_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if email:
            cur.execute('UPDATE accounts SET email = %s WHERE account_id = %s',
                       (email, account_id))
        
        if subscription_id is not None:
            cur.execute('UPDATE accounts SET subscription_id = %s WHERE account_id = %s',
                       (subscription_id, account_id))
        
        conn.commit()
        return jsonify({'message': 'Account updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/accounts/<int:account_id>', methods=['DELETE'])
@admin_token_required
def delete_account(current_admin_id, account_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM accounts WHERE account_id = %s', (account_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Account not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Account deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# CONTENT MANAGEMENT
@app.route('/api/admin/content', methods=['GET'])
@admin_token_required
def admin_get_content(current_admin_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT content_id, title, type FROM content')
        content = cur.fetchall()
        return jsonify([dict(c) for c in content]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content', methods=['POST'])
@admin_token_required
def create_content(current_admin_id):
    data = request.json
    title = data.get('title')
    content_type = data.get('type')
    description = data.get('description')
    release_year = data.get('release_year')
    
    if not title or not content_type or not description or not release_year:
        return jsonify({'error': 'title, type, description, and release_year required'}), 400
    
    if content_type not in ['Movie', 'Show']:
        return jsonify({'error': 'type must be Movie or Show'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO content (title, type, description, release_year) VALUES (%s, %s, %s, %s) RETURNING content_id',
            (title, content_type, description, release_year)
        )
        content_id = cur.fetchone()['content_id']
        conn.commit()
        
        return jsonify({'content_id': content_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content/<int:content_id>', methods=['GET'])
@admin_token_required
def admin_get_content_by_id(current_admin_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'SELECT content_id, title, type, description, release_year FROM content WHERE content_id = %s',
            (content_id,)
        )
        content = cur.fetchone()
        
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        return jsonify(dict(content)), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content/<int:content_id>', methods=['PUT'])
@admin_token_required
def admin_update_content(current_admin_id, content_id):
    data = request.json
    title = data.get('title')
    description = data.get('description')
    release_year = data.get('release_year')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if title:
            cur.execute('UPDATE content SET title = %s WHERE content_id = %s',
                       (title, content_id))
        
        if description:
            cur.execute('UPDATE content SET description = %s WHERE content_id = %s',
                       (description, content_id))
        
        if release_year is not None:
            cur.execute('UPDATE content SET release_year = %s WHERE content_id = %s',
                       (release_year, content_id))
        
        conn.commit()
        return jsonify({'message': 'Content updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content/<int:content_id>', methods=['DELETE'])
@admin_token_required
def admin_delete_content(current_admin_id, content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM content WHERE content_id = %s', (content_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Content not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Content deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# MEDIA FILE MANAGEMENT
@app.route('/api/admin/content/<int:content_id>/media', methods=['POST'])
@admin_token_required
def create_media_file(current_admin_id, content_id):
    data = request.json
    resolution = data.get('resolution')
    language = data.get('language')
    file_path = data.get('file_path')
    
    if not resolution or not language or not file_path:
        return jsonify({'error': 'resolution, language, and file_path required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO media_files (content_id, resolution, language, file_path) VALUES (%s, %s, %s, %s) RETURNING media_id',
            (content_id, resolution, language, file_path)
        )
        media_id = cur.fetchone()['media_id']
        conn.commit()
        
        return jsonify({'media_id': media_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/media/<int:media_id>', methods=['DELETE'])
@admin_token_required
def delete_media_file(current_admin_id, media_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM media_files WHERE media_id = %s', (media_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Media file not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Media file deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# GENRE MANAGEMENT
@app.route('/api/admin/genres', methods=['GET'])
@admin_token_required
def get_genres(current_admin_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT genre_id, name FROM genres')
        genres = cur.fetchall()
        return jsonify([dict(g) for g in genres]), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/genres', methods=['POST'])
@admin_token_required
def create_genre(current_admin_id):
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'name required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('INSERT INTO genres (name) VALUES (%s) RETURNING genre_id', (name,))
        genre_id = cur.fetchone()['genre_id']
        conn.commit()
        
        return jsonify({'genre_id': genre_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/genres/<int:genre_id>', methods=['PUT'])
@admin_token_required
def update_genre(current_admin_id, genre_id):
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'name required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE genres SET name = %s WHERE genre_id = %s', (name, genre_id))
        conn.commit()
        return jsonify({'message': 'Genre updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/genres/<int:genre_id>', methods=['DELETE'])
@admin_token_required
def delete_genre(current_admin_id, genre_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM genres WHERE genre_id = %s', (genre_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Genre not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Genre deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content/<int:content_id>/genres/<int:genre_id>', methods=['POST'])
@admin_token_required
def link_genre_to_content(current_admin_id, content_id, genre_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO content_genres (content_id, genre_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
            (content_id, genre_id)
        )
        conn.commit()
        return jsonify({'message': 'Genre linked to content'}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/content/<int:content_id>/genres/<int:genre_id>', methods=['DELETE'])
@admin_token_required
def unlink_genre_from_content(current_admin_id, content_id, genre_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'DELETE FROM content_genres WHERE content_id = %s AND genre_id = %s',
            (content_id, genre_id)
        )
        conn.commit()
        return jsonify({'message': 'Genre unlinked from content'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# SEASONS & EPISODES
@app.route('/api/admin/content/<int:content_id>/seasons', methods=['POST'])
@admin_token_required
def create_season(current_admin_id, content_id):
    data = request.json
    season_number = data.get('season_number')
    
    if season_number is None:
        return jsonify({'error': 'season_number required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO seasons (content_id, season_number) VALUES (%s, %s) RETURNING season_id',
            (content_id, season_number)
        )
        season_id = cur.fetchone()['season_id']
        conn.commit()
        
        return jsonify({'season_id': season_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/seasons/<int:season_id>', methods=['PUT'])
@admin_token_required
def update_season(current_admin_id, season_id):
    data = request.json
    season_number = data.get('season_number')
    
    if season_number is None:
        return jsonify({'error': 'season_number required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE seasons SET season_number = %s WHERE season_id = %s',
                   (season_number, season_id))
        conn.commit()
        return jsonify({'message': 'Season updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/seasons/<int:season_id>', methods=['DELETE'])
@admin_token_required
def delete_season(current_admin_id, season_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM seasons WHERE season_id = %s', (season_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Season not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Season deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/seasons/<int:season_id>/episodes', methods=['POST'])
@admin_token_required
def create_episode(current_admin_id, season_id):
    data = request.json
    title = data.get('title')
    episode_number = data.get('episode_number')
    
    if not title or episode_number is None:
        return jsonify({'error': 'title and episode_number required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO episodes (season_id, title, episode_number) VALUES (%s, %s, %s) RETURNING episode_id',
            (season_id, title, episode_number)
        )
        episode_id = cur.fetchone()['episode_id']
        conn.commit()
        
        return jsonify({'episode_id': episode_id}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/episodes/<int:episode_id>', methods=['PUT'])
@admin_token_required
def update_episode(current_admin_id, episode_id):
    data = request.json
    title = data.get('title')
    episode_number = data.get('episode_number')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if title:
            cur.execute('UPDATE episodes SET title = %s WHERE episode_id = %s',
                       (title, episode_id))
        
        if episode_number is not None:
            cur.execute('UPDATE episodes SET episode_number = %s WHERE episode_id = %s',
                       (episode_number, episode_id))
        
        conn.commit()
        return jsonify({'message': 'Episode updated'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/admin/episodes/<int:episode_id>', methods=['DELETE'])
@admin_token_required
def delete_episode(current_admin_id, episode_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM episodes WHERE episode_id = %s', (episode_id,))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Episode not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Episode deleted'}), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)