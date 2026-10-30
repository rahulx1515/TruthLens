import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AnalyzePage } from '../pages/AnalyzePage';

describe('News Analyze Page Component', () => {
  it('renders headline, content text area, and model selector', () => {
    render(
      <BrowserRouter>
        <AnalyzePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Evaluate Article Credibility')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/as u.s. budget fight/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run credibility analysis/i })).toBeInTheDocument();
  });

  it('switches between Text and URL extraction tabs', () => {
    render(
      <BrowserRouter>
        <AnalyzePage />
      </BrowserRouter>
    );

    const urlTabBtn = screen.getByRole('button', { name: /url extractor/i });
    fireEvent.click(urlTabBtn);

    expect(screen.getByPlaceholderText(/https:\/\/www.reuters.com/i)).toBeInTheDocument();
  });

  it('loads sample authentic preset when sample button is clicked', () => {
    render(
      <BrowserRouter>
        <AnalyzePage />
      </BrowserRouter>
    );

    const presetBtn = screen.getByRole('button', { name: /sample authentic news/i });
    fireEvent.click(presetBtn);

    const headlineInput = screen.getByPlaceholderText(/as u.s. budget fight/i) as HTMLInputElement;
    expect(headlineInput.value).toContain('Reuters');
  });
});

