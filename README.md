# Git Conflict Resolver & Impact Simulator

> AI-powered Git merge conflict analysis with visual impact mapping.

## Overview

Merge conflicts are one of the most frustrating parts of collaborative development. Reading conflict markers and understanding how changes affect the surrounding code can quickly become overwhelming, especially in large projects.

**Git Conflict Resolver & Impact Simulator** is a full-stack web application that simplifies this process by:

- Parsing Git merge conflicts
- Visualizing affected functions
- Using AI to suggest a safe merged version
- Explaining why the merge was chosen

Instead of manually comparing two versions of code, developers get an interactive view of the conflict and an AI-assisted resolution.

---

## Features

- Parse raw Git merge conflicts (`<<<<<<<`, `=======`, `>>>>>>>`)
- Separate current and incoming changes
- Detect JavaScript functions using Tree-sitter
- Visualize affected functions with an interactive graph
- Skip AI calls when changes are only formatting differences
- Generate AI-assisted merge suggestions
- Explain merge decisions in plain English
- Local fallback when AI is unavailable
- Docker support for quick deployment

---

## Tech Stack

### Frontend

- React
- Vite
- Axios
- React Flow
- CSS

### Backend

- FastAPI
- Python
- Tree-sitter
- OpenAI SDK
- Groq API

### DevOps

- Docker
- Docker Compose
- Nginx

---

## Project Structure

```text
.
├── conflict-resolver-backend/
├── conflict-resolver-frontend/
├── docker-compose.yml
└── README.md
```

---

## API

### POST `/api/resolve`

**Request**

```json
{
  "raw_text": "Git conflict text"
}
```

**Response**

```json
{
  "status": "success",
  "parsed_blocks": {},
  "graph_data": {},
  "ai_resolution": "...",
  "explanation": "..."
}
```

---

## Getting Started

### Clone the repository

```bash
git clone <repository-url>
cd <repository>
```

### Configure Environment

Create a `.env` file inside the backend:

```env
GROQ_API_KEY=your_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

### Run with Docker

```bash
docker compose up --build
```

Frontend: http://localhost:5173

Backend: http://localhost:8000

---

## Future Improvements

- Support multiple conflict blocks
- Support more programming languages
- Better dependency analysis
- Side-by-side diff viewer
- AI confidence score
- Automated testing

---

## License

MIT License
