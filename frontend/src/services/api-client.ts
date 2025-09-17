/**
 * API Client for backend integration (no mock or local fallbacks in production).
 * - Strictly calls backend endpoints; if unreachable, throws errors for UI to handle.
 */

import axios from 'axios'
import { getAppConfig } from '../config'

export interface TranslationRequest {
  text: string
  source_language: 'chinese' | 'shathyar'
}

export interface TranslationResponse {
  translated_text: string
  source_text: string
  is_cached: boolean
  is_ai_generated: boolean
  can_edit: boolean
  confidence_score?: number
  translation_id?: string
  magic_power_remaining?: number
  source?: 'cache' | 'dictionary' | 'ai_generated'
}

export interface QuotaStatus {
  tokens_remaining: number
  daily_limit: number
  reset_time: string
  time_to_reset_seconds?: number
  is_blocked?: boolean
}

// Axios instance with dynamic baseURL from runtime config
const http = axios.create({ timeout: 15000 })

http.interceptors.request.use((config) => {
  const base = getAppConfig().apiBaseUrl || '/api/v1'
  config.baseURL = String(base).replace(/\/$/, '')
  return config
})

export const apiClient = {
  async getQuota(): Promise<QuotaStatus> {
    try {
      const { data } = await http.get('/session/quota')
      // Normalize field names from backend
      const q: QuotaStatus = {
        tokens_remaining: data.tokens_remaining ?? data.magic_power_remaining ?? 0,
        daily_limit: data.daily_limit ?? 500,
        reset_time: data.reset_time ?? new Date().toISOString(),
        time_to_reset_seconds: data.time_to_reset_seconds,
        is_blocked: data.is_blocked,
      }
      return q
    } catch (err) {
      // No local fallback; surface error to UI
      if (axios.isAxiosError(err)) {
        const msg = (err.response?.data && (err.response.data.error || err.response.data.detail)) || '无法获取配额 / Failed to fetch quota'
        throw new Error(msg)
      }
      throw new Error('无法获取配额，后端不可用 / Failed to fetch quota, backend unreachable')
    }
  },

  async translate(req: TranslationRequest): Promise<TranslationResponse> {
    try {
      const { data } = await http.post('/translate', req)
      return data
    } catch (err) {
      // Propagate backend error or network issue
      if (axios.isAxiosError(err)) {
        const msg = (err.response?.data && (err.response.data.error || err.response.data.detail)) || '翻译失败'
        throw new Error(msg)
      }
      throw new Error('后端不可用 / Backend unreachable')
    }
  },

  async confirmTranslation(translationId: string, editedText: string, _originalChinese: string): Promise<TranslationResponse> {
    try {
      const { data } = await http.post(`/translate/${encodeURIComponent(translationId)}/confirm`, {
        edited_text: editedText,
      })
      return data
    } catch (err) {
      // Do NOT pretend success: confirmation must persist on backend
      if (axios.isAxiosError(err)) {
        const msg = (err.response?.data && (err.response.data.error || err.response.data.detail)) || '确认失败，未保存到服务器'
        throw new Error(msg)
      }
      throw new Error('确认失败，后端不可用 / Confirmation failed, backend unreachable')
    }
  },
}

export type { QuotaStatus as MagicQuota }
