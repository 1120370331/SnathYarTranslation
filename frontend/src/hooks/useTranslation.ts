/**
 * useTranslation Hook (backend-first)
 *
 * Delegates to backend API to enforce one-IP-per-day quota. The apiClient
 * includes a localStorage fallback so refreshing the page will NOT reset
 * displayed quota even when backend is unreachable.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, type TranslationRequest, type TranslationResponse } from '../services/api-client'

export interface UseTranslationResult {
  mutate: (data: TranslationRequest) => void
  mutateAsync: (data: TranslationRequest) => Promise<TranslationResponse>
  data: TranslationResponse | undefined
  isLoading: boolean
  error: Error | null
  reset: () => void
}

export const useTranslation = (): UseTranslationResult => {
  const queryClient = useQueryClient()

  const mutation = useMutation<TranslationResponse, Error, TranslationRequest>({
    mutationFn: (payload: TranslationRequest) => apiClient.translate(payload),
    onSuccess: () => {
      // Keep magic power indicator and any history in sync
      queryClient.invalidateQueries(['magic-power'])
      queryClient.invalidateQueries(['translation-history'])
    },
    onError: (error) => {
      console.error('Translation failed:', error)
    },
  })

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    data: mutation.data,
    isLoading: mutation.isLoading,
    error: mutation.error as any,
    reset: mutation.reset,
  }
}

// Export confirmation function for direct use
export const useConfirmTranslation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ translationId, editedText, originalChinese }: { translationId: string; editedText: string; originalChinese: string }) =>
      apiClient.confirmTranslation(translationId, editedText, originalChinese),
    onSuccess: () => {
      queryClient.invalidateQueries(['translation-history'])
    },
  })
}

