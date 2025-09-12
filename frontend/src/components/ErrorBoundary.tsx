/**
 * Error Boundary Component
 * 
 * Global error boundary with mystical theming for graceful error handling
 */

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  }

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error, errorInfo: null }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🔥 Mystical error boundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-mystical-dark text-mystical-text font-mystical flex items-center justify-center px-4">
          <div className="max-w-2xl mx-auto text-center">
            {/* Mystical Error Icon */}
            <div className="text-8xl mb-6 animate-pulse">💀</div>
            
            {/* Error Title */}
            <h1 className="text-4xl font-bold mb-4 text-mystical-text">
              虚空裂隙出现 / Void Rift Detected
            </h1>
            
            <h2 className="text-2xl font-bold mb-6 text-mystical-accent">
              Translation Portal Disrupted
            </h2>
            
            {/* Error Description */}
            <div className="bg-mystical-darker rounded-lg border border-red-600 p-6 mb-8">
              <p className="text-mystical-text mb-4 leading-relaxed">
                翻译门户遭遇了神秘力量的干扰，无法正常运行。请尝试重新加载页面或联系我们的法师团队。
              </p>
              <p className="text-mystical-muted italic">
                The translation portal has encountered interference from mystical forces and cannot operate normally. 
                Please try reloading the page or contact our mage team.
              </p>
              
              {/* Error Details (Development Only) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-mystical-accent hover:text-mystical-accent-hover">
                    🔧 Technical Spell Details (Dev)
                  </summary>
                  <div className="mt-2 p-4 bg-mystical-darkest rounded border font-mono text-sm overflow-auto">
                    <div className="text-red-400 mb-2">
                      <strong>Error:</strong> {this.state.error.name}
                    </div>
                    <div className="text-yellow-400 mb-2">
                      <strong>Message:</strong> {this.state.error.message}
                    </div>
                    <div className="text-blue-400">
                      <strong>Stack:</strong>
                      <pre className="mt-1 text-xs overflow-x-auto">
                        {this.state.error.stack}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div className="text-green-400 mt-2">
                        <strong>Component Stack:</strong>
                        <pre className="mt-1 text-xs overflow-x-auto">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
            
            {/* Recovery Actions */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={this.handleReload}
                  className="mystical-button px-8 py-3 rounded-md font-medium bg-mystical-accent hover:bg-mystical-accent-hover text-mystical-dark hover:shadow-mystical-glow transition-all duration-300"
                >
                  🔄 重新加载门户 / Reload Portal
                </button>
                
                <button
                  onClick={this.handleReset}
                  className="mystical-button-outline px-8 py-3 rounded-md font-medium border-2 border-mystical-accent text-mystical-accent hover:bg-mystical-accent hover:text-mystical-dark transition-all duration-300"
                >
                  ⚡ 重置法阵 / Reset Spell Circle
                </button>
              </div>
              
              <div className="text-sm text-mystical-muted">
                <p>如果问题持续存在，请检查浏览器控制台或联系技术支持</p>
                <p className="italic">If the problem persists, please check the browser console or contact technical support</p>
              </div>
            </div>
            
            {/* Mystical Footer */}
            <div className="mt-12 pt-8 border-t border-mystical-border">
              <p className="text-mystical-muted italic">
                "即使在最深的黑暗中，语言的力量依然闪烁..." 
                <br />
                <span className="text-sm">
                  "Even in the deepest darkness, the power of language still flickers..."
                </span>
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary