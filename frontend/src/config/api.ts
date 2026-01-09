/**
 * API configuration for the frontend.
 * Values can be overridden via environment variables.
 */

export const API_BASE = import.meta.env.VITE_API_BASE || '/api';
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
