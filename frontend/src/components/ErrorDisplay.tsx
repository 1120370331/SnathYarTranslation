/**
 * ErrorDisplay Component
 * 
 * Displays error messages with mystical theming and retry functionality.
 * Used throughout the application for consistent error handling UI.
 */

import React from 'react';

export interface ErrorDisplayProps {
  error: Error | { message: string } | string;
  onRetry?: () => void;
  title?: string;
  showRetry?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  title = '失败',
  showRetry = true
}) => {
  // Extract error message from various error types
  const getErrorMessage = (): string => {
    if (typeof error === 'string') {
      return error;
    }
    
    if (error && typeof error === 'object' && 'message' in error) {
      return error.message;
    }
    
    return '未知的神秘力量干扰了翻译过程...';
  };

  const errorMessage = getErrorMessage();

  // Categorize error for appropriate styling and messaging
  const getErrorCategory = (): {
    type: 'network' | 'validation' | 'quota' | 'server' | 'unknown';
    icon: string;
    suggestion: string;
  } => {
    const message = errorMessage.toLowerCase();
    
    if (message.includes('network') || message.includes('连接') || message.includes('timeout')) {
      return {
        type: 'network',
        icon: '🌐',
        suggestion: '请检查网络连接后重试 / Please check your network connection and try again'
      };
    }
    
    if (message.includes('quota') || message.includes('limit') || message.includes('魔力') || message.includes('耗尽')) {
      return {
        type: 'quota',
        icon: '⚡',
        suggestion: '魔力已耗尽，请等待重置 / Magic power exhausted, please wait for reset'
      };
    }
    
    if (message.includes('validation') || message.includes('invalid') || message.includes('冗长') || message.includes('长度')) {
      return {
        type: 'validation',
        icon: '📝',
        suggestion: '请检查输入内容 / Please check your input'
      };
    }
    
    if (message.includes('server') || message.includes('500') || message.includes('服务器')) {
      return {
        type: 'server',
        icon: '🔧',
        suggestion: '服务暂时不可用，请稍后重试 / Service temporarily unavailable, please try again later'
      };
    }
    
    return {
      type: 'unknown',
      icon: '❌',
      suggestion: '请尝试重新操作 / Please try again'
    };
  };

  const errorCategory = getErrorCategory();

  return (
    <div 
      className={`mystical-error-display p-6 rounded-lg border shadow-mystical ${
        errorCategory.type === 'quota' ? 'bg-yellow-900 border-yellow-600' :
        errorCategory.type === 'network' ? 'bg-blue-900 border-blue-600' :
        errorCategory.type === 'validation' ? 'bg-purple-900 border-purple-600' :
        'bg-red-900 border-red-600'
      }`}
      role="alert"
      data-testid="error-display"
    >
      {/* Error Header */}
      <div className="flex items-center mb-3">
        <span className="text-2xl mr-3" role="img" aria-label="error icon">
          {errorCategory.icon}
        </span>
        <h3 className="text-lg font-bold font-mystical text-mystical-text">
          {title}
        </h3>
      </div>

      {/* Error Message */}
      <div className="mb-4">
        <p className="text-mystical-text font-mystical leading-relaxed">
          {errorMessage}
        </p>
      </div>

      {/* Error Suggestion */}
      <div className="mb-4">
        <p className="text-sm text-mystical-muted font-mystical italic">
          {errorCategory.suggestion}
        </p>
      </div>

      {/* Action Buttons */}
      {(showRetry && onRetry) && (
        <div className="flex justify-end">
          <button
            onClick={onRetry}
            className="mystical-button-outline px-6 py-2 rounded-md font-medium border-2 border-mystical-accent text-mystical-accent hover:bg-mystical-accent hover:text-mystical-dark transition-all duration-300"
            data-testid="retry-button"
          >
            重试 / Retry
          </button>
        </div>
      )}

      {/* Technical Details (for development) */}
      {process.env.NODE_ENV === 'development' && (
        <details className="mt-4">
          <summary className="text-xs text-mystical-muted font-mystical cursor-pointer hover:text-mystical-text">
            技术详情 / Technical Details
          </summary>
          <pre className="mt-2 p-3 bg-mystical-darker rounded text-xs text-mystical-muted font-mono overflow-auto">
            {JSON.stringify(error, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};
