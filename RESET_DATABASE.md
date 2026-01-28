# How to Reset Database and Reseed Data

## Problem
After removing containers with `docker-compose down`, the database volume persists. When you restart with `docker-compose up`, the seed functions detect existing (possibly empty) data and skip seeding, resulting in no books or users showing.

## Solution 1: Remove Volumes (Recommended for Fresh Start)

This completely removes all data and starts fresh:

```bash
# Stop containers and remove volumes
docker-compose down -v

# Start fresh
docker-compose up
```

This will:
- Remove all containers
- Remove the PostgreSQL volume (all data deleted)
- Create fresh containers
- Automatically seed books, users, orders, and policies

## Solution 2: Force Reseed (Keep Existing Data Structure)

If you want to reseed without removing volumes, you can force reseeding:

```bash
# Stop containers (keep volumes)
docker-compose down

# Start with force reseed environment variable
FORCE_RESeed=true docker-compose up
```

Or add to your `.env` file:
```
FORCE_RESeed=true
```

Then start normally:
```bash
docker-compose up
```

## Solution 3: Manual Reseed via Container

If containers are already running:

```bash
# Force reseed via environment variable
docker-compose exec backend bash -c "FORCE_RESeed=true python -c 'from data.database import AsyncSessionLocal; from data.seed_books import seed_books; from data.seed_users import seed_users; from data.seed_orders import seed_orders; from data.seed_policies import seed_policies; import asyncio; async def main(): async with AsyncSessionLocal() as s: await seed_books(s, force=True); await seed_users(s, force=True); await seed_orders(s, force=True); await seed_policies(s, force=True); asyncio.run(main())'"
```

Or restart the backend with the environment variable:

```bash
# Add to docker-compose.yml backend environment:
FORCE_RESeed: "true"

# Then restart
docker-compose restart backend
```

## Quick Reference

| Command | What it does |
|---------|-------------|
| `docker-compose down` | Stops containers, keeps volumes |
| `docker-compose down -v` | Stops containers, **removes volumes** (deletes data) |
| `docker-compose up` | Starts containers, seeds if empty |
| `FORCE_RESeed=true docker-compose up` | Starts containers, **forces reseed** |

## Verify Seeding

After starting, check the backend logs:

```bash
docker-compose logs backend | grep -i seed
```

You should see:
```
Generating 500 books...
Seeded 500 books successfully!
Creating 10 user profiles...
Seeded 10 user profiles successfully!
Creating ~45 orders with edge cases...
Seeded policies successfully!
```

## Demo Accounts

After seeding, you can log in with any of these accounts:
- Email: `sarah.johnson@email.com` (or any from the seed_users.py file)
- Password: `demo123`

All demo accounts use the same password: `demo123`
