import { 
  Notification as INotification, 
  NotificationPriority, 
  NotificationChannel,
  NotificationSettings,
  NotificationFilter,
  NotificationStats
} from '@/types/notification';

interface NotificationStore {
  active: INotification[];
  history: INotification[];
  settings: NotificationSettings;
  filters: NotificationFilter;
}

class NotificationManager {
  private static instance: NotificationManager;
  private store: NotificationStore;
  private listeners: Set<(notifications: INotification[]) => void>;
  private historyListeners: Set<(history: INotification[]) => void>;
  private audioContext: AudioContext | null = null;
  private sounds: Map<NotificationPriority, AudioBuffer> = new Map();

  private constructor() {
    this.store = {
      active: [],
      history: [],
      settings: {
        enabled: true,
        soundEnabled: true,
        pushEnabled: false,
        emailEnabled: false,
        priorities: {
          [NotificationPriority.CRITICAL]: true,
          [NotificationPriority.HIGH]: true,
          [NotificationPriority.MEDIUM]: true,
          [NotificationPriority.LOW]: false
        },
        channels: {
          [NotificationChannel.SYSTEM]: true,
          [NotificationChannel.SECURITY]: true,
          [NotificationChannel.TRADING]: true,
          [NotificationChannel.PARTNER]: true,
          [NotificationChannel.COMPLIANCE]: true
        },
        maxActiveNotifications: 10,
        autoMarkAsRead: false,
        historyRetentionDays: 30
      },
      filters: {
        priorities: Object.values(NotificationPriority),
        channels: Object.values(NotificationChannel),
        dateRange: null,
        readStatus: 'all' as const,
        searchQuery: ''
      }
    };
    this.listeners = new Set();
    this.historyListeners = new Set();
    this.initializeAudio();
    this.loadPersistedData();
  }

  /**
   * Initialize audio context and load notification sounds
   */
  private async initializeAudio() {
    if (typeof window !== 'undefined' && window.AudioContext) {
      try {
        this.audioContext = new AudioContext();
        await this.loadSounds();
      } catch (error) {
        console.warn('Failed to initialize audio context:', error);
      }
    }
  }

  /**
   * Load notification sounds into audio context
   */
  private async loadSounds() {
    if (!this.audioContext) return;

    // 프로그래매틱하게 사운드 생성 (실제 파일 대신)
    const createBeepBuffer = (frequency: number, duration: number) => {
      const sampleRate = this.audioContext!.sampleRate;
      const numSamples = sampleRate * duration;
      const buffer = this.audioContext!.createBuffer(1, numSamples, sampleRate);
      const channelData = buffer.getChannelData(0);
      
      for (let i = 0; i < numSamples; i++) {
        channelData[i] = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 0.3;
      }
      
      return buffer;
    };

    // 우선순위별로 다른 주파수의 비프음 생성
    this.sounds.set(NotificationPriority.CRITICAL, createBeepBuffer(800, 0.5)); // 높은 주파수, 긴 소리
    this.sounds.set(NotificationPriority.HIGH, createBeepBuffer(600, 0.3));     // 중간 주파수
    this.sounds.set(NotificationPriority.MEDIUM, createBeepBuffer(400, 0.2));   // 낮은 주파수
    this.sounds.set(NotificationPriority.LOW, createBeepBuffer(300, 0.1));      // 가장 낮은 주파수, 짧은 소리
  }

  /**
   * Play notification sound based on priority
   */
  private playSound(priority: NotificationPriority) {
    if (!this.store.settings.soundEnabled || !this.audioContext || !this.sounds.has(priority)) {
      return;
    }

    try {
      const audioBuffer = this.sounds.get(priority);
      if (audioBuffer) {
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.start();
      }
    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  }

  /**
   * Load persisted notification data from localStorage
   */
  private loadPersistedData() {
    if (typeof window === 'undefined') return;

    try {
      const savedSettings = localStorage.getItem('notification-settings');
      if (savedSettings) {
        this.store.settings = { ...this.store.settings, ...JSON.parse(savedSettings) };
      }

      const savedHistory = localStorage.getItem('notification-history');
      if (savedHistory) {
        this.store.history = JSON.parse(savedHistory);
        this.cleanupOldHistory();
      }
    } catch (error) {
      console.warn('Failed to load persisted notification data:', error);
    }
  }

  /**
   * Persist notification data to localStorage
   */
  private persistData() {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem('notification-settings', JSON.stringify(this.store.settings));
      localStorage.setItem('notification-history', JSON.stringify(this.store.history));
    } catch (error) {
      console.warn('Failed to persist notification data:', error);
    }
  }

  /**
   * Cleanup old notification history based on retention policy
   */
  private cleanupOldHistory() {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.store.settings.historyRetentionDays);
    
    this.store.history = this.store.history.filter(
      notification => new Date(notification.timestamp) > cutoffDate
    );
  }

  /**
   * Add a new notification
   */
  public addNotification(notification: Omit<INotification, 'id' | 'timestamp' | 'read'>): INotification {
    if (!this.store.settings.enabled) return notification as any as INotification;

    const newNotification: INotification = {
      ...notification,
      id: this.generateId(),
      timestamp: new Date(),
      read: false
    } as INotification;

    // Check if this priority is enabled
    if (!this.store.settings.priorities[notification.priority]) {
      return newNotification;
    }

    // Check if this channel is enabled
    if (!this.store.settings.channels[notification.channel]) {
      return newNotification;
    }

    // Add to active notifications
    this.store.active.unshift(newNotification);

    // Maintain max active notifications limit
    if (this.store.active.length > this.store.settings.maxActiveNotifications) {
      const removed = this.store.active.splice(this.store.settings.maxActiveNotifications);
      this.store.history.unshift(...removed);
    }

    // Add to history
    this.store.history.unshift(newNotification);

    // Play sound notification
    this.playSound(notification.priority);

    // Send push notification if enabled
    if (this.store.settings.pushEnabled) {
      this.sendPushNotification(newNotification);
    }

    // Auto mark as read if enabled
    if (this.store.settings.autoMarkAsRead) {
      setTimeout(() => {
        this.markAsRead(newNotification.id);
      }, 3000);
    }

    this.persistData();
    this.notifyListeners();
    
    return newNotification;
  }

  /**
   * Send push notification using the Web Notifications API
   */
  private async sendPushNotification(notification: INotification) {
    if (!('Notification' in window)) return;

    if (Notification.permission === 'granted') {
      try {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          tag: notification.id,
          requireInteraction: notification.priority === NotificationPriority.CRITICAL
        });
      } catch (error) {
        console.warn('Failed to send push notification:', error);
      }
    } else if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        this.sendPushNotification(notification);
      }
    }
  }

  /**
   * Get active notifications
   */
  public getActiveNotifications(): INotification[] {
    return this.applyFilters(this.store.active);
  }

  /**
   * Get notification history
   */
  public getNotificationHistory(): INotification[] {
    return this.applyFilters(this.store.history);
  }

  /**
   * Apply filters to the notifications
   */
  private applyFilters(notifications: INotification[]): INotification[] {
    let filtered = notifications;

    // Filter by priorities
    if (this.store.filters.priorities.length > 0) {
      filtered = filtered.filter(n => this.store.filters.priorities.includes(n.priority));
    }

    // Filter by channels
    if (this.store.filters.channels.length > 0) {
      filtered = filtered.filter(n => this.store.filters.channels.includes(n.channel));
    }

    // Filter by read status
    if (this.store.filters.readStatus === 'read') {
      filtered = filtered.filter(n => n.read);
    } else if (this.store.filters.readStatus === 'unread') {
      filtered = filtered.filter(n => !n.read);
    }

    // Filter by search query
    if (this.store.filters.searchQuery) {
      const query = this.store.filters.searchQuery.toLowerCase();
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(query) ||
        n.message.toLowerCase().includes(query)
      );
    }

    // Filter by date range
    if (this.store.filters.dateRange) {
      const { start, end } = this.store.filters.dateRange;
      filtered = filtered.filter(n => {
        const date = new Date(n.timestamp);
        return date >= start && date <= end;
      });
    }

    return filtered;
  }

  /**
   * Update notification filters
   */
  public updateFilters(filters: Partial<NotificationFilter>) {
    this.store.filters = { ...this.store.filters, ...filters };
    this.notifyListeners();
  }

  /**
   * Get count of unread notifications
   */
  public getUnreadCount(): number {
    return this.store.active.filter(n => !n.read).length;
  }

  /**
   * Mark a notification as read
   */
  public markAsRead(id: string): void {
    // Mark in active notifications
    const activeIndex = this.store.active.findIndex(n => n.id === id);
    if (activeIndex !== -1) {
      this.store.active[activeIndex].read = true;
    }

    // Mark in history
    const historyIndex = this.store.history.findIndex(n => n.id === id);
    if (historyIndex !== -1) {
      this.store.history[historyIndex].read = true;
    }

    this.persistData();
    this.notifyListeners();
  }

  /**
   * Mark all notifications as read
   */
  public markAllAsRead(): void {
    this.store.active.forEach(n => n.read = true);
    this.store.history.forEach(n => n.read = true);
    this.persistData();
    this.notifyListeners();
  }

  /**
   * Remove a notification
   */
  public removeNotification(id: string): void {
    this.store.active = this.store.active.filter(n => n.id !== id);
    this.persistData();
    this.notifyListeners();
  }

  /**
   * Clear all notifications
   */
  public clearAll(): void {
    // Move active notifications to history
    this.store.history.unshift(...this.store.active);
    this.store.active = [];
    this.persistData();
    this.notifyListeners();
  }

  /**
   * Update notification settings
   */
  public updateSettings(settings: Partial<NotificationSettings>): void {
    this.store.settings = { ...this.store.settings, ...settings };
    this.persistData();
  }

  /**
   * Get current notification settings
   */
  public getSettings(): NotificationSettings {
    return { ...this.store.settings };
  }

  /**
   * Get notification statistics
   */
  public getStats(): NotificationStats {
    const active = this.store.active;
    const stats: NotificationStats = {
      total: active.length,
      unread: active.filter(n => !n.read).length,
      critical: active.filter(n => n.priority === NotificationPriority.CRITICAL).length,
      high: active.filter(n => n.priority === NotificationPriority.HIGH).length,
      medium: active.filter(n => n.priority === NotificationPriority.MEDIUM).length,
      low: active.filter(n => n.priority === NotificationPriority.LOW).length,
      byChannel: {
        [NotificationChannel.SYSTEM]: active.filter(n => n.channel === NotificationChannel.SYSTEM).length,
        [NotificationChannel.SECURITY]: active.filter(n => n.channel === NotificationChannel.SECURITY).length,
        [NotificationChannel.TRADING]: active.filter(n => n.channel === NotificationChannel.TRADING).length,
        [NotificationChannel.PARTNER]: active.filter(n => n.channel === NotificationChannel.PARTNER).length,
        [NotificationChannel.COMPLIANCE]: active.filter(n => n.channel === NotificationChannel.COMPLIANCE).length,
      }
    };
    
    return stats;
  }

  /**
   * Delete a notification
   */
  public deleteNotification(notificationId: string): void {
    this.store.active = this.store.active.filter(n => n.id !== notificationId);
    this.store.history = this.store.history.filter(n => n.id !== notificationId);
    this.notifyListeners();
  }

  /**
   * Request notification permission (browser notifications)
   */
  public async requestPermission(): Promise<NotificationPermission> {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission;
    }

    return 'denied';
  }

  /**
   * Subscribe to notification changes
   */
  public subscribe(callback: (notifications: INotification[]) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Subscribe to notification history changes
   */
  public subscribeToHistory(callback: (history: INotification[]) => void): () => void {
    this.historyListeners.add(callback);
    return () => this.historyListeners.delete(callback);
  }

  /**
   * Notify all listeners about changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(callback => callback(this.getActiveNotifications()));
    this.historyListeners.forEach(callback => callback(this.getNotificationHistory()));
  }

  /**
   * Generate unique ID for notifications
   */
  private generateId(): string {
    return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get singleton instance of NotificationManager
   */
  public static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }
}

export const notificationManager = NotificationManager.getInstance();

// Helper functions for convenience
export function addNotification(notification: Omit<INotification, 'id' | 'timestamp' | 'read'>): INotification {
  return notificationManager.addNotification(notification);
}

export function markAsRead(notificationId: string): void {
  notificationManager.markAsRead(notificationId);
}

export function getNotifications(): INotification[] {
  return notificationManager.getActiveNotifications();
}

export function getNotificationHistory(): INotification[] {
  return notificationManager.getNotificationHistory();
}

export function getSettings(): NotificationSettings {
  return notificationManager.getSettings();
}

export function updateSettings(settings: Partial<NotificationSettings>): void {
  notificationManager.updateSettings(settings);
}
