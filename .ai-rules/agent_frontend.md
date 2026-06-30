# Frontend Agent

The Frontend Agent keeps CERESA UI work aligned with the current Vite, React, and TypeScript application.

Rules:

- Use the current Vite, React, and TypeScript stack.
- Reuse patterns already used in Reception MVP, Guests, Reservations, and Rooms.
- Do not introduce heavy libraries without justification.
- Centralize API calls.
- Show loading, error, and empty states.
- Keep the UI functional before adding advanced design.
- Run the frontend build with:

```powershell
cd frontend
npm.cmd run build
cd ..
```

- On Windows, use `npm.cmd`.
- Do not treat `actor_user_id` as real authentication.
