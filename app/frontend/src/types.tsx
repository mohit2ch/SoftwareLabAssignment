export interface ApiProxyItem {
  ip: string;
  port: number;
  protocol: string;
  country?: string | null;
  anonymity?: string | null;
  source?: string | null;
  last_checked?: string | null;
  response_time?: number | null; // Raw number from API
  is_valid: boolean;
}

export interface ProxyDisplayInfo {
  id: string;
  proxyString: string;
  status: 'Valid' | 'Invalid' | 'Unknown';
  anonymity: string;
  country: string;
  responseTimeString: string; // Formatted string for display
  rawResponseTime?: number | null; // Raw number for sorting
  lastChecked: string;
  source: string;
}

export interface SchedulerStatus {
  status: 'stopped' | 'running' | 'paused' | 'validating';
  validation_in_progress: boolean;
  interval_seconds: number;
  validation_threads: number;
  test_url: string;
  last_run_time?: string | null;
  next_run_time?: string | null;
  current_proxy_count: number;
  valid_proxy_count: number;
}