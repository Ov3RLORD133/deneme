/**
 * KeyChaser Frontend Type Definitions
 * 
 * Strictly typed interfaces matching the FastAPI backend schemas.
 */

export interface Bot {
  id: number;
  ip_address: string;
  port: number;
  protocol: string;
  bot_id: string | null;
  hostname: string | null;
  username: string | null;
  os_info: string | null;
  malware_version: string | null;
  campaign_id: string | null;
  extra_data: string | null;
  first_seen: string;
  last_seen: string;
  created_at: string;
}

export interface Log {
  id: number;
  bot_id: number;
  log_type: string;
  window_title: string | null;
  keystroke_data: string | null;
  application: string | null;
  url: string | null;
  raw_data: string | null;
  captured_at: string | null;
  received_at: string;
  created_at: string;
}

export interface Credential {
  id: number;
  bot_id: number;
  cred_type: string;
  url: string | null;
  username: string | null;
  password: string | null;
  email: string | null;
  application: string | null;
  token: string | null;
  cookie_data: string | null;
  captured_at: string | null;
  received_at: string;
  created_at: string;
}

export interface StatsOverview {
  total_bots: number;
  active_bots: number;
  total_logs: number;
  total_credentials: number;
  protocols: Record<string, number>;
  timestamp: string;
}

export interface ProtocolStats {
  protocol: string;
  bots: number;
  logs: number;
  credentials: number;
  last_activity: string | null;
}

export interface TopIP {
  ip: string;
  count: number;
}

export interface TimelineData {
  hour: string;
  count: number;
}

export interface Timeline {
  bots: TimelineData[];
  logs: TimelineData[];
  hours: number;
}

/**
 * WebSocket Event Types
 */
export enum WebSocketEventType {
  NEW_BEACON = 'new_beacon',
  NEW_LOG = 'new_log',
  NEW_CREDENTIAL = 'new_credential',
  BOT_UPDATE = 'bot_update',
  CONNECTION = 'connection',
  ERROR = 'error',
}

export interface WebSocketEvent {
  type: WebSocketEventType;
  timestamp: string;
  data: unknown;
}

export interface NewBeaconEvent extends WebSocketEvent {
  type: WebSocketEventType.NEW_BEACON;
  data: {
    bot_id: number;
    ip_address: string;
    protocol: string;
    hostname?: string;
  };
}

export interface NewLogEvent extends WebSocketEvent {
  type: WebSocketEventType.NEW_LOG;
  data: {
    log_id: number;
    bot_id: number;
    log_type: string;
    preview: string;
  };
}

export interface NewCredentialEvent extends WebSocketEvent {
  type: WebSocketEventType.NEW_CREDENTIAL;
  data: {
    credential_id: number;
    bot_id: number;
    cred_type: string;
    url?: string;
  };
}

/**
 * UI State Types
 */
export interface BotWithGeo extends Bot {
  country?: string;
  country_code?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
}

export interface HexViewerData {
  bytes: Uint8Array;
  selectedOffset: number | null;
}

export interface FilterState {
  protocol?: string;
  bot_id?: number;
  search?: string;
  timeRange?: '1h' | '24h' | '7d' | '30d' | 'all';
}
