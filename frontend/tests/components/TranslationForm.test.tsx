/**
 * Test for TranslationForm component
 * 
 * This test MUST FAIL initially (component doesn't exist yet)
 * Tests the main translation form UI component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { TranslationForm } from '../../src/components/TranslationForm'

// Mock API client
const mockTranslate = vi.fn()
vi.mock('../../src/services/api-client', () => ({
  apiClient: {
    translate: mockTranslate
  }
}))

describe('TranslationForm', () => {
  beforeEach(() => {
    mockTranslate.mockReset()
  })

  it('renders translation form with language selection', () => {
    render(<TranslationForm />)
    
    // Should have language selection dropdown
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    
    // Should have text input area
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    
    // Should have translate button
    expect(screen.getByRole('button', { name: /translate|翻译/i })).toBeInTheDocument()
  })

  it('shows correct placeholder for Chinese input', async () => {
    const user = userEvent.setup()
    render(<TranslationForm />)
    
    const languageSelect = screen.getByRole('combobox')
    const textInput = screen.getByRole('textbox')
    
    // Select Chinese language
    await user.selectOptions(languageSelect, 'chinese')
    
    // Should show Chinese placeholder
    expect(textInput).toHaveAttribute('placeholder', expect.stringContaining('输入中文文本'))
  })

  it('shows correct placeholder for Shathyar input', async () => {
    const user = userEvent.setup()
    render(<TranslationForm />)
    
    const languageSelect = screen.getByRole('combobox')
    const textInput = screen.getByRole('textbox')
    
    // Select Shathyar language  
    await user.selectOptions(languageSelect, 'shathyar')
    
    // Should show Shathyar placeholder
    expect(textInput).toHaveAttribute('placeholder', expect.stringContaining('输入沙斯亚尔语文本'))
  })

  it('displays character counter', async () => {
    const user = userEvent.setup()
    render(<TranslationForm />)
    
    const textInput = screen.getByRole('textbox')
    
    // Type some text
    await user.type(textInput, '虚空的力量召唤着我们')
    
    // Should show character count (12 characters)
    expect(screen.getByText('12/500')).toBeInTheDocument()
  })

  it('validates input length and shows error for text > 500 characters', async () => {
    const user = userEvent.setup()
    render(<TranslationForm />)
    
    const textInput = screen.getByRole('textbox')
    
    // Type text longer than 500 characters
    const longText = '测试'.repeat(251) // 502 characters
    await user.type(textInput, longText)
    
    // Should show error message
    expect(screen.getByText(/古卷无法记录如此冗长的文字/)).toBeInTheDocument()
    
    // Translate button should be disabled
    const translateButton = screen.getByRole('button', { name: /translate|翻译/i })
    expect(translateButton).toBeDisabled()
  })

  it('calls translation API when form is submitted', async () => {
    const user = userEvent.setup()
    
    mockTranslate.mockResolvedValue({
      translated_text: "Vash'jir kul'thrak mor'dun",
      source_text: "虚空的力量召唤着我们",
      is_cached: false,
      is_ai_generated: true,
      magic_power_remaining: 499
    })
    
    render(<TranslationForm />)
    
    const languageSelect = screen.getByRole('combobox')
    const textInput = screen.getByRole('textbox')
    const translateButton = screen.getByRole('button', { name: /translate|翻译/i })
    
    // Fill form
    await user.selectOptions(languageSelect, 'chinese')
    await user.type(textInput, '虚空的力量召唤着我们')
    
    // Submit form
    await user.click(translateButton)
    
    // Should call API with correct parameters
    await waitFor(() => {
      expect(mockTranslate).toHaveBeenCalledWith({
        text: '虚空的力量召唤着我们',
        source_language: 'chinese'
      })
    })
  })

  it('shows loading state during translation', async () => {
    const user = userEvent.setup()
    
    // Mock API to return a pending promise
    let resolveTranslation: (value: any) => void
    const translationPromise = new Promise(resolve => {
      resolveTranslation = resolve
    })
    mockTranslate.mockReturnValue(translationPromise)
    
    render(<TranslationForm />)
    
    const languageSelect = screen.getByRole('combobox')
    const textInput = screen.getByRole('textbox')
    const translateButton = screen.getByRole('button', { name: /translate|翻译/i })
    
    // Fill and submit form
    await user.selectOptions(languageSelect, 'chinese')
    await user.type(textInput, '测试文本')
    await user.click(translateButton)
    
    // Should show loading state
    expect(translateButton).toBeDisabled()
    expect(screen.getByText(/翻译中|loading/i)).toBeInTheDocument()
    
    // Resolve the promise
    resolveTranslation!({
      translated_text: "Test'kul mor'dun",
      source_text: "测试文本",
      is_cached: false,
      magic_power_remaining: 498
    })
    
    // Loading should disappear
    await waitFor(() => {
      expect(screen.queryByText(/翻译中|loading/i)).not.toBeInTheDocument()
    })
  })

  it('applies mystical theme styling', () => {
    render(<TranslationForm />)
    
    const form = screen.getByRole('form') || screen.getByTestId('translation-form')
    
    // Should have mystical theme classes
    expect(form).toHaveClass(expect.stringContaining('mystical'))
  })
})