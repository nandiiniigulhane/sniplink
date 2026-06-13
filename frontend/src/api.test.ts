import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

import { shortenUrl, register, login, getMyUrls, deleteUrl } from './api';

beforeEach(() => {
  vi.resetAllMocks();
  (localStorage as any).clear();
});

describe('request helper', () => {
  it('adds Authorization header when token present', async () => {
    localStorage.setItem('token', 'my-token');
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: 'x', email: 'a@b.com' }),
    });

    await login('a@b.com', 'password123');

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.Authorization).toBe('Bearer my-token');
  });

  it('does not add Authorization header when no token', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: 'x', email: 'a@b.com' }),
    });

    await login('a@b.com', 'password123');

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders.Authorization).toBeUndefined();
  });

  it('throws on non-2xx response with detail', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'Custom error' }),
    });

    await expect(login('a@b.com', 'bad')).rejects.toThrow('Custom error');
  });

  it('throws fallback on non-2xx response without detail', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({}),
    });

    await expect(login('a@b.com', 'bad')).rejects.toThrow('Something went wrong');
  });
});

describe('shortenUrl', () => {
  it('calls POST /api/shorten with correct body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        short_url: 'http://localhost:8000/abc',
        long_url: 'https://example.com',
        alias: 'abc',
        expires_at: null,
        is_custom: false,
        has_password: false,
      }),
    });

    const result = await shortenUrl('https://example.com');
    expect(result.alias).toBe('abc');
    expect(mockFetch).toHaveBeenCalledWith('/api/shorten', expect.objectContaining({
      method: 'POST',
    }));
  });

  it('omits undefined optional fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        short_url: 'http://localhost:8000/abc',
        long_url: 'https://example.com',
        alias: 'abc',
        expires_at: null,
        is_custom: false,
        has_password: false,
      }),
    });

    await shortenUrl('https://example.com');
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.long_url).toBe('https://example.com');
    expect(body.custom_alias).toBeUndefined();
    expect(body.expires_in_days).toBeUndefined();
  });

  it('includes optional fields when provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        short_url: 'http://localhost:8000/my-link',
        long_url: 'https://example.com',
        alias: 'my-link',
        expires_at: null,
        is_custom: true,
        has_password: true,
      }),
    });

    await shortenUrl('https://example.com', 'my-link', 7, 'secret');
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.custom_alias).toBe('my-link');
    expect(body.expires_in_days).toBe(7);
    expect(body.password).toBe('secret');
  });
});

describe('register', () => {
  it('calls POST /api/auth/register', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        access_token: 'token123',
        token_type: 'bearer',
        email: 'test@example.com',
      }),
    });

    const result = await register('test@example.com', 'password123');
    expect(result.access_token).toBe('token123');
    expect(result.email).toBe('test@example.com');
  });
});

describe('login', () => {
  it('calls POST /api/auth/login', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        access_token: 'token123',
        token_type: 'bearer',
        email: 'test@example.com',
      }),
    });

    const result = await login('test@example.com', 'password123');
    expect(result.access_token).toBe('token123');
  });
});

describe('getMyUrls', () => {
  it('calls GET /api/urls and extracts urls array', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        urls: [{
          alias: 'abc',
          long_url: 'https://example.com',
          short_url: 'http://localhost:8000/abc',
          is_custom: false,
          has_password: false,
          expires_at: null,
          created_at: null,
        }],
      }),
    });

    const result = await getMyUrls();
    expect(result).toHaveLength(1);
    expect(result[0].alias).toBe('abc');
  });
});

describe('deleteUrl', () => {
  it('calls DELETE /api/urls/{alias}', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ detail: 'deleted' }),
    });

    await deleteUrl('abc');
    expect(mockFetch).toHaveBeenCalledWith('/api/urls/abc', expect.objectContaining({
      method: 'DELETE',
    }));
  });
});
