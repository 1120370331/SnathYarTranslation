/**
 * API Client for backend integration with graceful fallbacks.
 * - Primary: call backend endpoints
 * - Fallback: localStorage simulation to avoid quota reset on refresh
 */

import axios from 'axios'

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

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// Fallback quota store (per-browser, per-day) used only if backend is unreachable
const LS_KEY = 'shathyar_quota_v1'

function getLocalQuota(): QuotaStatus {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      if (data.reset_time && new Date(data.reset_time).getTime() > Date.now()) {
        return data
      }
    }
  } catch {}
  const reset = new Date()
  reset.setUTCHours(0, 0, 0, 0)
  if (reset.getTime() <= Date.now()) {
    reset.setUTCDate(reset.getUTCDate() + 1)
  }
  const initial: QuotaStatus = {
    tokens_remaining: 500,
    daily_limit: 500,
    reset_time: reset.toISOString(),
  }
  try { localStorage.setItem(LS_KEY, JSON.stringify(initial)) } catch {}
  return initial
}

function setLocalQuota(q: QuotaStatus) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(q)) } catch {}
}

function consumeLocalToken(): QuotaStatus {
  const q = getLocalQuota()
  if (q.tokens_remaining <= 0) return q
  const updated = { ...q, tokens_remaining: q.tokens_remaining - 1 }
  setLocalQuota(updated)
  return updated
}

// Minimal Shathyar-style generator as ultimate fallback (kept very lightweight)
function generateShathyar(text: string): string {
  const syl = ['ak','an','al','sh','th','ul','za','ra','qu','gul','ka','iil','bw','ez']
  const end = ["'ah","'gl","'th","'ov"]
  const words = Math.max(1, Math.min(5, Math.ceil(text.length / 2)))
  const result: string[] = []
  for (let i=0;i<words;i++) {
    let w = ''
    const n = Math.random() > 0.7 ? 3 : Math.random() > 0.3 ? 2 : 1
    for (let j=0;j<n;j++) w += syl[Math.floor(Math.random()*syl.length)]
    if (Math.random()>0.5) w += end[Math.floor(Math.random()*end.length)]
    result.push(w.charAt(0).toUpperCase()+w.slice(1))
  }
  return result.join(' ')
}

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
      // Backend unavailable: use local fallback
      return getLocalQuota()
    }
  },

  async translate(req: TranslationRequest): Promise<TranslationResponse> {
    try {
      const { data } = await http.post('/translate', req)
      // Backend returns the authoritative remaining power
      return data
    } catch (err) {
      // If backend responded with an error, propagate it so UI can show proper message
      if (axios.isAxiosError(err) && err.response) {
        const msg = (err.response.data && (err.response.data.error || err.response.data.detail)) || '翻译失败'
        throw new Error(msg)
      }
      // Optionally disable fallback in development via Vite env
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      if (import.meta?.env?.VITE_DISABLE_FALLBACK === 'true') {
        throw new Error('后端不可用 / Backend unreachable')
      }
      // Fallback: simulate with local quota so refresh doesn't reset
      const raw = localStorage.getItem('shathyar_cache_v1')
      const cache: Record<string, string> = raw ? JSON.parse(raw) : {}
      if (req.source_language === 'chinese') {
        // 1) If we already have a cached mapping, return it without consuming
        const existing = cache[req.text]
        if (existing) {
          return {
            translated_text: existing,
            source_text: req.text,
            is_cached: true,
            is_ai_generated: true,
            can_edit: false,
            translation_id: 'local_cache',
            magic_power_remaining: getLocalQuota().tokens_remaining,
            source: 'cache',
          }
        }
        // 2) Otherwise generate once, store mapping, and consume quota
        const q = consumeLocalToken()
        if (q.tokens_remaining < 0) {
          throw new Error('魔力耗尽，请等待重置 / Magic power exhausted, please wait for reset')
        }
        const gen = generateShathyar(req.text)
        cache[req.text] = gen
        try { localStorage.setItem('shathyar_cache_v1', JSON.stringify(cache)) } catch {}
        return {
          translated_text: gen,
          source_text: req.text,
          is_cached: false,
          is_ai_generated: true,
          can_edit: true,
          confidence_score: 0.8,
          translation_id: 'local_' + Date.now(),
          magic_power_remaining: getLocalQuota().tokens_remaining,
          source: 'ai_generated',
        }
      } else {
        // Reverse lookup from local cache: find CN where value equals SH
        const entry = Object.entries(cache).find(([, sh]) => sh === req.text)
        if (entry) {
          const [cn] = entry
          return {
            translated_text: cn,
            source_text: req.text,
            is_cached: true,
            is_ai_generated: true,
            can_edit: false,
            magic_power_remaining: getLocalQuota().tokens_remaining,
            source: 'cache',
          }
        }
        // Do not fake a result; bubble up error for UI to show failure
        throw new Error('破译失败…… / Decryption failed…')
      }
    }
  },

  async confirmTranslation(translationId: string, editedText: string, originalChinese: string): Promise<TranslationResponse> {
    try {
      const { data } = await http.post(`/translate/${encodeURIComponent(translationId)}/confirm`, {
        edited_text: editedText,
      })
      return data
    } catch (err) {
      // Fallback: store mapping in local cache so future lookups hit cache
      try {
        const raw = localStorage.getItem('shathyar_cache_v1')
        const cache = raw ? JSON.parse(raw) : {}
        cache[originalChinese] = editedText
        localStorage.setItem('shathyar_cache_v1', JSON.stringify(cache))
      } catch {}
      return {
        translated_text: editedText,
        source_text: originalChinese,
        is_cached: true,
        is_ai_generated: true,
        can_edit: false,
        magic_power_remaining: getLocalQuota().tokens_remaining,
        translation_id: translationId,
        source: 'cache',
      }
    }
  },
}

export type { QuotaStatus as MagicQuota }
