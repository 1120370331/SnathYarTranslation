/**
 * Main App Component
 * 
 * Root component for the Shathyar Translation application with routing and layout
 */

import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import TranslationPage from './pages/TranslationPage'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <div className="App mystical-container min-h-screen">
        <Router>
          {/* Header */}
          <header className="bg-mystical-darker border-b border-mystical-border shadow-mystical">
            <div className="container mx-auto px-4 py-6">
              <div className="mystical-card rounded-xl border border-mystical-border p-6 text-center">
                <h1 className="text-4xl font-bold font-mystical text-mystical-text mb-2 mystical-text-gold">
                  📜 沙斯亚尔语翻译器
                </h1>
                <h2 className="text-2xl font-mystical text-mystical-accent mb-2">
                  Shathyar Translator
                </h2>
                <div className="w-24 h-px bg-gradient-to-r from-transparent via-mystical-accent to-transparent mx-auto mb-3"></div>
                <p className="text-mystical-muted font-mystical italic">
                  克苏鲁风·棕黑卷轴配色 · 魔法引导 / Cthulhu-inspired scroll aesthetic with guided UX
                </p>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<TranslationPage />} />
              <Route path="/translate" element={<TranslationPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="bg-mystical-darker border-t border-mystical-border mt-16">
            <div className="container mx-auto px-4 py-6">
              <div className="text-center text-mystical-muted font-mystical">
                <p className="mb-2">
                  ⚡ 每日翻译配额: 500次 / Daily Translation Quota: 500 requests
                </p>
                <p className="text-sm">
                  "在古老卷轴与虚空低语间，觅得言语真意..." /
                  "Between ancient scrolls and void whispers, find the essence of language..."
                </p>
                <p className="text-xs mt-4 opacity-70">
                  © 2025 Shathyar Translation Portal | Guided by Ancient Runes & Void Magic
                </p>
              </div>
            </div>
          </footer>
        </Router>

        {/* Toast Notifications with Mystical Theme */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#151520',
              color: '#e6e6f0',
              border: '1px solid #374151',
              fontFamily: 'system-ui',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#151520',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#151520',
              },
            },
          }}
        />
      </div>
    </ErrorBoundary>
  )
}

// 404 Not Found Page
const NotFoundPage: React.FC = () => {
  return (
    <div className="text-center py-16">
      <div className="mb-8">
        <div className="text-6xl mb-4">🌌</div>
        <h1 className="text-3xl font-bold font-mystical text-mystical-text mb-4">
          404 - 迷失在虚空中
        </h1>
        <h2 className="text-xl font-mystical text-mystical-accent mb-4">
          Lost in the Void
        </h2>
        <p className="text-mystical-muted font-mystical max-w-md mx-auto">
          古卷中未记录此路径... 请返回翻译门户继续您的语言探索之旅。
          <br />
          <em>This path is not recorded in the ancient scrolls... Please return to the translation portal to continue your linguistic journey.</em>
        </p>
      </div>
      <a
        href="/"
        className="mystical-button px-8 py-3 rounded-md font-medium bg-mystical-accent hover:bg-mystical-accent-hover text-mystical-dark hover:shadow-mystical-glow transition-all duration-300 inline-block"
      >
        返回翻译门户 / Return to Portal
      </a>
    </div>
  )
}

export default App
