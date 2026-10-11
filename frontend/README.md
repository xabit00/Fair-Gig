# FairGig frontend

Vite and React Router application shell with login, worker registration, refresh-token handling, role-protected routes, responsive navigation, and Level 1 placeholder pages.

## Run on Windows

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The auth API defaults to `http://localhost:8001`; override it with `VITE_AUTH_API_URL` before starting Vite.

## Production build

```powershell
cd frontend
npm run build
```
