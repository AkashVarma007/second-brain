# Second Brain — Web Dashboard

A small monitoring dashboard for the Second Brain: a React + Vite + TypeScript
UI over the brain's local HTTP API. It shows whether the brain is online,
lists recent notes and tasks, and can send a sample transcript to be
processed as either.

## Prerequisites

- Node 22+
- The Second Brain server running locally on `:8000`

## Setup

```bash
npm install
npm run dev    # http://localhost:5173
```

`npm run build` type-checks and produces a production build in `dist/`.

## Configuration

The API base URL is read from `VITE_API_BASE` (default
`http://localhost:8000`). Copy `.env.example` to `.env` to override it.

## API contract

The dashboard consumes the brain's HTTP API through the types in
`src/protocol.ts`, which mirrors `brain/app/models.py`.
