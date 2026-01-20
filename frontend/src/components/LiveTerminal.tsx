/**
 * LiveTerminal Component - Real-Time Event Stream
 * 
 * Displays WebSocket events in a terminal-style scrolling window.
 * Features auto-scroll, pause/resume, and event filtering.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Pause, Play, Trash2, Download } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { WebSocketEvent, WebSocketEventType } from '@/types';
import { useKeyChaserSocket } from '@/hooks/useKeyChaserSocket';

export const LiveTerminal: React.FC = () => {
  const { isConnected, messages, clearMessages } = useKeyChaserSocket();
  const [isPaused, setIsPaused] = useState(false);
  const [filter, setFilter] = useState<WebSocketEventType | 'all'>('all');
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive (unless paused)
  useEffect(() => {
    if (!isPaused && terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [messages, isPaused]);

  /**
   * Get color class for event type
   */
  const getEventColor = (type: WebSocketEventType): string => {
    switch (type) {
      case 'new_beacon':
        return 'text-ops-red glow-red';
      case 'new_log':
        return 'text-ops-green';
      case 'new_credential':
        return 'text-ops-yellow';
      default:
        return 'text-ops-cyan';
    }
  };

  /**
   * Format event for display
   */
  const formatEvent = (event: WebSocketEvent): string => {
    const time = new Date(event.timestamp).toLocaleTimeString();
    const type = event.type.toUpperCase().padEnd(15);
    
    let details = '';
    if (event.type === 'new_beacon' && 'data' in event) {
      const data = event.data as any;
      details = `IP: ${data.ip_address} | Protocol: ${data.protocol}`;
    } else if (event.type === 'new_log' && 'data' in event) {
      const data = event.data as any;
      details = `Bot: ${data.bot_id} | Type: ${data.log_type}`;
    }
    
    return `[${time}] ${type} ${details}`;
  };

  /**
   * Export logs to file
   */
  const exportLogs = () => {
    const content = messages
      .map((msg) => `${msg.timestamp} - ${msg.type} - ${JSON.stringify(msg.data)}`)
      .join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `keychaser-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filter messages
  const filteredMessages = messages.filter((msg) =>
    filter === 'all' || msg.type === filter
  );

  return (
    <div className="ops-card h-full flex flex-col">
      {/* Header */}
      <div className="ops-card-header">
        <div className="flex items-center gap-2">
          <span className="status-dot" className={isConnected ? 'status-active' : 'status-inactive'} />
          <span>Live Event Stream</span>
          <span className="text-gray-500 text-[10px]">
            ({filteredMessages.length} events)
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as WebSocketEventType | 'all')}
            className="ops-input py-1 px-2 text-[10px]"
          >
            <option value="all">All Events</option>
            <option value="new_beacon">New Beacons</option>
            <option value="new_log">New Logs</option>
            <option value="new_credential">Credentials</option>
          </select>

          {/* Controls */}
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="ops-button py-1 px-2"
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          </button>
          
          <button
            onClick={exportLogs}
            className="ops-button py-1 px-2"
            title="Export logs"
          >
            <Download className="w-3 h-3" />
          </button>
          
          <button
            onClick={clearMessages}
            className="ops-button-danger py-1 px-2"
            title="Clear logs"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-auto font-mono text-xs leading-relaxed"
      >
        {filteredMessages.length === 0 ? (
          <div className="text-gray-600 text-center py-8">
            {isConnected ? 'Waiting for events...' : 'Connecting to event stream...'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredMessages.map((event, index) => (
              <div
                key={index}
                className={`log-entry-new px-2 py-1 hover:bg-ops-gray hover:bg-opacity-50 transition-colors ${
                  index === filteredMessages.length - 1 ? 'font-semibold' : ''
                }`}
              >
                <span className={getEventColor(event.type)}>
                  {formatEvent(event)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="border-t border-ops-border pt-2 mt-2 flex items-center justify-between text-[10px] text-gray-500">
        <div>
          {isConnected ? (
            <span className="text-ops-green">● CONNECTED</span>
          ) : (
            <span className="text-ops-red">● DISCONNECTED</span>
          )}
        </div>
        {isPaused && (
          <div className="text-ops-yellow animate-pulse">
            ⏸ PAUSED
          </div>
        )}
        <div>
          Last update: {messages.length > 0 ? formatDistanceToNow(new Date(messages[messages.length - 1].timestamp), { addSuffix: true }) : 'Never'}
        </div>
      </div>
    </div>
  );
};

export default LiveTerminal;
