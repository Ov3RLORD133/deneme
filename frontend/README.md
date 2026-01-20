# KeyChaser Frontend - Operator Console

> High-performance React dashboard for real-time malware C2 traffic analysis

## 🎨 Design Philosophy

**"The Red Team Aesthetic"** - A dark ops, cyberpunk-inspired interface for security analysts. Every pixel is designed for maximum information density and rapid threat assessment.

### Visual Identity
- **Background**: Deep black (`#050505`) for reduced eye strain during long analysis sessions
- **Accents**: 
  - Neon Green (`#00ff41`) for active beacons and success states
  - Crimson Red (`#ff0000`) for threats and malware detection
  - Cyan (`#00f3ff`) for data streams and interactive elements
- **Typography**: JetBrains Mono throughout for terminal authenticity

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running KeyChaser backend on `localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## 🏗️ Architecture

### Tech Stack
- **React 18** with TypeScript for type-safe components
- **Vite** for lightning-fast HMR and optimized builds
- **TailwindCSS** for utility-first styling
- **React Query** for intelligent API state management
- **React-Leaflet** for geospatial visualization
- **Native WebSocket** for real-time event streaming

### Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── BotDataGrid.tsx  # Bot list table
│   │   ├── DashboardLayout.tsx  # Main layout
│   │   ├── HexViewer.tsx    # Hex payload inspector
│   │   ├── InfectionMap.tsx # GeoIP map
│   │   └── LiveTerminal.tsx # WebSocket event stream
│   ├── hooks/
│   │   └── useKeyChaserSocket.ts  # WebSocket management
│   ├── lib/
│   │   └── api.ts           # Axios API client
│   ├── types/
│   │   └── index.ts         # TypeScript definitions
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## 🔌 Core Features

### 1. Real-Time WebSocket Integration

The `useKeyChaserSocket` hook manages persistent WebSocket connections:

```typescript
const { isConnected, lastMessage, messages } = useKeyChaserSocket({
  url: 'ws://localhost:8000/ws/events',
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
});
```

**Features:**
- Automatic reconnection with exponential backoff
- Message buffering (last 100 events)
- Connection state management
- Type-safe event parsing

### 2. HexViewer Component

Advanced binary data inspector for malware payload analysis:

```tsx
<HexViewer 
  data={payloadBytes}
  bytesPerRow={16}
  showAscii={true}
  showOffset={true}
/>
```

**Features:**
- Interactive byte selection
- Hover highlighting synchronized between hex and ASCII
- Copyable hex strings
- Offset display (hex and decimal)
- Detailed byte info panel

### 3. Live Terminal

Scrolling event log with filtering and export:

```tsx
<LiveTerminal />
```

**Features:**
- Auto-scroll with pause control
- Event type filtering
- Export to text file
- Color-coded event types
- Real-time connection status

### 4. Infection Map

Dark-themed global map showing bot locations:

```tsx
<InfectionMap bots={botsWithGeo} />
```

**Features:**
- CartoDB Dark Matter tiles
- Custom bot markers
- Interactive popups with bot details
- Automatic clustering for dense areas

### 5. Bot DataGrid

Sortable, filterable table of infected machines:

```tsx
<BotDataGrid 
  onBotSelect={(bot) => console.log(bot)}
  protocol="AgentTesla"
/>
```

**Features:**
- Multi-column sorting
- Activity status indicators
- Click-to-inspect details
- Protocol filtering
- Auto-refresh every 10 seconds

## 🎨 Styling System

### Custom CSS Classes

```css
/* Terminal output styling */
.terminal-output

/* Glowing text effects */
.glow-green
.glow-red  
.glow-cyan

/* Border glow effects */
.border-glow-green
.border-glow-red

/* Hex viewer byte */
.hex-byte
.hex-byte.selected

/* Status indicators */
.status-dot
.status-active
.status-inactive
.status-alert

/* Operational UI cards */
.ops-card
.ops-card-header
.ops-button
.ops-button-primary
.ops-button-danger
.ops-input
```

### Tailwind Extensions

Custom colors available in Tailwind:
- `bg-ops-black` - `#050505`
- `bg-ops-gray` - `#1a1a1a`
- `border-ops-border` - `#333333`
- `text-ops-green` - `#00ff41`
- `text-ops-red` - `#ff0000`
- `text-ops-cyan` - `#00f3ff`

## 🔗 API Integration

### REST Endpoints

The `api.ts` client provides typed methods for all backend endpoints:

```typescript
import { botsApi, logsApi, statsApi } from '@/lib/api';

// Fetch bots
const bots = await botsApi.list({ protocol: 'AgentTesla' });

// Search logs
const logs = await logsApi.search('password');

// Get statistics
const stats = await statsApi.overview();
```

### WebSocket Events

Event types received from backend:

```typescript
enum WebSocketEventType {
  NEW_BEACON = 'new_beacon',
  NEW_LOG = 'new_log',
  NEW_CREDENTIAL = 'new_credential',
  BOT_UPDATE = 'bot_update',
}
```

## 🔧 Configuration

### Environment Variables

Create `.env` in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/events
```

### Proxy Configuration

Vite proxy (for development) in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    },
  },
}
```

## 🧪 Development

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Building

```bash
npm run build
```

Output in `dist/` directory.

## 🎯 Key Components Deep Dive

### useKeyChaserSocket Hook

Custom hook for WebSocket management:

**Returns:**
- `isConnected: boolean` - Connection state
- `lastMessage: WebSocketEvent | null` - Most recent event
- `messages: WebSocketEvent[]` - Message buffer (last 100)
- `sendMessage: (data) => void` - Send data to server
- `clearMessages: () => void` - Clear message buffer
- `reconnect: () => void` - Manual reconnection trigger
- `connectionAttempts: number` - Reconnection attempt count

**Options:**
- `url: string` - WebSocket endpoint
- `reconnectInterval: number` - Delay between reconnection attempts (ms)
- `maxReconnectAttempts: number` - Max reconnection tries
- `onConnect: () => void` - Connection callback
- `onDisconnect: () => void` - Disconnection callback
- `onError: (error) => void` - Error callback

### HexViewer Component

**Props:**
- `data: Uint8Array | string` - Binary data or string to display
- `bytesPerRow?: number` - Bytes per row (default: 16)
- `showAscii?: boolean` - Show ASCII column (default: true)
- `showOffset?: boolean` - Show offset column (default: true)
- `className?: string` - Additional CSS classes

**State:**
- Tracks selected byte index
- Tracks hovered byte index
- Copy-to-clipboard functionality

### LiveTerminal Component

**Features:**
- Pause/resume auto-scroll
- Event type filtering dropdown
- Export logs to text file
- Clear message buffer
- Connection status indicator
- Relative timestamps

### InfectionMap Component

**Props:**
- `bots: BotWithGeo[]` - Bots with latitude/longitude
- `className?: string` - Additional CSS classes

**Requirements:**
- Bots must have `latitude` and `longitude` fields
- Uses React-Leaflet for map rendering
- Custom marker icon for bot locations

## 🚨 Known Limitations

1. **GeoIP Data**: Frontend currently expects geolocation data from backend. You'll need to integrate a GeoIP service (MaxMind, IP2Location) in the Python backend.

2. **WebSocket Reconnection**: Max reconnection attempts prevent infinite loops. Consider implementing exponential backoff in production.

3. **Message Buffer**: LiveTerminal keeps only last 100 messages in memory to prevent memory leaks during long sessions.

4. **Map Performance**: With 1000+ bots, consider implementing marker clustering (react-leaflet-cluster).

## 🔮 Future Enhancements

- [ ] WebSocket authentication (JWT tokens)
- [ ] User preferences persistence (localStorage)
- [ ] Advanced filtering (date ranges, regex search)
- [ ] Chart/graph visualizations (ApexCharts)
- [ ] Dark/light theme toggle
- [ ] Export reports (PDF, CSV)
- [ ] Alerting system (browser notifications)
- [ ] Multi-language support

## 📚 Resources

- [React Query Docs](https://tanstack.com/query/latest)
- [React-Leaflet Docs](https://react-leaflet.js.org/)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [Vite Docs](https://vitejs.dev/)

---

**Built for security researchers, by security researchers.**

*Warning: This tool is for authorized research only. Always obtain proper authorization before deploying in any environment.*
