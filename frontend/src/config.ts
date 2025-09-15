export type AppConfig = {
  apiBaseUrl: string
  basePath: string
}

const defaultConfig: AppConfig = {
  apiBaseUrl: '/api/v1',
  basePath: '/',
}

let cached: AppConfig | null = null

export async function loadAppConfig(): Promise<AppConfig> {
  if (cached) return cached
  // Try to load runtime JSON from the same directory as index.html
  try {
    const res = await fetch('app-config.json', { cache: 'no-store' })
    if (res.ok) {
      const json = await res.json()
      cached = {
        apiBaseUrl:
          (json.apiBaseUrl || '').toString().replace(/\/$/, '') ||
          ((import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined) ||
          defaultConfig.apiBaseUrl,
        basePath:
          (json.basePath || '').toString() ||
          ((import.meta as any)?.env?.VITE_BASE_PATH as string | undefined) ||
          defaultConfig.basePath,
      }
    } else {
      cached = {
        apiBaseUrl: ((((import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined) || defaultConfig.apiBaseUrl)).toString().replace(/\/$/, ''),
        basePath: ((((import.meta as any)?.env?.VITE_BASE_PATH as string | undefined) || defaultConfig.basePath)).toString(),
      }
    }
  } catch {
    cached = {
      apiBaseUrl: ((((import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined) || defaultConfig.apiBaseUrl)).toString().replace(/\/$/, ''),
      basePath: ((((import.meta as any)?.env?.VITE_BASE_PATH as string | undefined) || defaultConfig.basePath)).toString(),
    }
  }
  ;(window as any).__APP_CONFIG__ = cached
  return cached
}

export function getAppConfig(): AppConfig {
  return (window as any).__APP_CONFIG__ || cached || defaultConfig
}
