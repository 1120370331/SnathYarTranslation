/**
 * TranslationResult Component
 * 
 * Displays translation results with editing capabilities and mystical theming.
 * Allows users to edit AI-generated translations and confirm them.
 */

import React, { useState, useCallback } from 'react';
import { useConfirmTranslation } from '../hooks/useTranslation';
import toast from 'react-hot-toast';

export interface TranslationResultProps {
  result: {
    translated_text: string;
    source_text: string;
    is_cached: boolean;
    is_ai_generated: boolean;
    can_edit: boolean;
    confidence_score?: number;
    translation_id?: string;
  };
  onTranslationConfirmed?: (result: any) => void;
}

export const TranslationResult: React.FC<TranslationResultProps> = ({
  result,
  onTranslationConfirmed
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(result.translated_text);
  const [isSaving, setIsSaving] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const confirmTranslation = useConfirmTranslation();

  // Handle edit mode toggle
  const handleEditClick = useCallback(() => {
    setIsEditing(true);
    setEditedText(result.translated_text);
  }, [result.translated_text]);

  // Handle copy to clipboard
  const handleCopyToClipboard = useCallback(async () => {
    setIsCopying(true);
    
    try {
      await navigator.clipboard.writeText(result.translated_text);
      toast.success('翻译已复制到剪贴板！ / Translation copied to clipboard!', {
        icon: '📋',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      toast.error('复制失败 / Copy failed', {
        icon: '❌',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
    } finally {
      setIsCopying(false);
    }
  }, [result.translated_text]);

  // Handle direct save (without editing)
  const handleDirectSave = useCallback(async () => {
    if (!result.translation_id) return;
    
    setIsSaving(true);
    
    try {
      await confirmTranslation.mutateAsync({
        translationId: result.translation_id,
        editedText: result.translated_text,
        originalChinese: result.source_text
      });
      
      // Auto copy to clipboard after saving
      await navigator.clipboard.writeText(result.translated_text);
      
      toast.success('翻译已保存并复制！ / Translation saved and copied!', {
        icon: '💾✨',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
      
      if (onTranslationConfirmed) {
        onTranslationConfirmed({
          ...result,
          is_cached: true,
          can_edit: false
        });
      }
      
    } catch (error) {
      console.error('Failed to save translation:', error);
      toast.error('保存失败 / Save failed', {
        icon: '❌',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
    } finally {
      setIsSaving(false);
    }
  }, [result, confirmTranslation, onTranslationConfirmed]);

  // Handle cancel editing
  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
    setEditedText(result.translated_text);
  }, [result.translated_text]);

  // Handle save edited translation
  const handleSaveEdit = useCallback(async () => {
    if (!editedText.trim() || !result.translation_id) return;
    
    setIsSaving(true);
    
    try {
      await confirmTranslation.mutateAsync({
        translationId: result.translation_id,
        editedText,
        originalChinese: result.source_text
      });
      
      // Auto copy to clipboard after saving
      await navigator.clipboard.writeText(editedText);
      
      toast.success('翻译已确认并复制！ / Translation confirmed and copied!', {
        icon: '✅📋',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
      
      if (onTranslationConfirmed) {
        onTranslationConfirmed({
          ...result,
          translated_text: editedText,
          is_cached: true,
          can_edit: false
        });
      }
      
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save translation:', error);
      toast.error('确认失败 / Confirmation failed', {
        icon: '❌',
        style: {
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          color: '#f0f0f5',
          border: '1px solid #4a5568',
          borderRadius: '8px',
        }
      });
    } finally {
      setIsSaving(false);
    }
  }, [editedText, result, confirmTranslation, onTranslationConfirmed]);

  // Get source badge text and styling
  const getSourceBadge = () => {
    if (!result.is_ai_generated) {
      return {
        text: '官方词典 / Official Dictionary',
        className: 'bg-green-600 text-green-100'
      };
    }
    
    if (result.is_cached) {
      return {
        text: '缓存结果 / Cached Result',
        className: 'bg-blue-600 text-blue-100'
      };
    }
    
    return {
      text: 'AI 生成 / AI Generated',
      className: 'bg-purple-600 text-purple-100'
    };
  };

  const sourceBadge = getSourceBadge();
  const characterCount = editedText.length;
  const isTextTooLong = characterCount > 1000;

  return (
    <div 
      className="mystical-translation-result bg-mystical-dark rounded-lg border border-mystical-border shadow-mystical p-6"
      data-testid="translation-result"
    >
      {/* Header with source indicator */}
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold font-mystical text-mystical-text">
          翻译结果 / Translation Result
        </h3>
        <span className={`px-3 py-1 rounded-full text-xs font-mystical ${sourceBadge.className}`}>
          {sourceBadge.text}
        </span>
      </div>

      {/* Source text display */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-mystical-muted mb-2">
          原文 / Source Text
        </label>
        <div className="p-3 bg-mystical-darker rounded-md border border-mystical-border">
          <p className="text-mystical-text font-mystical break-words">
            {result.source_text}
          </p>
        </div>
      </div>

      {/* Translation result */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium text-mystical-muted">
            译文 / Translation
          </label>
          {result.confidence_score && (
            <span className="text-xs text-mystical-muted font-mystical">
              置信度: {Math.round(result.confidence_score * 100)}%
            </span>
          )}
        </div>

        {isEditing ? (
          <div>
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className={`mystical-textarea w-full p-4 rounded-md bg-mystical-darker border text-mystical-text placeholder-mystical-muted focus:ring-2 focus:ring-mystical-accent focus:border-mystical-accent min-h-[120px] resize-vertical ${
                isTextTooLong ? 'border-red-500' : 'border-mystical-border'
              }`}
              placeholder="编辑翻译结果..."
              maxLength={1100}
              data-testid="edit-translation-textarea"
            />
            <div className="flex justify-between items-center mt-2">
              <div className={`text-sm font-mystical ${
                isTextTooLong ? 'text-red-400' : 'text-gray-400'
              }`}>
                {characterCount}/1000
              </div>
              {isTextTooLong && (
                <div className="text-red-400 text-sm font-mystical">
                  翻译文本过长
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-4 bg-mystical-darker rounded-md border border-mystical-border">
            <p className="text-mystical-text font-mystical text-lg break-words leading-relaxed">
              {result.translated_text}
            </p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex justify-end space-x-3">
        {isEditing ? (
          <>
            <button
              onClick={handleCancelEdit}
              disabled={isSaving}
              className="mystical-button-secondary px-4 py-2 rounded-md font-medium text-mystical-muted hover:text-mystical-text transition-colors"
              data-testid="cancel-edit-btn"
            >
              取消 / Cancel
            </button>
            <button
              onClick={handleSaveEdit}
              disabled={isSaving || !editedText.trim() || isTextTooLong}
              className={`mystical-button px-6 py-2 rounded-md font-medium transition-all duration-300 ${
                isSaving || !editedText.trim() || isTextTooLong
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-mystical-accent hover:bg-mystical-accent-hover text-mystical-dark hover:shadow-mystical-glow'
              }`}
              data-testid="save-edit-btn"
            >
              {isSaving ? (
                <span className="flex items-center">
                  <div className="animate-spin w-4 h-4 border-2 border-mystical-dark border-t-transparent rounded-full mr-2"></div>
                  确认中...
                </span>
              ) : (
                '确认并复制 / Confirm & Copy'
              )}
            </button>
          </>
        ) : (
          <div className="flex space-x-3">
            {/* Copy to clipboard button - always available */}
            <button
              onClick={handleCopyToClipboard}
              disabled={isCopying}
              className="mystical-button-outline px-4 py-2 rounded-md font-medium border-2 border-mystical-gold text-mystical-gold hover:bg-mystical-gold hover:text-mystical-dark transition-all duration-300 flex items-center"
              data-testid="copy-translation-btn"
            >
              {isCopying ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2"></div>
                  复制中...
                </>
              ) : (
                <>
                  <span className="mr-2">📋</span>
                  复制 / Copy
                </>
              )}
            </button>
            
            {/* Direct save button - for AI generated translations */}
            {result.can_edit && result.is_ai_generated && !result.is_cached && result.translation_id && (
              <button
                onClick={handleDirectSave}
                disabled={isSaving}
                className="mystical-button px-4 py-2 rounded-md font-medium bg-green-600 hover:bg-green-700 text-white transition-all duration-300 flex items-center"
                data-testid="direct-save-btn"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <span className="mr-2">💾</span>
                    确认保存 / Confirm & Save
                  </>
                )}
              </button>
            )}
            
            {/* Edit button - for editable translations */}
            {result.can_edit && (
              <button
                onClick={handleEditClick}
                className="mystical-button-outline px-6 py-2 rounded-md font-medium border-2 border-mystical-accent text-mystical-accent hover:bg-mystical-accent hover:text-mystical-dark transition-all duration-300"
                data-testid="edit-translation-btn"
              >
                编辑翻译 / Edit Translation
              </button>
            )}
          </div>
        )}
      </div>

      {/* Usage note for AI translations */}
      {result.is_ai_generated && !result.is_cached && (
        <div className="mt-4 p-3 bg-mystical-darker rounded-md border border-mystical-border">
          <p className="text-xs text-mystical-muted font-mystical">
            ⚡ AI 翻译结果仅供参考，建议人工校对后确认 / AI translation for reference only, manual review recommended
          </p>
        </div>
      )}
    </div>
  );
};