import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

// Mock localStorage
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

// Mock fetch for shareQr
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

// Mock clipboard
const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
Object.defineProperty(navigator, 'clipboard', { value: mockClipboard, writable: true, configurable: true });

// Mock share API
const mockShare = vi.fn().mockResolvedValue(undefined);
const mockCanShare = vi.fn().mockReturnValue(true);
(globalThis as any).navigator = {
  ...navigator,
  share: mockShare,
  canShare: mockCanShare,
};

// Mock qrcode
vi.mock('qrcode', () => ({
  default: {
    toDataURL: vi.fn().mockResolvedValue('data:image/png;base64,abc123'),
  },
}));

// Mock API module completely
vi.mock('./api', () => ({
  shortenUrl: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  getMyUrls: vi.fn(),
  deleteUrl: vi.fn(),
}));

import App from './App';
import * as api from './api';

const mockApi = api as any;

beforeEach(() => {
  vi.clearAllMocks();
  (localStorage as any).clear();
  mockFetch.mockReset();

  // Reset navigator share
  (globalThis as any).navigator = {
    ...navigator,
    share: mockShare,
    canShare: mockCanShare,
  };
});

describe('App (unauthenticated)', () => {
  it('renders hero section', () => {
    render(<App />);
    expect(screen.getByText(/Shorten links/i)).toBeInTheDocument();
  });

  it('renders features grid', () => {
    render(<App />);
    expect(screen.getByText('Lightning Fast')).toBeInTheDocument();
    expect(screen.getByText('Password Protected')).toBeInTheDocument();
    expect(screen.getByText('Auto Expiry')).toBeInTheDocument();
    expect(screen.getByText('Custom Aliases')).toBeInTheDocument();
    expect(screen.getByText('QR Codes')).toBeInTheDocument();
    expect(screen.getByText('Dark & Light Mode')).toBeInTheDocument();
  });

  it('shows Sign In and Sign Up buttons', () => {
    render(<App />);
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByText('Sign Up Free')).toBeInTheDocument();
  });

  it('renders footer', () => {
    render(<App />);
    expect(screen.getAllByText('SnipLink')).toHaveLength(2);
  });

  it('opens auth modal when Sign In clicked', async () => {
    render(<App />);
    await userEvent.click(screen.getByText('Sign In'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Welcome back')).toBeInTheDocument();
  });

  it('opens auth modal when Sign Up clicked', async () => {
    render(<App />);
    await userEvent.click(screen.getByText('Sign Up Free'));
    expect(screen.getByText('Get started')).toBeInTheDocument();
  });

  it('theme toggle changes theme', async () => {
    render(<App />);
    const themeBtn = screen.getByTitle(/Switch to/);
    await userEvent.click(themeBtn);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });
});

describe('App (authenticated)', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('email', 'user@test.com');
    mockApi.getMyUrls.mockResolvedValue([]);
  });

  it('shows user email in header', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    });
  });

  it('shows Sign out button', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Sign out')).toBeInTheDocument();
    });
  });
});

describe('UrlShortenerBar', () => {
  it('handles successful URL shortening', async () => {
    mockApi.shortenUrl.mockResolvedValueOnce({
      short_url: 'http://localhost:8000/abc123',
      long_url: 'https://example.com',
      alias: 'abc123',
      expires_at: null,
      is_custom: false,
      has_password: false,
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/very-long-url/);
    await userEvent.type(input, 'https://example.com');
    await userEvent.click(screen.getByText('Shorten'));

    await waitFor(() => {
      expect(mockApi.shortenUrl).toHaveBeenCalled();
    });
  });

  it('shows error on failed shortening', async () => {
    mockApi.shortenUrl.mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/very-long-url/);
    await userEvent.type(input, 'https://example.com');
    await userEvent.click(screen.getByText('Shorten'));

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('toggles advanced options', async () => {
    render(<App />);
    const toggle = screen.getByText('Advanced options');
    await userEvent.click(toggle);
    expect(screen.getByLabelText('Custom alias')).toBeInTheDocument();
  });
});

describe('UrlHistory', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('email', 'user@test.com');
  });

  it('shows error state', async () => {
    mockApi.getMyUrls.mockRejectedValueOnce(new Error('Failed to load'));
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load')).toBeInTheDocument();
    });
  });

  it('shows empty state', async () => {
    mockApi.getMyUrls.mockResolvedValueOnce([]);
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/You haven't created any links yet/)).toBeInTheDocument();
    });
  });

  it('lists URLs', async () => {
    mockApi.getMyUrls.mockResolvedValueOnce([{
      alias: 'abc123',
      long_url: 'https://example.com/long',
      short_url: 'http://localhost:8000/abc123',
      is_custom: false,
      has_password: false,
      expires_at: null,
      created_at: null,
    }]);

    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('http://localhost:8000/abc123')).toBeInTheDocument();
    });
  });

  it('delete button removes URL', async () => {
    mockApi.getMyUrls.mockResolvedValueOnce([{
      alias: 'abc123',
      long_url: 'https://example.com/long',
      short_url: 'http://localhost:8000/abc123',
      is_custom: false,
      has_password: false,
      expires_at: null,
      created_at: null,
    }]);
    mockApi.deleteUrl.mockResolvedValueOnce(undefined);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('http://localhost:8000/abc123')).toBeInTheDocument();
    });

    const deleteBtn = document.querySelector('.btn-delete')!;
    await userEvent.click(deleteBtn);

    await waitFor(() => {
      expect(mockApi.deleteUrl).toHaveBeenCalledWith('abc123');
    });
  });
});

describe('AuthModal', () => {
  it('can switch between login and register', async () => {
    render(<App />);
    await userEvent.click(screen.getByText('Sign In'));

    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    await userEvent.click(screen.getByText('Sign up'));
    expect(screen.getByText('Get started')).toBeInTheDocument();
  });

  it('closes on Escape key', async () => {
    render(<App />);
    await userEvent.click(screen.getByText('Sign In'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
    });
  });

  it('handles login submission', async () => {
    mockApi.login.mockResolvedValueOnce({
      access_token: 'token123',
      token_type: 'bearer',
      email: 'user@test.com',
    });

    render(<App />);
    await userEvent.click(screen.getByText('Sign In'));

    await userEvent.type(screen.getByLabelText('Email'), 'user@test.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');

    const panel = document.querySelector('.modal-panel')!;
    const submitBtn = panel.querySelector('button[type="submit"]')!;
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockApi.login).toHaveBeenCalledWith('user@test.com', 'password123');
    });
  });

  it('shows error on login failure', async () => {
    mockApi.login.mockRejectedValueOnce(new Error('Invalid credentials'));

    render(<App />);
    await userEvent.click(screen.getByText('Sign In'));

    await userEvent.type(screen.getByLabelText('Email'), 'user@test.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');

    const panel = document.querySelector('.modal-panel')!;
    const submitBtn = panel.querySelector('button[type="submit"]')!;
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });
});

describe('shareQr utility', () => {
  it('opens native share sheet when available', async () => {
    mockFetch.mockResolvedValueOnce({
      blob: () => Promise.resolve(new Blob(['test'], { type: 'image/png' })),
    });

    mockApi.shortenUrl.mockResolvedValueOnce({
      short_url: 'http://localhost:8000/abc123',
      long_url: 'https://example.com',
      alias: 'abc123',
      expires_at: null,
      is_custom: false,
      has_password: false,
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/very-long-url/);
    await userEvent.type(input, 'https://example.com');
    await userEvent.click(screen.getByText('Shorten'));

    await waitFor(() => {
      expect(screen.getByText('Share QR')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Share QR'));

    await waitFor(() => {
      expect(mockShare).toHaveBeenCalled();
    });
  });

  it('falls back to download when share not available', async () => {
    (globalThis as any).navigator = {
      ...navigator,
      share: undefined,
      canShare: undefined,
      clipboard: mockClipboard,
    };

    mockFetch.mockResolvedValueOnce({
      blob: () => Promise.resolve(new Blob(['test'], { type: 'image/png' })),
    });

    mockApi.shortenUrl.mockResolvedValueOnce({
      short_url: 'http://localhost:8000/abc123',
      long_url: 'https://example.com',
      alias: 'abc123',
      expires_at: null,
      is_custom: false,
      has_password: false,
    });

    render(<App />);

    const input = screen.getByPlaceholderText(/https:\/\/example.com\/very-long-url/);
    await userEvent.type(input, 'https://example.com');
    await userEvent.click(screen.getByText('Shorten'));

    await waitFor(() => {
      expect(screen.getByText('Share QR')).toBeInTheDocument();
    });

    // Should trigger download without error
    await userEvent.click(screen.getByText('Share QR'));
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });
});
