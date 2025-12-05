# Streaming Service Backend API

A complete Flask-based REST API for a video streaming service with customer and administrative functionality, using PostgreSQL in Docker.

## Project Structure

```
streaming-service/
├── app.py                      # Main Flask application with all API routes
├── setup_database.py           # Database initialization script
├── test_admin_service.py       # Admin workflow testing script
├── test_user_workflow.py       # User workflow testing script
├── docker-compose.yml          # Docker configuration for PostgreSQL
├── Dockerfile                  # Optional: Flask app containerization
├── requirements.txt            # Python dependencies
├── TESTING.md                  # Comprehensive API testing documentation
└── README.md                   # This file
```

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ installed
- pip (Python package manager)

### 1. Start PostgreSQL in Docker

```bash
# Start PostgreSQL container
docker-compose up -d

# Verify PostgreSQL is running
docker ps
```

You should see the `streaming_db` container running.

### 2. Install Python Dependencies

It's recommended to use a virtual environment. For Windows PowerShell:

```powershell
python -m venv venv; .\venv\Scripts\Activate
python -m pip install -r requirements.txt
```

For POSIX shells (macOS / Linux / WSL):

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 3. Initialize the Database

```bash
# The script will automatically wait for PostgreSQL to be ready
python setup_database.py
```

This creates all tables and populates seed data including:
- 3 subscription plans (Basic, Standard, Premium)
- Default admin account (username: `admin`, password: `admin123`)
- Sample genres, content, and media files

### 4. Run the Flask Application

```bash
python app.py
```

Server will start at `http://localhost:5000`

### 5. Run Tests

```bash
# In separate terminal windows:

# Test admin operations
python test_admin_service.py

# Test complete user workflow
python test_user_workflow.py
```

## Docker Commands

### Managing PostgreSQL Container

```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# Stop and remove data (fresh start)
docker-compose down -v

# View PostgreSQL logs
docker-compose logs postgres

# Follow PostgreSQL logs
docker-compose logs -f postgres

# Access PostgreSQL CLI
docker exec -it streaming_db psql -U postgres -d streaming_service
```

### Verify Database Connection

```bash
# Check if database is accepting connections
docker exec -it streaming_db pg_isready -U postgres

# List all databases
docker exec -it streaming_db psql -U postgres -c "\l"

# Connect and query
docker exec -it streaming_db psql -U postgres -d streaming_service -c "SELECT * FROM subscriptions;"
```

## Features

### Customer Features
- **Authentication**: User registration, login, and JWT-based authentication
- **Account Management**: Update email, password, and subscription plans
- **Profiles**: Create multiple profiles per account (based on subscription tier)
- **Content Browsing**: Search and filter movies and TV shows by type, genre, and year
- **Wishlist**: Add and manage favorite content
- **Viewing History**: Track watch progress for movies and TV episodes
- **Multi-format Support**: Access content in different resolutions and languages

### Administrative Features
- **Admin Authentication**: Secure admin login with separate JWT tokens
- **Subscription Management**: Create and modify subscription tiers
- **Content Management**: Add, update, and delete movies and TV shows
- **Genre Management**: Create genres and link them to content
- **Media Files**: Manage multiple video files per content (resolutions, languages)
- **Season & Episode Management**: Full TV show episode management
- **Account Management**: View and manage user accounts

## Database Schema

### Core Tables
- **accounts**: User accounts with authentication
- **subscriptions**: Subscription plans (Basic, Standard, Premium)
- **profiles**: User profiles with age ratings
- **content**: Movies and TV shows
- **genres**: Content categories
- **media_files**: Video files in various formats
- **seasons**: TV show seasons
- **episodes**: Individual episodes
- **wishlist**: User saved content
- **viewing_history**: Watch progress tracking
- **admins**: Administrative users

## Default Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Subscription Plans
| Plan | Price/Month | Max Profiles |
|------|-------------|--------------|
| Basic | $9.99 | 1 |
| Standard | $15.99 | 2 |
| Premium | $19.99 | 4 |

### PostgreSQL (Docker)
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `streaming_service`
- **Username**: `postgres`
- **Password**: `postgres`

## API Overview

### Customer Endpoints
- Authentication: `/api/auth/*`
- Account: `/api/account/*`
- Profiles: `/api/profiles/*`
- Content: `/api/content/*`
- Wishlist: `/api/profiles/{id}/wishlist/*`
- History: `/api/profiles/{id}/history/*`

### Admin Endpoints
- Authentication: `/api/admin/login`
- Subscriptions: `/api/admin/subscriptions/*`
- Content: `/api/admin/content/*`
- Genres: `/api/admin/genres/*`
- Media: `/api/admin/media/*`
- Seasons/Episodes: `/api/admin/seasons/*, /api/admin/episodes/*`
- Accounts: `/api/admin/accounts/*`

## Documentation

For detailed API documentation including request/response formats, authentication flows, and example workflows, see [TESTING.md](TESTING.md).

## Testing

### Database Setup Script (`setup_database.py`)
- Automatically waits for Docker PostgreSQL to be ready
- Creates all database tables from scratch
- Populates seed data including subscription plans, admin account, sample genres, movies, and TV shows

### Admin Service Test (`test_admin_service.py`)
Tests administrative operations:
- Admin authentication
- Creating subscription plans
- Managing genres
- Adding movies and TV shows
- Creating seasons and episodes
- Managing media files

### User Workflow Test (`test_user_workflow.py`)
Tests complete user journey:
- User registration and login
- Subscription selection
- Profile creation
- Content browsing and filtering
- Wishlist management
- Watching movies and TV shows
- Viewing history tracking

## Security Features

- **Password Hashing**: BCrypt encryption for all passwords
- **JWT Authentication**: Secure token-based authentication
- **Authorization**: Role-based access control (customer vs admin)
- **Input Validation**: Request data validation
- **SQL Injection Protection**: Parameterized queries via psycopg2

## Environment Variables

Configure the application using environment variables:

```bash
export DB_HOST=localhost          # Database host
export DB_PORT=5432               # Database port
export DB_NAME=streaming_service  # Database name
export DB_USER=postgres           # Database user
export DB_PASSWORD=postgres       # Database password
export SECRET_KEY=your-secret-key # JWT secret key
```

## Example Usage

### User Registration and Login
```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'
```

### Browse Content
```bash
# Get all movies
curl http://localhost:5000/api/content?type=Movie

# Filter by genre
curl http://localhost:5000/api/content?genre=Action

# Filter by year
curl http://localhost:5000/api/content?year=2024
```

### Admin Operations
```bash
# Admin login
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Create content (use token from login)
curl -X POST http://localhost:5000/api/admin/content \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Movie",
    "type": "Movie",
    "description": "Description here",
    "release_year": 2024
  }'
```

## Technology Stack

- **Framework**: Flask 3.0
- **Database**: PostgreSQL 15 (Dockerized)
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: BCrypt
- **Database Driver**: psycopg2
- **Containerization**: Docker & Docker Compose
- **Testing**: Requests library

## Deliverables

Implemented features:

- Complete route implementation: all documented API routes
- Database integration with PostgreSQL using psycopg2
- Dockerized PostgreSQL service
- Database setup script to create schema and seed data
- Admin operations (subscriptions, content, genres, media files)
- User workflow endpoints and content browsing
- Testing guidance and example scripts in TESTING.md

## Key Implementation Details

- **Authentication Decorators**: `@token_required` and `@admin_token_required`
- **Docker Integration**: PostgreSQL runs in isolated Docker container
- **Database Connection Handling**: Automatic retry logic for Docker startup
- **Error Handling**: Comprehensive try-catch blocks with rollback
- **RESTful Design**: Proper HTTP methods and status codes
- **Input Validation**: Required field checking and type validation
- **Cascade Operations**: Proper foreign key relationships with cascading deletes

## Troubleshooting

### PostgreSQL Container Not Starting
```bash
# Check Docker is running
docker --version

# View container logs
docker-compose logs postgres

# Restart containers
docker-compose restart
```

### Cannot Connect to Database
```bash
# Verify PostgreSQL is ready
docker exec -it streaming_db pg_isready -U postgres

# Check if port 5432 is already in use
lsof -i :5432  # On Mac/Linux
netstat -ano | findstr :5432  # On Windows

# If port is in use, stop other PostgreSQL instances or modify docker-compose.yml
```

### Database Already Exists Error
```bash
# Reset database completely
docker-compose down -v
docker-compose up -d
python setup_database.py
```

### Module Not Found Errors
```bash
# Install all requirements
pip install -r requirements.txt
```

### Wrong `jwt` package installed

If you see an error like `AttributeError: module 'jwt' has no attribute 'encode'`, uninstall the incorrect `jwt` package and install `PyJWT`:

```powershell
python -m pip uninstall jwt -y
python -m pip install PyJWT==2.8.0
```

### Token Invalid Errors
- Tokens expire - login again to get a new token
- Ensure token is properly formatted: `Bearer YOUR_TOKEN`
- Check that you're using the right token type (customer vs admin)

## Support

For detailed API usage, authentication flows, and troubleshooting, refer to [TESTING.md](TESTING.md).

## License

This project is provided for educational purposes.

---

## Complete Setup Workflow

```bash
# 1. Start PostgreSQL in Docker
docker-compose up -d

# 2. Wait for PostgreSQL to be ready (automatic in setup script)
# Or manually check:
docker exec -it streaming_db pg_isready -U postgres

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Initialize database
python setup_database.py

# 5. Run Flask application
python app.py

# 6. In a separate terminal, run testing script
python run_all_tests.py

# 7. When done, stop PostgreSQL
docker-compose down
```
