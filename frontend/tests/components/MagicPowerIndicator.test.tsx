/**
 * Test for MagicPowerIndicator component
 * 
 * This test MUST FAIL initially (component doesn't exist yet)
 * Tests the magic power quota display component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MagicPowerIndicator } from '../../src/components/MagicPowerIndicator'

describe('MagicPowerIndicator', () => {
  it('displays current magic power and total limit', () => {
    render(<MagicPowerIndicator remaining={423} total={500} />)
    
    // Should show current/total format
    expect(screen.getByText('423/500')).toBeInTheDocument()
    
    // Should show magic power label
    expect(screen.getByText(/魔力值/)).toBeInTheDocument()
  })

  it('shows full magic power state', () => {
    render(<MagicPowerIndicator remaining={500} total={500} />)
    
    expect(screen.getByText('500/500')).toBeInTheDocument()
    
    // Should have full power visual indicator
    const indicator = screen.getByTestId('magic-power-bar') || screen.getByRole('progressbar')
    expect(indicator).toHaveStyle({ width: '100%' })
  })

  it('shows exhausted magic power state', () => {
    const resetTime = '2025-09-12T00:00:00Z'
    render(<MagicPowerIndicator remaining={0} total={500} resetTime={resetTime} />)
    
    expect(screen.getByText('0/500')).toBeInTheDocument()
    
    // Should show exhausted message
    expect(screen.getByText(/魔力耗尽/)).toBeInTheDocument()
    
    // Should show reset time
    expect(screen.getByText(/明日重置/)).toBeInTheDocument()
  })

  it('calculates and displays correct percentage', () => {
    render(<MagicPowerIndicator remaining={250} total={500} />)
    
    const progressBar = screen.getByTestId('magic-power-bar') || screen.getByRole('progressbar')
    expect(progressBar).toHaveStyle({ width: '50%' })
  })

  it('applies different visual states based on remaining power', () => {
    // High power (green/normal state)
    const { rerender } = render(<MagicPowerIndicator remaining={400} total={500} />)
    let indicator = screen.getByTestId('magic-power-indicator')
    expect(indicator).toHaveClass(expect.stringContaining('high'))
    
    // Medium power (yellow/warning state)
    rerender(<MagicPowerIndicator remaining={100} total={500} />)
    indicator = screen.getByTestId('magic-power-indicator')
    expect(indicator).toHaveClass(expect.stringContaining('medium'))
    
    // Low power (red/danger state)
    rerender(<MagicPowerIndicator remaining={10} total={500} />)
    indicator = screen.getByTestId('magic-power-indicator')
    expect(indicator).toHaveClass(expect.stringContaining('low'))
  })

  it('applies mystical theme styling', () => {
    render(<MagicPowerIndicator remaining={300} total={500} />)
    
    const container = screen.getByTestId('magic-power-indicator')
    expect(container).toHaveClass(expect.stringContaining('mystical'))
  })

  it('shows countdown to reset when exhausted', () => {
    const resetTime = '2025-09-12T00:00:00Z'
    render(<MagicPowerIndicator remaining={0} total={500} resetTime={resetTime} />)
    
    // Should show some form of countdown or time until reset
    expect(screen.getByTestId('reset-countdown')).toBeInTheDocument()
  })
})