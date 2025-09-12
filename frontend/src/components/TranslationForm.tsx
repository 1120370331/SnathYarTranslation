/**
 * TranslationForm Component
 * 
 * Main translation form with language selection, input validation, and mystical theme.
 * Implements all functional requirements for user input and translation workflow.
 */

import React, { useState, useCallback } from 'react';
import { useTranslation } from '../hooks/useTranslation';
import { TranslationResult } from './TranslationResult';
import { ErrorDisplay } from './ErrorDisplay';

export interface TranslationFormProps {
  onTranslationComplete?: (result: any) => void;
  initialLanguage?: 'chinese' | 'shathyar';
}

export interface TranslationFormData {
  text: string;
  source_language: 'chinese' | 'shathyar';
}

export const TranslationForm: React.FC<TranslationFormProps> = ({
  onTranslationComplete,
  initialLanguage = 'chinese'
}) => {
  const [formData, setFormData] = useState<TranslationFormData>({
    text: '',
    source_language: initialLanguage
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const {
    mutate: translate,
    mutateAsync: translateAsync,
    data: translationResult,
    isLoading,
    error: translationError,
    reset: resetTranslation
  } = useTranslation();

  // Character count and validation
  const characterCount = formData.text.length;
  const isTextTooLong = characterCount > 500;
  const isTextEmpty = !formData.text.trim();

  // Form validation
  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (isTextEmpty) {
      newErrors.text = '请输入要翻译的文本';
    } else if (isTextTooLong) {
      newErrors.text = '古卷无法记录如此冗长的文字...';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [isTextEmpty, isTextTooLong]);

  // Handle input changes
  const handleTextChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = event.target.value;
    setFormData(prev => ({ ...prev, text: newText }));
    
    // Clear errors when user starts typing
    if (errors.text) {
      setErrors(prev => ({ ...prev, text: '' }));
    }
    
    // Reset previous translation when input changes
    if (translationResult) {
      resetTranslation();
    }
  }, [errors.text, translationResult, resetTranslation]);

  const handleLanguageChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const newLanguage = event.target.value as 'chinese' | 'shathyar';
    setFormData(prev => ({ ...prev, source_language: newLanguage }));
    
    // Reset translation when language changes
    if (translationResult) {
      resetTranslation();
    }
  }, [translationResult, resetTranslation]);

  // Handle form submission
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      const result = await translateAsync(formData);
      // Notify parent immediately so magic power updates without waiting for confirm
      if (onTranslationComplete && result) {
        onTranslationComplete(result);
      }
    } catch (error) {
      console.error('Translation error:', error);
    }
  }, [formData, validateForm, translateAsync, onTranslationComplete]);

  // Get placeholder text based on selected language
  const getPlaceholder = useCallback(() => {
    return formData.source_language === 'chinese' 
      ? '输入中文文本...'
      : '输入沙斯亚尔语文本...';
  }, [formData.source_language]);

  // Character counter styling based on length
  const getCharacterCountClass = useCallback(() => {
    const baseClass = 'text-sm font-mystical';
    if (isTextTooLong) return `${baseClass} text-red-400`;
    if (characterCount > 400) return `${baseClass} text-yellow-400`;
    return `${baseClass} text-gray-400`;
  }, [characterCount, isTextTooLong]);

  return (
    <div className="mystical-container max-w-4xl mx-auto p-6">

      {/* Main Translation Form */}
      <form 
        onSubmit={handleSubmit}
        className="mystical-form bg-mystical-dark rounded-lg shadow-mystical p-6 border border-mystical-border"
        data-testid="translation-form"
        role="form"
      >
        {/* Language Selection */}
        <div className="mb-4">
          <label htmlFor="language-select" className="block text-sm font-medium text-mystical-text mb-2">
            选择源语言 / Select Source Language
          </label>
          <select
            id="language-select"
            data-testid="language-select"
            value={formData.source_language}
            onChange={handleLanguageChange}
            className="mystical-select w-full p-3 rounded-md bg-mystical-darker border border-mystical-border text-mystical-text focus:ring-2 focus:ring-mystical-accent focus:border-mystical-accent"
            disabled={isLoading}
          >
            <option value="chinese">中文 (Chinese)</option>
            <option value="shathyar">沙斯亚尔语 (Shathyar)</option>
          </select>
        </div>

        {/* Text Input Area */}
        <div className="mb-4">
          <label htmlFor="translation-input" className="block text-sm font-medium text-mystical-text mb-2">
            翻译文本 / Text to Translate
          </label>
          <textarea
            id="translation-input"
            data-testid="translation-input"
            value={formData.text}
            onChange={handleTextChange}
            placeholder={getPlaceholder()}
            className={`mystical-textarea w-full p-4 rounded-md bg-mystical-darker border text-mystical-text placeholder-mystical-muted focus:ring-2 focus:ring-mystical-accent focus:border-mystical-accent min-h-[120px] resize-vertical ${
              errors.text ? 'border-red-500' : 'border-mystical-border'
            }`}
            disabled={isLoading}
            maxLength={600} // Soft limit with visual feedback
            rows={4}
          />
          
          {/* Character Counter */}
          <div className="flex justify-between items-center mt-2">
            <div className={getCharacterCountClass()}>
              {characterCount}/500
            </div>
            {errors.text && (
              <div className="text-red-400 text-sm font-mystical">
                {errors.text}
              </div>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={isLoading || isTextEmpty || isTextTooLong}
            className={`mystical-button px-8 py-3 rounded-md font-medium transition-all duration-300 ${
              isLoading || isTextEmpty || isTextTooLong
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-mystical-accent hover:bg-mystical-accent-hover text-mystical-dark hover:shadow-mystical-glow'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center">
                <div className="animate-spin w-4 h-4 border-2 border-mystical-dark border-t-transparent rounded-full mr-2"></div>
                翻译中...
              </span>
            ) : (
              '开始翻译 / Translate'
            )}
          </button>
        </div>
      </form>

      {/* Error Display */}
      {translationError && (
        <div className="mt-6">
          <ErrorDisplay error={translationError} onRetry={() => translate(formData)} />
        </div>
      )}

      {/* Translation Result */}
      {translationResult && !translationError && (
        <div className="mt-6">
          <TranslationResult 
            result={translationResult}
            onTranslationConfirmed={onTranslationComplete}
          />
        </div>
      )}
    </div>
  );
};
