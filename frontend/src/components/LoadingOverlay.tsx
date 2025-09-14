import React from 'react'

interface LoadingOverlayProps {
  message?: string
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = '正在翻译... / Translating...' }) => {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <div className="relative flex flex-col items-center text-center text-mystical-text">
        <div className="mb-4 text-sm tracking-widest text-blue-200/90 font-mystical">
          {message}
        </div>
        <div className="relative">
          <div className="mystical-casting-aura" />
          <div className="mystical-casting-ring" />
          <div className="mystical-casting-core" />
        </div>
      </div>
    </div>
  )
}

export default LoadingOverlay

