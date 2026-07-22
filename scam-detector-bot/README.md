# CyberSheild-AI — Frontend

React 18 + Vite + TypeScript + Tailwind v4 + Framer Motion frontend for the CyberSheild-AI scam detector.

## Quick Start

```bash
npm install
npm run dev
```

## Connect to Backend

Copy `.env.example` to `.env` and set the API URL:

```
VITE_API_BASE_URL=http://localhost:8000
```

Open http://localhost:5173

## Build

```bash
npm run build
```

## Features

- **Message analysis** — Paste scam messages for real-time AI risk analysis
- **Risk visualization** — Animated score circle, red flags, confidence breakdown
- **Chat interface** — WhatsApp-style UI with user/bot messages
- **Sidebar** — Dashboard stats, scan history timeline, quick links
- **Modals** — Settings drawer, post-scam support, detailed analysis
- **Backend API** — Connects to FastAPI + Claude backend (falls back to local analyzer if offline)
- **Responsive** — Desktop sidebar, tablet icon-only, mobile drawer
- **Accessible** — ARIA labels, keyboard nav, WCAG AA contrast

## Architecture

```
src/
├── components/
│   ├── Cards/       # RiskBadge, RiskScoreCircle, RedFlagsList, etc.
│   ├── Chat/        # ChatContainer, UserMessage, BotRiskCard, etc.
│   ├── Layout/      # MainLayout, Header, Sidebar
│   ├── Modals/      # SettingsDrawer, DetailModal, PostScamSupportModal
│   ├── Sidebar/     # SidebarTabs, DashboardPane, ScamHistoryPane
│   └── UI/          # Button, Badge, Chip, TabNavigation
├── context/         # SettingsContext, ChatContext, ModalContext
├── hooks/           # useChat, useModal, useSettings, useDebouncedValue
├── lib/             # api.ts (backend client), analyzer.ts (local fallback), risk.ts
├── types/           # TypeScript interfaces
└── styles/          # Tailwind v4 globals.css with @theme tokens
```
