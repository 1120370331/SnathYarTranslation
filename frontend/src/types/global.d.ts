import type { AppConfig } from '../config'

declare global {
  interface Window {
    __APP_CONFIG__?: AppConfig
  }
}

export {}

