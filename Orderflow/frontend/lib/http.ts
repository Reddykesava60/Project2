import axios from 'axios';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

console.log('API Base URL:', apiBaseUrl);

export const http = axios.create({
    baseURL: apiBaseUrl,
    withCredentials: true, // Required for HttpOnly cookies
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const AUTH_TOKEN_KEY = 'auth_token';

// Request Interceptor to attach JWT token
http.interceptors.request.use(
    (config) => {
        // Handle base URL adjustment if needed (though axios does it)
        // Check for token in localStorage
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem(AUTH_TOKEN_KEY);
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response Interceptor for Global Error Handling
http.interceptors.response.use(
    (response) => response,
    (error) => {
        // Standardized Backend Conflict Errors
        if (error.response?.status === 409) {
            console.error('Resource Conflict:', error.response.data);
        }

        if (error.response?.status === 401) {
            // Force Login if session expired
            if (typeof window !== 'undefined') {
                // Clear all auth data to prevent infinite loops
                localStorage.removeItem(AUTH_TOKEN_KEY);
                localStorage.removeItem('auth_user'); // Matches key in auth-context.tsx

                // Only redirect if we aren't already on the login page
                if (!window.location.pathname.startsWith('/login')) {
                    // Use window.location.href to force full state reset
                    window.location.href = '/login?expired=true';
                }
            }
        }

        return Promise.reject(error);
    }
);
