import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Navbar } from '../layouts/Navbar';
import { AuthProvider } from '../hooks/useAuth';

describe('Navigation and Layout', () => {
  it('renders brand name TruthLens and public links', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Navbar />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText('TruthLens')).toBeInTheDocument();
    expect(screen.getByText('Verify')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
    expect(screen.getByText('Sign in')).toBeInTheDocument();
    expect(screen.getByText('Get Started')).toBeInTheDocument();

    // Verify old legacy Analyze and 2.0 badges are removed from primary nav
    expect(screen.queryByText('Analyze')).not.toBeInTheDocument();
    expect(screen.queryByText('2.0')).not.toBeInTheDocument();
  });
});
