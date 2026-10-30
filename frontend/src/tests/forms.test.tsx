import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { AuthProvider } from '../hooks/useAuth';

describe('Authentication Forms', () => {
  it('renders login form with email and password inputs', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByPlaceholderText('name@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('updates form inputs on change in login page', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    const emailInput = screen.getByPlaceholderText('name@example.com') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: 'analyst@truthlens.ai' } });
    expect(emailInput.value).toBe('analyst@truthlens.ai');
  });

  it('renders registration form with full name, email and password', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByPlaceholderText('Dr. Jane Doe')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('name@organization.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Minimum 6 characters')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
  });
});

