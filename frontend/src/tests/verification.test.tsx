import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { VerifyPage } from '../pages/VerifyPage';
import { AuthProvider } from '../hooks/useAuth';

describe('TruthLens 2.0 Verification UI', () => {
  it('renders verify page headline, inputs, and language selection', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <VerifyPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/Multilingual News/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Live Evidence Verification/i)).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('allows switching between Text and Article URL modes', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <VerifyPage />
        </AuthProvider>
      </BrowserRouter>
    );

    const urlTabBtn = screen.getByText('Article URL');
    fireEvent.click(urlTabBtn);

    expect(screen.getByPlaceholderText(/https:\/\/www\.reuters\.com/i)).toBeInTheDocument();

    const textTabBtn = screen.getByText('Text / Social Claim');
    fireEvent.click(textTabBtn);

    expect(screen.getByPlaceholderText(/Paste article body, quoted claims/i)).toBeInTheDocument();
  });
});

