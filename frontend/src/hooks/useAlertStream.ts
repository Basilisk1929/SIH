import { useEffect, useRef, useState, useCallback } from 'react';
import { Alert } from '../types';
import { useAuth } from '../context/AuthContext';

export interface AlertStreamOptions {
  onAlertCreated?: (alert: Alert) => void;
  onAlertUpdated?: (alert: Alert) => void;
  autoConnect?: boolean;
}

export function useAlertStream(options: AlertStreamOptions = {}) {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [latestAlert, setLatestAlert] = useState<Alert | null>(null);
  const [newAlertsQueue, setNewAlertsQueue] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef(0);

  const { onAlertCreated, onAlertUpdated, autoConnect = true } = options;

  const connect = useCallback(() => {
    if (!isAuthenticated) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      // Determine WebSocket URL from environment or API base URL
      let wsUrl = import.meta.env.VITE_WS_ALERT_URL;
      if (!wsUrl || typeof wsUrl !== 'string') {
        const apiBase = import.meta.env.VITE_API_BASE_URL;
        if (apiBase && typeof apiBase === 'string' && apiBase.startsWith('http')) {
          try {
            const parsed = new URL(apiBase);
            const wsProto = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl = `${wsProto}//${parsed.host}/alerts/ws`;
          } catch {
            // Fall back to relative host
          }
        }
        if (!wsUrl) {
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          const host = window.location.host;
          wsUrl = `${protocol}//${host}/alerts/ws`;
        }
      }

      // Append token query param if token available
      const urlWithAuth = token ? `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}token=${token}` : wsUrl;

      const ws = new WebSocket(urlWithAuth);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const eventType = payload.event_type;
          const alertData: Alert = payload.alert;

          if (eventType === 'ALERT_CREATED' && alertData) {
            setLatestAlert(alertData);
            setNewAlertsQueue((prev) => [alertData, ...prev.slice(0, 49)]);
            setUnreadCount((c) => c + 1);
            onAlertCreated?.(alertData);
          } else if (eventType === 'ALERT_UPDATED' && alertData) {
            setLatestAlert(alertData);
            onAlertUpdated?.(alertData);
          }
        } catch {
          // Non-JSON ping/pong or heartbeat
        }
      };

      ws.onerror = () => {
        setConnectionError('Real-time alert websocket error');
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        wsRef.current = null;

        // Auto-reconnect if authenticated and not a deliberate logout (code 1000)
        if (isAuthenticated && event.code !== 1000) {
          const backoffMs = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 15000);
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, backoffMs);
        }
      };
    } catch (err: any) {
      setConnectionError(err.message || 'Failed to initialize WebSocket');
    }
  }, [isAuthenticated, token, onAlertCreated, onAlertUpdated]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const markAllAsRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  useEffect(() => {
    if (autoConnect && isAuthenticated) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, isAuthenticated, connect, disconnect]);

  return {
    isConnected,
    latestAlert,
    newAlertsQueue,
    unreadCount,
    connectionError,
    markAllAsRead,
    connect,
    disconnect,
  };
}
