# GuardianAI Frontend

React + TypeScript frontend dashboard for GuardianAI LLM monitoring platform.

## Features

- **Real-time Dashboard**: Live metrics and health score monitoring
- **Threat Detection**: Visual threat timeline and incident management
- **Trace Viewer**: Searchable LLM request trace history
- **Analytics**: Deep dive into cost, performance, and quality metrics
- **Dark Mode**: Full dark mode support with system preference detection
- **WebSocket Updates**: Real-time data streaming from backend
- **Responsive Design**: Mobile-friendly responsive UI

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- Recharts (data visualization)
- React Router v6
- Vite (build tool)
- date-fns (date formatting)
- lucide-react (icons)

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── charts/      # Chart components
│   ├── ErrorBoundary.tsx
│   ├── Header.tsx
│   ├── Layout.tsx
│   ├── Sidebar.tsx
│   ├── StatCard.tsx
│   └── ThreatTimeline.tsx
├── contexts/        # React contexts
│   ├── ThemeContext.tsx
│   └── WebSocketContext.tsx
├── pages/           # Page components
│   ├── Analytics.tsx
│   ├── Dashboard.tsx
│   ├── Incidents.tsx
│   ├── Settings.tsx
│   ├── Threats.tsx
│   └── Traces.tsx
├── services/        # API services
│   └── api.ts
├── App.tsx          # Main app component
├── index.css        # Global styles
└── main.tsx         # Entry point
```

## Key Features

### Real-time Updates
The dashboard uses WebSocket connections to receive real-time updates for:
- Health scores
- New threats
- Incident creation
- Telemetry data

### Theme Support
Automatic dark mode detection with manual toggle. Theme preference is persisted to localStorage.

### Error Handling
React Error Boundary catches and displays errors gracefully with recovery options.

## API Integration

The frontend communicates with the GuardianAI backend API:
- Health checks
- Metrics aggregation
- Incident management
- Threat detection results
- Telemetry traces
- Auto-remediation triggers
