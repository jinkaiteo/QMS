// Notification Service - Phase C Frontend Development Continuation
import { apiClient } from './apiClient';

export interface NotificationTemplate {
  template_id: string;
  name: string;
  description: string;
  subject_template: string;
  body_template: string;
  template_type: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
}

export interface NotificationRequest {
  template_id: string;
  recipients: string[];
  variables?: Record<string, any>;
  priority?: 'critical' | 'high' | 'normal' | 'low' | 'batch';
  delivery_time?: string;
  metadata?: Record<string, any>;
}

export interface NotificationStatus {
  notification_id: string;
  status: string;
  sent_at?: string;
  delivered_at?: string;
  opened_at?: string;
  clicked_at?: string;
  failed_at?: string;
  error_message?: string;
  delivery_attempts: number;
}

export interface BulkNotificationRequest {
  template_id: string;
  recipient_groups: string[];
  variables?: Record<string, any>;
  send_immediately?: boolean;
  scheduled_time?: string;
  batch_size?: number;
}

export interface NotificationPreferences {
  user_id: number;
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  frequency: string;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  categories: Record<string, boolean>;
}

export interface DeliveryMetrics {
  total_sent: number;
  total_delivered: number;
  total_opened: number;
  total_clicked: number;
  total_failed: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
}

export interface ScheduledNotification {
  schedule_id: string;
  template_id: string;
  recipients: string[];
  scheduled_time: string;
  status: string;
  created_at: string;
}

class NotificationService {
  private baseURL = '/api/v1/notifications';

  async sendNotification(request: NotificationRequest): Promise<{
    success: boolean;
    notification_id: string;
    message: string;
    estimated_delivery: string;
  }> {
    const response = await apiClient.post(`${this.baseURL}/send`, request);
    return response.data;
  }

  async sendBulkNotification(request: BulkNotificationRequest): Promise<{
    success: boolean;
    bulk_id: string;
    message: string;
    estimated_completion: string;
  }> {
    const response = await apiClient.post(`${this.baseURL}/send-bulk`, request);
    return response.data;
  }

  async getNotificationTemplates(
    templateType?: string,
    activeOnly: boolean = true
  ): Promise<NotificationTemplate[]> {
    const response = await apiClient.get(`${this.baseURL}/templates`, {
      params: {
        template_type: templateType,
        active_only: activeOnly
      }
    });
    return response.data;
  }

  async createNotificationTemplate(template: Omit<NotificationTemplate, 'template_id' | 'created_at'>): Promise<{
    success: boolean;
    template_id: string;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseURL}/templates`, template);
    return response.data;
  }

  async getNotificationStatus(notificationId: string): Promise<NotificationStatus> {
    const response = await apiClient.get(`${this.baseURL}/status/${notificationId}`);
    return response.data;
  }

  async getNotificationPreferences(userId: number): Promise<NotificationPreferences> {
    const response = await apiClient.get(`${this.baseURL}/preferences/${userId}`);
    return response.data;
  }

  async updateNotificationPreferences(
    userId: number,
    preferences: Partial<NotificationPreferences>
  ): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.put(`${this.baseURL}/preferences/${userId}`, preferences);
    return response.data;
  }

  async getNotificationMetrics(
    startDate: string,
    endDate: string,
    templateId?: string
  ): Promise<DeliveryMetrics> {
    const response = await apiClient.get(`${this.baseURL}/metrics`, {
      params: {
        start_date: startDate,
        end_date: endDate,
        template_id: templateId
      }
    });
    return response.data;
  }

  async scheduleNotification(
    templateId: string,
    recipients: string[],
    scheduledTime: string,
    variables?: Record<string, any>
  ): Promise<{
    success: boolean;
    schedule_id: string;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseURL}/schedule`, null, {
      params: {
        template_id: templateId,
        recipients,
        scheduled_time: scheduledTime,
        variables
      }
    });
    return response.data;
  }

  async getScheduledNotifications(
    startDate?: string,
    endDate?: string,
    status?: string
  ): Promise<{
    scheduled_notifications: ScheduledNotification[];
    total_count: number;
    filters: Record<string, any>;
  }> {
    const response = await apiClient.get(`${this.baseURL}/scheduled`, {
      params: {
        start_date: startDate,
        end_date: endDate,
        status
      }
    });
    return response.data;
  }

  async cancelScheduledNotification(scheduleId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.delete(`${this.baseURL}/scheduled/${scheduleId}`);
    return response.data;
  }

  async sendTestEmail(
    templateId: string,
    recipient: string,
    variables?: Record<string, any>
  ): Promise<{
    success: boolean;
    test_id: string;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseURL}/test-email`, null, {
      params: {
        template_id: templateId,
        recipient,
        variables
      }
    });
    return response.data;
  }

  async getHealthCheck(): Promise<Record<string, any>> {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export const notificationService = new NotificationService();