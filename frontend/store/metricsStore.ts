import { BackendResponse } from '@/types';

// In-memory store for metrics/telemetry data
let metricsHistory: BackendResponse[] = [];
let latestResponse: BackendResponse | null = null;
let subscribers: Array<() => void> = [];
let seenIds: Set<string> = new Set(); // Track unique IDs to prevent duplicates
let isInitialized = false;

const MAX_HISTORY = 500;

const generateId = (response: BackendResponse): string => {
  // Use timestamp + first 50 chars of response as unique ID
  const timestamp = response.timestamp || new Date().toISOString();
  const responseSnippet = response.ai_response?.substring(0, 50) || '';
  return `${timestamp}-${responseSnippet}`;
};

export const metricsStore = {
  // Load historical data from backend
  loadHistory: async (): Promise<void> => {
    try {
      const response = await fetch('/api/telemetry?mode=history&limit=500');
      if (!response.ok) {
        console.error('Failed to load history:', response.status);
        return;
      }
      
      const data = await response.json();
      
      if (data.success && Array.isArray(data.history)) {
        // Clear existing and load from backend
        metricsHistory = [];
        seenIds.clear();
        
        for (const item of data.history) {
          const id = item.id || generateId(item);
          if (!seenIds.has(id)) {
            seenIds.add(id);
            metricsHistory.push(item);
          }
        }
        
        if (metricsHistory.length > 0) {
          latestResponse = metricsHistory[metricsHistory.length - 1];
        }
        
        isInitialized = true;
        notifySubscribers();
        console.log(`✅ Loaded ${metricsHistory.length} historical metrics`);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  },

  // Check if store is initialized
  isInitialized: (): boolean => {
    return isInitialized;
  },

  // Add a new metrics data point (called when a query completes)
  addMetricsPoint: (response: BackendResponse): void => {
    const id = (response as { id?: string }).id || generateId(response);
    
    // Prevent duplicates
    if (seenIds.has(id)) {
      console.log('⚠️ Duplicate metrics point skipped:', id);
      return;
    }
    
    seenIds.add(id);
    latestResponse = response;
    metricsHistory.push(response);
    
    // Keep only the last MAX_HISTORY points
    if (metricsHistory.length > MAX_HISTORY) {
      const removed = metricsHistory.shift();
      if (removed) {
        const removedId = (removed as { id?: string }).id || generateId(removed);
        seenIds.delete(removedId);
      }
    }
    
    notifySubscribers();
  },

  // Get the latest response
  getLatestResponse: (): BackendResponse | null => {
    return latestResponse;
  },

  // Get all metrics history for graphing
  getMetricsHistory: (): BackendResponse[] => {
    return [...metricsHistory];
  },

  // Get history count
  getHistoryCount: (): number => {
    return metricsHistory.length;
  },

  // Clear history
  clearHistory: (): void => {
    metricsHistory = [];
    latestResponse = null;
    seenIds.clear();
    isInitialized = false;
    notifySubscribers();
  },

  // Subscribe to changes
  subscribe: (callback: () => void): (() => void) => {
    subscribers.push(callback);
    return () => {
      subscribers = subscribers.filter((sub) => sub !== callback);
    };
  },
};

const notifySubscribers = (): void => {
  subscribers.forEach((callback) => callback());
};

