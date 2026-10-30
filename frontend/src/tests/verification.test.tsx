import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { VerifyPage } from '../pages/VerifyPage';
import { AuthProvider } from '../hooks/useAuth';

describe('TruthLens News Verification UI', () => {
  it('renders verify page hero, inputs, and language selection', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <VerifyPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/Know What's True/i)).toBeInTheDocument();
    expect(screen.getByText(/Verify With Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Live Evidence Verification/i)).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('allows switching between Paste Article and Article URL modes', () => {
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

    const textTabBtn = screen.getByText('Paste Article / Claim');
    fireEvent.click(textTabBtn);

    expect(screen.getByPlaceholderText(/Paste article body, quoted claims, or statements/i)).toBeInTheDocument();
  });

  it('populates Hindi sample input when sample button is clicked', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <VerifyPage />
        </AuthProvider>
      </BrowserRouter>
    );

    const hindiSampleBtn = screen.getByText(/हिन्दी अंतरिक्ष समाचार/i);
    fireEvent.click(hindiSampleBtn);

    const headlineInput = screen.getByPlaceholderText(/Federal Reserve Holds Benchmark Rates Steady/i) as HTMLInputElement;
    expect(headlineInput.value).toContain('ISRO चंद्रयान-3 मिशन');
  });
});
