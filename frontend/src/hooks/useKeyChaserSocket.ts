/**
 * Custom WebSocket Hook for KeyChaser Real-Time Events
 * 
 * Manages WebSocket connection lifecycle, automatic reconnection,
 * and exposes real-time events to React components.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketEvent, WebSocketEventType } from '@/types';

interface UseKeyChaserSocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseKeyChaserSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketEvent | null;
  messages: WebSocketEvent[];
  sendMessage: (data: unknown) => void;
  clearMessages: () => void;
  reconnect: () => void;
  connectionAttempts: number;
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/events';

/**
 * Hook for managing WebSocket connection to KeyChaser backend
 */
export const useKeyChaserSocket = (
  options: UseKeyChaserSocketOptions = {}
): UseKeyChaserSocketReturn => {
  const {
    url = WS_URL,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketEvent | null>(null);
  const [messages, setMessages] = useState<WebSocketEvent[]>([]);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    try {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[KeyChaser WS] Connected to event stream');
        setIsConnected(true);
        setConnectionAttempts(0);
        onConnect?.();
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as WebSocketEvent;
          
          // Add timestamp if not present
          if (!data.timestamp) {
            data.timestamp = new Date().toISOString();
          }

          setLastMessage(data);
          setMessages((prev) => [...prev.slice(-99), data]); // Keep last 100 messages

          console.log('[KeyChaser WS] Received event:', data.type, data);
        } catch (error) {
          console.error('[KeyChaser WS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error: Event) => {
        console.error('[KeyChaser WS] Error:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('[KeyChaser WS] Connection closed');
        setIsConnected(false);
        onDisconnect?.();

        // Attempt reconnection if enabled
        if (
          shouldReconnectRef.current &&
          connectionAttempts < maxReconnectAttempts
        ) {
          setConnectionAttempts((prev) => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`[KeyChaser WS] Reconnecting... (attempt ${connectionAttempts + 1})`);
            connect();
          }, reconnectInterval);
        } else if (connectionAttempts >= maxReconnectAttempts) {
          console.error('[KeyChaser WS] Max reconnection attempts reached');
        }
      };
    } catch (error) {
      console.error('[KeyChaser WS] Connection error:', error);
    }
  }, [
    url,
    reconnectInterval,
    maxReconnectAttempts,
    connectionAttempts,
    onConnect,
    onDisconnect,
    onError,
  ]);

  /**
   * Send message through WebSocket
   */
  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('[KeyChaser WS] Cannot send message: WebSocket not connected');
    }
  }, []);

  /**
   * Clear message history
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessage(null);
  }, []);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    setConnectionAttempts(0);
    connect();
  }, [connect]);

  // Initialize connection on mount
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    messages,
    sendMessage,
    clearMessages,
    reconnect,
    connectionAttempts,
  };
};

/**
 * Hook to filter messages by event type
 */
export const useFilteredMessages = (
  messages: WebSocketEvent[],
  eventType: WebSocketEventType
): WebSocketEvent[] => {
  return messages.filter((msg) => msg.type === eventType);
};

export default useKeyChaserSocket;
