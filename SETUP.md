 ## ResumeCoach - Setup Guide

### Prerequisites
- Node.js 20+ (recommended) or 22
- npm 9+
- Windows, macOS, or Linux

### 1) Install
```bash
npm ci
```

### 2) Environment
Set your Gemini API key (choose one env var):

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY = 'YOUR_GEMINI_KEY'
```

macOS/Linux:
```bash
export GEMINI_API_KEY=YOUR_GEMINI_KEY
```

Optional alternatives supported by server:
- `GOOGLE_API_KEY`

### 3) Development run (single server, serves API + Vite client)
```powershell
$env:NODE_ENV='development'; npx tsx server/index.ts
```
```bash
NODE_ENV=development npx tsx server/index.ts
```
Then open: http://localhost:5000

Notes:
- On Windows, the server listens without reusePort to avoid ENOTSUP.
- If you see EADDRINUSE, a previous instance is running. Stop it or use another port (see below).

### 4) Changing the port
```powershell
$env:PORT='5050'; npx tsx server/index.ts
```
```bash
PORT=5050 npx tsx server/index.ts
```
Open: http://localhost:5050

### 5) Production build and start
```bash
npm run build
npm start
```
The build command bundles the client with Vite and the server with esbuild.

### 6) Using the app
1. Go to Upload page, upload PDF/DOC/DOCX/TXT
2. The server extracts text, calls Gemini (or uses graceful mock fallback if rate-limited), stores results
3. Dashboard shows ATS score, interview questions, roadmap, and progress

### 7) Troubleshooting
- ENOTSUP on Windows when starting: fixed by code (reusePort disabled on win32). Update repo and retry.
- EADDRINUSE: another process bound the port.
  - Kill existing: close previous terminal or change the port via `PORT`.
  - Check: on Windows, `Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess`.
- 404 dashboard: upload a resume first to generate data.
- Missing Gemini key: set `GEMINI_API_KEY` before starting.

### 8) Optional clean-up
- Remove dev/reference assets: delete `attached_assets/`
- Clear uploaded files: delete contents of `uploads/` (files are cleaned after processing; any left are safe to remove)

### 9) Scripts
```json
{
  "dev": "NODE_ENV=development tsx server/index.ts",
  "build": "vite build && esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist",
  "start": "NODE_ENV=production node dist/index.js",
  "check": "tsc",
  "db:push": "drizzle-kit push"
}
```

### 10) Tech stack
- Express + Vite middleware (dev)
- React 18 + Tailwind + Radix UI
- Drizzle ORM (schemas in `shared/schema.ts`)
- Google Gemini via `@google/genai`








$env:GEMINI_API_KEY = 'AIzaSyCRULzE_qBnPBjZgYwkoeNDydSWDhDtrhU'


## http://localhost:5050