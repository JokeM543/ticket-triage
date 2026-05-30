# Ticket Triage

Кратко: MVP-сервис для автоматической классификации, приоритизации и сохранения обращений клиентов с помощью AI.

AI support-ticket triage MVP with:

- FastAPI backend for ticket submission and AI classification
- OpenAI + Instructor structured output
- Supabase ticket storage
- Streamlit dashboard for demo submission and support queue review

## Local Setup

Create `.env` from the example:

```bash
cp .env.example .env
```

Required values:

```env
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_server_key
API_BASE_URL=http://127.0.0.1:8000
```

`SUPABASE_URL` must be the base project URL only. Do not include `/rest/v1`.

Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
streamlit run dashboard.py
```

## Remote Deployment

This repo is set up for a two-service deployment:

1. Backend API on Render
2. Dashboard on Streamlit Community Cloud

### Backend: Render

Use `render.yaml` as a Render Blueprint, or create a Python web service manually with:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables in Render:

```env
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_server_key
```

After deployment, copy the backend URL, for example:

```text
https://ticket-triage-api.onrender.com
```

### Dashboard: Streamlit Community Cloud

Create a Streamlit app from this GitHub repository:

- Branch: `main`
- Main file path: `dashboard.py`

Set these Streamlit secrets as root-level values:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your_supabase_server_key"
API_BASE_URL = "https://your-render-backend-url.onrender.com"
```

The remote dashboard must use the deployed backend URL for `API_BASE_URL`; `http://127.0.0.1:8000` only works locally.
