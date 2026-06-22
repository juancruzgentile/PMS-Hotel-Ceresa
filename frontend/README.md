# Ceresa Frontend

Frontend workspace for the Ceresa PMS web application.

## Structure

```text
src/
  api/              HTTP client and endpoint wrappers
  app/              App shell, providers, router and layouts
  features/         Business modules grouped by Ceresa domain
  shared/           Reusable UI, hooks, utilities and constants
  styles/           Global CSS and design tokens
  types/            Shared TypeScript contracts
```

## Commands

```bash
npm install
npm run dev
```

The development server runs on `http://localhost:5173` and proxies `/api/*`
to the FastAPI backend at `http://localhost:8000`.
