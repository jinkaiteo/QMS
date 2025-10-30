// Analytics WebSocket Service - Phase B Sprint 1 Day 4
// Real-time data streaming for live dashboard updates

interface AnalyticsUpdate {
  type: 'metric_update' | 'dashboard_refresh' | 'alert' | 'user_activity';
  data: any;
  timestamp: string;
  department_id?: number;
  user_id?: number;
}

class AnalyticsWebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, Function[]> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(private baseUrl: string = 'ws://localhost:8001') {}

  connect(userId: number, departmentId?: number): Promise<boolean> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.baseUrl}/analytics?userId=${userId}&departmentId=${departmentId || ''}&room=analytics`;
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
          console.log('✅ Analytics WebSocket connected');
          this.reconnectAttempts = 0;
          if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
          }
          resolve(true);
        };

        this.socket.onmessage = (event) => {
          try {
            const update: AnalyticsUpdate = JSON.parse(event.data);
            this.handleAnalyticsUpdate(update);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          console.log('⚠️ Analytics WebSocket disconnected:', event.code);
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect(userId, departmentId);
          }
        };

        this.socket.onerror = (error) => {
          console.error('❌ Analytics WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(userId: number, departmentId?: number): void {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000); // Exponential backoff, max 30s
    
    console.log(`🔄 Attempting WebSocket reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect(userId, departmentId).catch(() => {
        // Connection failed, will try again if attempts remain
      });
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
  }

  // Subscribe to specific analytics updates
  subscribe(eventType: string, callback: Function): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)?.push(callback);
  }

  // Unsubscribe from analytics updates
  unsubscribe(eventType: string, callback: Function): void {
    const eventListeners = this.listeners.get(eventType);
    if (eventListeners) {
      const index = eventListeners.indexOf(callback);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  // Handle incoming analytics updates
  private handleAnalyticsUpdate(update: AnalyticsUpdate): void {
    const listeners = this.listeners.get(update.type) || [];
    listeners.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in analytics update callback:', error);
      }
    });

    // Also trigger generic 'update' listeners
    const genericListeners = this.listeners.get('update') || [];
    genericListeners.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in generic update callback:', error);
      }
    });
  }

  // Send message to server
  private sendMessage(message: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  // Request specific dashboard refresh
  requestDashboardRefresh(dashboardId: string, filters?: any): void {
    this.sendMessage({
      type: 'request_dashboard_refresh',
      data: {
        dashboardId,
        filters,
        timestamp: new Date().toISOString()
      }
    });
  }

  // Send user interaction events
  trackUserInteraction(interaction: {
    type: string;
    widget_id?: string;
    dashboard_id?: string;
    action?: string;
    metadata?: any;
  }): void {
    this.sendMessage({
      type: 'user_interaction',
      data: {
        ...interaction,
        timestamp: new Date().toISOString()
      }
    });
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  // Get connection state
  getConnectionState(): string {
    if (!this.socket) return 'disconnected';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }
}

// Global instance
export const analyticsWebSocket = new AnalyticsWebSocketService();
export default AnalyticsWebSocketService;