import { describe, it, expect } from 'vitest';
import { resolveApiBaseUrl } from '../services/api';

describe('resolveApiBaseUrl configuration tests', () => {
  it('defaults to /api/v1 when VITE_API_URL is empty or undefined', () => {
    expect(resolveApiBaseUrl('')).toBe('/api/v1');
    expect(resolveApiBaseUrl('   ')).toBe('/api/v1');
    expect(resolveApiBaseUrl(undefined)).toBe('/api/v1');
  });

  it('appends /api/v1 exactly once when given root Render hostname', () => {
    const backendUrl = 'https://truthlens-backend.onrender.com';
    expect(resolveApiBaseUrl(backendUrl)).toBe('https://truthlens-backend.onrender.com/api/v1');
  });

  it('handles hostname with trailing slash cleanly without duplicate slashes', () => {
    const backendUrl = 'https://truthlens-backend.onrender.com/';
    expect(resolveApiBaseUrl(backendUrl)).toBe('https://truthlens-backend.onrender.com/api/v1');
  });

  it('does not duplicate /api/v1 if already present in VITE_API_URL', () => {
    const backendUrl = 'https://truthlens-backend.onrender.com/api/v1';
    expect(resolveApiBaseUrl(backendUrl)).toBe('https://truthlens-backend.onrender.com/api/v1');
  });

  it('handles /api/v1 with trailing slash', () => {
    const backendUrl = 'https://truthlens-backend.onrender.com/api/v1/';
    expect(resolveApiBaseUrl(backendUrl)).toBe('https://truthlens-backend.onrender.com/api/v1');
  });

  it('handles URL ending with /api by appending /v1', () => {
    const backendUrl = 'https://truthlens-backend.onrender.com/api';
    expect(resolveApiBaseUrl(backendUrl)).toBe('https://truthlens-backend.onrender.com/api/v1');
  });
});

