# CERESA Frontend Agent Instructions

## Scope

- Applies to everything inside `frontend/`.

## Stack

- Vite.
- React.
- TypeScript.
- React Router.
- TanStack Query if already configured.
- Centralized API client.

## Commands

```powershell
npm.cmd run dev
npm.cmd run build
```

## Rules

- Do not introduce heavy libraries without justification.
- Do not duplicate HTTP clients.
- Keep endpoints centralized.
- Show API errors on screen.
- Prioritize functional flows.
- Keep components simple and readable.
- Do not treat `actor_user_id` as real authentication.
- Do not commit `dist`, `node_modules`, `.vite`, `*.tsbuildinfo`, `vite.config.js`, or `vite.config.d.ts`.

## Reception MVP

- The Reception MVP screen exists.
- It must allow testing the guest -> room -> reservation -> billing -> payment -> check-in -> check-out -> audit events flow.
- Demo codes must avoid collisions.
- The actor user ID is optional and manual for now.
