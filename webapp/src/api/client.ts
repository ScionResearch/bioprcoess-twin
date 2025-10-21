import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  AuthResponse,
  Batch,
  BatchCreate,
  Calibration,
  CalibrationCreate,
  Inoculation,
  InoculationCreate,
  MediaPreparation,
  MediaPreparationCreate,
  Sample,
  SampleCreate,
  Failure,
  FailureCreate,
  BatchClosure,
  BatchClosureCreate,
  APIError
} from '../types';

// API Base URL - intelligently determine based on runtime
const getApiBaseUrl = (): string => {
  // Always use the same host as the webapp but port 8000
  // This allows the app to work with any hostname (localhost, hostname, IP, etc.)
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8000/api/v1`;
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIError>) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Authentication
  auth: {
    login: async (username: string, password: string): Promise<AuthResponse> => {
      const response = await apiClient.post<AuthResponse>('/auth/login', {
        username,
        password,
      });
      return response.data;
    },
  },

  // Batches
  batches: {
    list: async (): Promise<Batch[]> => {
      const response = await apiClient.get<Batch[]>('/batches');
      return response.data;
    },

    get: async (batchId: string): Promise<Batch> => {
      const response = await apiClient.get<Batch>(`/batches/${batchId}`);
      return response.data;
    },

    create: async (batch: BatchCreate): Promise<Batch> => {
      const response = await apiClient.post<Batch>('/batches', batch);
      return response.data;
    },

    update: async (batchId: string, notes: string): Promise<Batch> => {
      const response = await apiClient.patch<Batch>(`/batches/${batchId}`, { notes });
      return response.data;
    },

    delete: async (batchId: string): Promise<void> => {
      await apiClient.delete(`/batches/${batchId}`);
    },
  },

  // Calibrations
  calibrations: {
    list: async (batchId: string): Promise<Calibration[]> => {
      const response = await apiClient.get<Calibration[]>(`/batches/${batchId}/calibrations`);
      return response.data;
    },

    create: async (batchId: string, calibration: CalibrationCreate): Promise<Calibration> => {
      const response = await apiClient.post<Calibration>(
        `/batches/${batchId}/calibrations`,
        calibration
      );
      return response.data;
    },
  },

  // Media Preparation
  media: {
    get: async (batchId: string): Promise<MediaPreparation | null> => {
      try {
        const response = await apiClient.get<MediaPreparation>(`/batches/${batchId}/media`);
        return response.data;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },

    create: async (batchId: string, media: MediaPreparationCreate): Promise<MediaPreparation> => {
      const response = await apiClient.post<MediaPreparation>(
        `/batches/${batchId}/media`,
        media
      );
      return response.data;
    },
  },

  // Inoculation
  inoculation: {
    get: async (batchId: string): Promise<Inoculation | null> => {
      try {
        const response = await apiClient.get<Inoculation>(`/batches/${batchId}/inoculation`);
        return response.data;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },

    create: async (batchId: string, inoculation: InoculationCreate): Promise<Inoculation> => {
      const response = await apiClient.post<Inoculation>(
        `/batches/${batchId}/inoculation`,
        inoculation
      );
      return response.data;
    },
  },

  // Samples
  samples: {
    list: async (batchId: string): Promise<Sample[]> => {
      const response = await apiClient.get<Sample[]>(`/batches/${batchId}/samples`);
      return response.data;
    },

    create: async (batchId: string, sample: SampleCreate): Promise<Sample> => {
      const response = await apiClient.post<Sample>(
        `/batches/${batchId}/samples`,
        sample
      );
      return response.data;
    },
  },

  // Failures
  failures: {
    list: async (batchId: string): Promise<Failure[]> => {
      const response = await apiClient.get<Failure[]>(`/batches/${batchId}/failures`);
      return response.data;
    },

    create: async (batchId: string, failure: FailureCreate): Promise<Failure> => {
      const response = await apiClient.post<Failure>(
        `/batches/${batchId}/failures`,
        failure
      );
      return response.data;
    },
  },

  // Batch Closure
  closure: {
    close: async (batchId: string, closure: BatchClosureCreate): Promise<BatchClosure> => {
      const response = await apiClient.post<BatchClosure>(
        `/batches/${batchId}/close`,
        closure
      );
      return response.data;
    },
  },
};

export default apiClient;
