# Streaming Service API - Testing Documentation

## Table of Contents
1. [Setup Instructions](#setup-instructions)
2. [Running the Application](#running-the-application)
3. [API Authentication](#api-authentication)
4. [Customer API Endpoints](#customer-api-endpoints)
5. [Admin API Endpoints](#admin-api-endpoints)
6. [Testing Scripts](#testing-scripts)
7. [Example Workflows](#example-workflows)

---

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+
- pip (Python package manager)

### Installation Steps

1. **Start PostgreSQL in Docker**
```bash
# Start the PostgreSQL container
docker-compose up -d

# Verify container is running
docker ps

# Check PostgreSQL logs (optional)
docker-compose logs postgres
```

2. **Install Required Python Packages**
```bash
pip install -r requirements.txt
# Or manually:
# pip install flask psycopg2-binary bcrypt pyjwt requests
```

3. **Configure Environment Variables (Optional)**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=streaming_service
export DB_USER=postgres
export DB_PASSWORD=postgres
export SECRET_KEY=your-secret-key-here
```

4. **Initialize the Database**
```bash
python setup_database.py
```

The script will automatically wait for PostgreSQL to be ready, then create all tables and populate seed data including:
- 3 subscription plans (Basic, Standard, Premium)
- Default admin account (username: `admin`, password: `admin123`)
- Sample genres, content, and media files

### Docker Management

**Stop PostgreSQL:**
```bash
docker-compose down
```

**Stop and remove all data (fresh start):**
```bash
docker-compose down -v
docker-compose up -d
python setup_database.py
```

**View logs:**
```bash
docker-compose logs -f postgres
```

**Access PostgreSQL CLI:**
```bash
docker exec -it streaming_db psql -U postgres -d streaming_service
```

---

## Running the Application

### Start the Flask Server
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Verify Server is Running
```bash
curl http://localhost:5000/api/content
```

---

## API Authentication

### Customer Authentication
Customer endpoints require a JWT token in the Authorization header:

**Register a new account:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Response includes a `token` field. Use it in subsequent requests:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5000/api/account
```

### Admin Authentication
Admin endpoints require an admin JWT token:

**Admin Login:**
```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

---

## Customer API Endpoints

### Authentication

#### Register
- **POST** `/api/auth/register`
- **Body:** `{"email": "string", "password": "string"}`
- **Response:** `{"account_id": int, "email": string, "subscription_id": null, "token": string}`

#### Login
- **POST** `/api/auth/login`
- **Body:** `{"email": "string", "password": "string"}`
- **Response:** `{"account_id": int, "email": string, "subscription_id": int, "token": string}`

#### Get Current User
- **GET** `/api/auth/me`
- **Headers:** `Authorization: Bearer TOKEN`
- **Response:** `{"account_id": int, "email": string, "subscription_id": int, "created_at": timestamp}`

### Account Management

#### Get Account
- **GET** `/api/account`
- **Headers:** `Authorization: Bearer TOKEN`

#### Update Account
- **PUT** `/api/account`
- **Headers:** `Authorization: Bearer TOKEN`
- **Body:** `{"email": "string" (optional), "password": "string" (optional)}`

#### Get Subscription
- **GET** `/api/account/subscription`
- **Headers:** `Authorization: Bearer TOKEN`

#### Update Subscription
- **PUT** `/api/account/subscription`
- **Headers:** `Authorization: Bearer TOKEN`
- **Body:** `{"subscription_id": int}`

### Profiles

#### List Profiles
- **GET** `/api/profiles`
- **Headers:** `Authorization: Bearer TOKEN`

#### Create Profile
- **POST** `/api/profiles`
- **Headers:** `Authorization: Bearer TOKEN`
- **Body:** `{"name": "string", "age_rating_pref": "string"}`

#### Get Profile
- **GET** `/api/profiles/{profile_id}`
- **Headers:** `Authorization: Bearer TOKEN`

#### Update Profile
- **PUT** `/api/profiles/{profile_id}`
- **Headers:** `Authorization: Bearer TOKEN`
- **Body:** `{"name": "string" (optional), "age_rating_pref": "string" (optional)}`

#### Delete Profile
- **DELETE** `/api/profiles/{profile_id}`
- **Headers:** `Authorization: Bearer TOKEN`

### Content Browsing

#### Browse Content
- **GET** `/api/content`
- **Query Params:** `type` (Movie/Show), `genre` (string), `year` (int)
- **Example:** `/api/content?type=Movie&genre=Action&year=2024`

#### Get Content Details
- **GET** `/api/content/{content_id}`

#### Get Content Media Files
- **GET** `/api/content/{content_id}/media`

#### Get Content Genres
- **GET** `/api/content/{content_id}/genres`

#### Get TV Show Seasons
- **GET** `/api/content/{content_id}/seasons`

#### Get Season Episodes
- **GET** `/api/seasons/{season_id}/episodes`

#### Get Episode Details
- **GET** `/api/episodes/{episode_id}`

### Wishlist

#### Get Wishlist
- **GET** `/api/profiles/{profile_id}/wishlist`
- **Headers:** `Authorization: Bearer TOKEN`

#### Add to Wishlist
- **POST** `/api/profiles/{profile_id}/wishlist/{content_id}`
- **Headers:** `Authorization: Bearer TOKEN`

#### Remove from Wishlist
- **DELETE** `/api/profiles/{profile_id}/wishlist/{content_id}`
- **Headers:** `Authorization: Bearer TOKEN`

### Viewing History

#### Get History
- **GET** `/api/profiles/{profile_id}/history`
- **Headers:** `Authorization: Bearer TOKEN`

#### Get Specific History
- **GET** `/api/profiles/{profile_id}/history/{content_id}`
- **Headers:** `Authorization: Bearer TOKEN`

#### Update History
- **PUT** `/api/profiles/{profile_id}/history/{content_id}`
- **Headers:** `Authorization: Bearer TOKEN`
- **Body:** `{"last_timestamp": int}`

#### Delete History
- **DELETE** `/api/profiles/{profile_id}/history/{content_id}`
- **Headers:** `Authorization: Bearer TOKEN`

---

## Admin API Endpoints

### Admin Authentication

#### Admin Login
- **POST** `/api/admin/login`
- **Body:** `{"username": "string", "password": "string"}`

### Subscription Management

#### List Subscriptions
- **GET** `/api/admin/subscriptions`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Create Subscription
- **POST** `/api/admin/subscriptions`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"name": "string", "max_profiles": int, "monthly_price": float}`

#### Get Subscription
- **GET** `/api/admin/subscriptions/{subscription_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Update Subscription
- **PUT** `/api/admin/subscriptions/{subscription_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"name": "string" (optional), "max_profiles": int (optional), "monthly_price": float (optional)}`

#### Delete Subscription
- **DELETE** `/api/admin/subscriptions/{subscription_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

### Content Management

#### List Content
- **GET** `/api/admin/content`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Create Content
- **POST** `/api/admin/content`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"title": "string", "type": "Movie|Show", "description": "string", "release_year": int}`

#### Update Content
- **PUT** `/api/admin/content/{content_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"title": "string" (optional), "description": "string" (optional), "release_year": int (optional)}`

#### Delete Content
- **DELETE** `/api/admin/content/{content_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

### Media File Management

#### Add Media File
- **POST** `/api/admin/content/{content_id}/media`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"resolution": "string", "language": "string", "file_path": "string"}`

#### Delete Media File
- **DELETE** `/api/admin/media/{media_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

### Genre Management

#### List Genres
- **GET** `/api/admin/genres`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Create Genre
- **POST** `/api/admin/genres`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"name": "string"}`

#### Update Genre
- **PUT** `/api/admin/genres/{genre_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"name": "string"}`

#### Delete Genre
- **DELETE** `/api/admin/genres/{genre_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Link Genre to Content
- **POST** `/api/admin/content/{content_id}/genres/{genre_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Unlink Genre from Content
- **DELETE** `/api/admin/content/{content_id}/genres/{genre_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

### Seasons & Episodes

#### Create Season
- **POST** `/api/admin/content/{content_id}/seasons`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"season_number": int}`

#### Update Season
- **PUT** `/api/admin/seasons/{season_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"season_number": int}`

#### Delete Season
- **DELETE** `/api/admin/seasons/{season_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

#### Create Episode
- **POST** `/api/admin/seasons/{season_id}/episodes`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"title": "string", "episode_number": int}`

#### Update Episode
- **PUT** `/api/admin/episodes/{episode_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`
- **Body:** `{"title": "string" (optional), "episode_number": int (optional)}`

#### Delete Episode
- **DELETE** `/api/admin/episodes/{episode_id}`
- **Headers:** `Authorization: Bearer ADMIN_TOKEN`

---

## Testing Scripts

### 1. Database Setup Script
```bash
python setup_database.py
```
Creates all tables and populates seed data on an empty database.

### 2. Admin Service Test Script
```bash
python test_admin_service.py
```
Tests administrative operations:
- Admin login
- Creating subscription plans
- Managing content (movies and shows)
- Creating genres and linking them
- Creating seasons and episodes
- Managing accounts

### 3. User Workflow Test Script
```bash
python test_user_workflow.py
```
Tests complete user journey:
- User registration and login
- Subscription selection
- Profile creation
- Content browsing
- Wishlist management
- Watching movies and TV shows
- Viewing history tracking

---

## Example Workflows

### Example 1: New User Signs Up and Watches a Movie

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "pass123"}'

# Save the token from response
TOKEN="your_token_here"

# 2. Select subscription
curl -X PUT http://localhost:5000/api/account/subscription \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subscription_id": 2}'

# 3. Create profile
curl -X POST http://localhost:5000/api/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "age_rating_pref": "PG-13"}'

# Save profile_id from response
PROFILE_ID=1

# 4. Browse movies
curl http://localhost:5000/api/content?type=Movie

# 5. Add movie to wishlist
curl -X POST http://localhost:5000/api/profiles/$PROFILE_ID/wishlist/1 \
  -H "Authorization: Bearer $TOKEN"

# 6. Start watching (update progress)
curl -X PUT http://localhost:5000/api/profiles/$PROFILE_ID/history/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"last_timestamp": 1800}'
```

### Example 2: Admin Adds New Content

```bash
# 1. Admin login
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Save admin token
ADMIN_TOKEN="your_admin_token_here"

# 2. Create a new movie
curl -X POST http://localhost:5000/api/admin/content \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Action Movie",
    "type": "Movie",
    "description": "An exciting new film",
    "release_year": 2024
  }'

# Save content_id
CONTENT_ID=10

# 3. Add media files
curl -X POST http://localhost:5000/api/admin/content/$CONTENT_ID/media \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "4K",
    "language": "English",
    "file_path": "/media/new_movie_4k.mp4"
  }'

# 4. Link genres
curl -X POST http://localhost:5000/api/admin/content/$CONTENT_ID/genres/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Example 3: User Watches TV Show Episodes

```bash
# 1. Browse TV shows
curl http://localhost:5000/api/content?type=Show

# 2. Get show details (assume content_id = 4)
curl http://localhost:5000/api/content/4

# 3. Get seasons
curl http://localhost:5000/api/content/4/seasons

# 4. Get episodes from season 1 (assume season_id = 1)
curl http://localhost:5000/api/seasons/1/episodes

# 5. Watch episode 1 (track progress)
curl -X PUT http://localhost:5000/api/profiles/$PROFILE_ID/history/4 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"last_timestamp": 3600}'

# 6. Continue to episode 2
curl -X PUT http://localhost:5000/api/profiles/$PROFILE_ID/history/4 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"last_timestamp": 7200}'
```

---

## Error Responses

The API returns standard HTTP status codes:

- **200 OK**: Successful GET/PUT/DELETE
- **201 Created**: Successful POST
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error response format:
```json
{
  "error": "Description of the error"
}
```

---

## Notes

1. **Token Expiration**: Customer tokens expire after 30 days, admin tokens after 7 days
2. **Profile Limits**: Profile creation is limited based on subscription plan
3. **Content Filtering**: Use query parameters for precise content discovery
4. **Timestamps**: Viewing history timestamps are in seconds
5. **Cascade Deletes**: Deleting accounts/content will cascade to related data

---

## Troubleshooting

### PostgreSQL Docker Container Issues

```bash
# Check if Docker is running
docker --version

# Check container status
docker ps -a

# View container logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres

# Fresh start (removes all data)
docker-compose down -v
docker-compose up -d
```

### Cannot Connect to Database
```bash
# Check if PostgreSQL is ready
docker exec -it streaming_db pg_isready -U postgres

# Check if port 5432 is available
# On Mac/Linux:
lsof -i :5432
# On Windows:
netstat -ano | findstr :5432

# If port is in use, stop other PostgreSQL instances or modify docker-compose.yml
```

### Database Connection Timeout
The setup script automatically waits up to 60 seconds for PostgreSQL to be ready. If it still times out:
```bash
# Ensure Docker container is healthy
docker ps
# Should show "healthy" status

# Check PostgreSQL is accepting connections
docker exec -it streaming_db psql -U postgres -c "SELECT 1;"
```

### Token Invalid Errors
- Tokens expire - login again to get a new token
- Ensure token is properly formatted: `Bearer YOUR_TOKEN`
- Check that you're using the right token type (customer vs admin)

### Module Not Found Errors
```bash
# Install all requirements
pip install flask psycopg2-binary bcrypt pyjwt requests
```