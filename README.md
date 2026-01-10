# Bookly

A full-stack bookstore application with AI-powered customer support chat.

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **AI**: Claude (Anthropic API) for support chat
- **Infrastructure**: Docker, Docker Compose

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Anthropic API Key](https://console.anthropic.com/) for the chat agent

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/bookly.git
cd bookly
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 3. Start the application

```bash
docker-compose up --build
```

This will start:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432

### 4. Access the application

Open http://localhost:5173 in your browser.

## Development

### Running without Docker

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Note: You'll need a PostgreSQL database running and update `DATABASE_URL` in your environment.

### Project Structure

```
bookly/
├── backend/
│   ├── agent/          # AI chat agent logic
│   ├── api/            # FastAPI routes
│   ├── data/           # Database models and schemas
│   ├── state/          # State management
│   ├── main.py         # Application entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── store/      # Zustand state stores
│   │   └── types/      # TypeScript types
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Features

- Browse and search books
- User authentication
- Shopping cart and checkout
- Order tracking
- AI-powered support chat with:
  - Order status inquiries
  - Book recommendations
  - Return assistance
  - General support

## Stopping the Application

```bash
docker-compose down
```

To also remove the database volume:

```bash
docker-compose down -v
```
