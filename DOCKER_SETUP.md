# Docker Setup Guide

This guide explains how to run the entire Bookly application (backend, frontend, and database) using Docker Compose with persistent database storage.

## Quick Start

### 1. Create Environment File

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `ANTHROPIC_API_KEY` - Required for Claude agent
- `OPENAI_API_KEY` - Required for OpenAI fallback
- `JWT_SECRET` - Change this in production!

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL** database (port 5432)
- **Backend** API (port 8000)
- **Frontend** dev server (port 5173)
- **Datadog Agent** (optional, for telemetry)

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Analytics Dashboard**: http://localhost:5173/analytics

## Database Persistence

✅ **Database data is automatically persisted!**

The `postgres_data` volume stores all database data. This means:
- Data persists across container restarts
- Data persists even if you remove containers
- You can backup/restore the volume

### Volume Location

The PostgreSQL data is stored in a Docker volume named `postgres_data`. You can:

**View volume:**
```bash
docker volume inspect booklyagent_postgres_data
```

**Backup database:**
```bash
docker-compose exec postgres pg_dump -U bookly bookly > backup.sql
```

**Restore database:**
```bash
docker-compose exec -T postgres psql -U bookly bookly < backup.sql
```

## Common Commands

### Start Services
```bash
docker-compose up -d          # Start in background
docker-compose up             # Start with logs
```

### Stop Services
```bash
docker-compose stop           # Stop but keep containers
docker-compose down           # Stop and remove containers (keeps volumes!)
docker-compose down -v        # Stop and remove volumes (⚠️ deletes data!)
```

### Restart Services
```bash
docker-compose restart        # Restart all
docker-compose restart backend  # Restart specific service
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build
docker-compose up -d
```

### Access Containers
```bash
# Backend shell
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U bookly bookly

# Frontend shell
docker-compose exec frontend sh
```

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Code changes trigger automatic reload (via `--reload` flag)
- **Frontend**: Vite HMR automatically updates browser

### Running Migrations/Seeding

```bash
# Seed database (first time)
docker-compose exec backend python -m data.seed_users
docker-compose exec backend python -m data.seed_books
docker-compose exec backend python -m data.seed_orders

# Seed analytics data
docker-compose exec backend python -m data.seed_analytics --days 7 --per-day 15

# Run load tests
docker-compose exec backend python -m tests.load_test_real_interactions --safe
```

## Troubleshooting

### Database Connection Issues

If backend can't connect to database:
```bash
# Check if postgres is healthy
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection manually
docker-compose exec backend python -c "from data.database import engine; print('Connected!')"
```

### Port Already in Use

If ports 8000, 5173, or 5432 are already in use:
```bash
# Option 1: Stop conflicting services
# Option 2: Change ports in docker-compose.yml
```

### Frontend Can't Connect to Backend

Check environment variables:
```bash
# In docker-compose.yml, frontend should have:
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# For Docker networking, you might need:
VITE_API_URL=http://backend:8000
VITE_WS_URL=ws://backend:8000
```

### Clear Everything and Start Fresh

⚠️ **This will delete all data!**

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d --build
```

## Production Considerations

For production, you should:

1. **Change JWT_SECRET** to a strong random value
2. **Use environment-specific .env files**
3. **Set up proper database backups**
4. **Use production Dockerfiles** (not dev mode)
5. **Configure proper CORS origins**
6. **Set up SSL/TLS**
7. **Use secrets management** (not .env files)

## Volume Management

### List Volumes
```bash
docker volume ls | grep bookly
```

### Remove Volume (⚠️ deletes data)
```bash
docker volume rm booklyagent_postgres_data
```

### Backup Volume
```bash
# Create backup
docker run --rm -v booklyagent_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore backup
docker run --rm -v booklyagent_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Network Configuration

Services communicate via Docker's internal network:
- Backend → Postgres: `postgres:5432`
- Frontend → Backend: `http://localhost:8000` (from host) or `http://backend:8000` (from container)
- Backend → Datadog: `http://datadog-agent:4318`

## Health Checks

PostgreSQL has a health check configured. Backend waits for postgres to be healthy before starting.

Check service health:
```bash
docker-compose ps
```
