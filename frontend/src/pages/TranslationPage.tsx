/**
 * Translation Page Component
 * 
 * Enhanced main page containing the translation form and results display
 * with beautiful mystical UI and proper PRD compliance
 */

import React, { useEffect, useState } from 'react'
import { TranslationForm } from '../components/TranslationForm'
import { MagicPowerIndicator } from '../components/MagicPowerIndicator'
import toast from 'react-hot-toast'
import { apiClient } from '../services/api-client'

const TranslationPage: React.FC = () => {
  const [magicPower, setMagicPower] = useState({
    remaining: 500,
    total: 500,
    resetTime: undefined as string | undefined
  })

  // Initialize magic power from backend (or local fallback) on mount
  useEffect(() => {
    let mounted = true
    apiClient.getQuota().then(q => {
      if (!mounted) return
      setMagicPower({
        remaining: q.tokens_remaining,
        total: q.daily_limit,
        resetTime: q.reset_time,
      })
    }).catch(() => {/* handled inside apiClient via fallback */})
    return () => { mounted = false }
  }, [])

  const handleTranslationComplete = (result: any) => {
    const prevRemaining = magicPower.remaining
    const nextRemaining = result.magic_power_remaining ?? prevRemaining

    // Update magic power from translation result
    setMagicPower(prev => ({
      ...prev,
      remaining: nextRemaining
    }))

    // If quota unchanged, show "no deduction" mystical toast; else normal success
    if (nextRemaining === prevRemaining) {
      toast(
        '📜 卷轴与古老的知识产生了共鸣，本次不消耗魔力值……',
        {
          icon: '✨',
          style: {
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            color: '#f0f0f5',
            border: '1px solid #4a5568',
            borderRadius: '8px',
          }
        }
      )
    } else {
      toast.success(
        `翻译完成！剩余魔力: ${nextRemaining} / Translation complete! Remaining power: ${nextRemaining}`,
        {
          icon: '✨',
          style: {
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            color: '#f0f0f5',
            border: '1px solid #4a5568',
            borderRadius: '8px',
          }
        }
      )
    }
  }

  return (
    <div className="min-h-screen">
      {/* Mystical Background Elements */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-32 h-32 mystical-float">
          <div className="w-full h-full rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-xl"></div>
        </div>
        <div className="absolute top-1/3 right-20 w-24 h-24 mystical-float" style={{animationDelay: '2s'}}>
          <div className="w-full h-full rounded-full bg-gradient-to-br from-blue-500/10 to-transparent blur-xl"></div>
        </div>
        <div className="absolute bottom-1/4 left-1/3 w-20 h-20 mystical-float" style={{animationDelay: '4s'}}>
          <div className="w-full h-full rounded-full bg-gradient-to-br from-yellow-500/10 to-transparent blur-xl"></div>
        </div>
      </div>

      <div className="relative max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* Welcome Section */}
        <div className="text-center mb-12">
          <div className="inline-block">
            <div className="text-8xl mb-6 mystical-float mystical-icon">🐙</div>
            <h1 className="text-4xl md:text-5xl font-bold font-mystical text-mystical-text mb-3 mystical-text-gold">
              卷轴展开 · 虚空渐启
            </h1>
            <h2 className="text-2xl md:text-3xl font-mystical mystical-text-gold mb-6">
              The Scroll Unfurls, The Void Awaits
            </h2>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <p className="text-xl text-mystical-text font-mystical leading-relaxed mb-4">
              欢迎来到沙斯亚尔语翻译门户。
            </p>
          </div>
        </div>

        {/* Magic Power Status - Enhanced Design */}
        <div className="mb-12">
          <div className="mystical-card rounded-xl p-6">
            <div className="flex items-center justify-center mb-4">
              <div className="text-3xl mystical-icon mr-3">⚡</div>
              <h3 className="text-2xl font-bold font-mystical mystical-text-glow">
                魔力法阵 / Magic Circle
              </h3>
            </div>
            <MagicPowerIndicator
              remaining={magicPower.remaining}
              total={magicPower.total}
              resetTime={magicPower.resetTime}
            />
            <div className="text-center mt-4">
              <p className="text-sm text-mystical-muted font-mystical">
                每日限制 {magicPower.total} 次翻译，已使用 {magicPower.total - magicPower.remaining} 次
              </p>
            </div>
          </div>
        </div>

        {/* Main Translation Interface */}
        <div className="mb-12">
          <TranslationForm 
            onTranslationComplete={handleTranslationComplete}
            initialLanguage="chinese"
          />
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <div className="mystical-card rounded-xl p-6 text-center">
            <div className="text-4xl mystical-icon mb-4">🧠</div>
            <h4 className="text-lg font-bold font-mystical text-mystical-text mb-2">自动翻译</h4>
            <p className="text-sm text-mystical-muted font-mystical">自动生成沙斯亚尔语</p>
          </div>
          
          <div className="mystical-card rounded-xl p-6 text-center">
            <div className="text-4xl mystical-icon mb-4">📚</div>
            <h4 className="text-lg font-bold font-mystical text-mystical-text mb-2">官方词典</h4>
            <p className="text-sm text-mystical-muted font-mystical">权威魔兽世界翻译</p>
          </div>
          
          <div className="mystical-card rounded-xl p-6 text-center">
            <div className="text-4xl mystical-icon mb-4">✏️</div>
            <h4 className="text-lg font-bold font-mystical text-mystical-text mb-2">用户编辑</h4>
            <p className="text-sm text-mystical-muted font-mystical">自由修改确认翻译</p>
          </div>
          
          <div className="mystical-card rounded-xl p-6 text-center">
            <div className="text-4xl mystical-icon mb-4">💾</div>
            <h4 className="text-lg font-bold font-mystical text-mystical-text mb-2">自动保存</h4>
            <p className="text-sm text-mystical-muted font-mystical">自动缓存积累词库</p>
          </div>
        </div>

        {/* Usage Guide - Enhanced */}
        <div className="mystical-card rounded-xl p-8 mb-16">
          <div className="text-center mb-6">
            <div className="text-4xl mystical-icon mb-4">📜</div>
            <h3 className="text-2xl font-bold font-mystical mystical-text-glow mb-4">
              古卷指引 / Ancient Scroll Guide
            </h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="mystical-card rounded-lg p-4">
                <h4 className="text-xl font-bold font-mystical text-mystical-text mb-3 flex items-center">
                  <span className="text-2xl mystical-icon mr-2">🇨🇳</span>
                  中文 → 沙斯亚尔语
                </h4>
                <ul className="space-y-2 text-mystical-muted font-mystical text-sm">
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 快速生成近似沙斯亚尔语</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 参考官方词典语料</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 支持用户编辑和确认</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 自动缓存提高效率</li>
                  <li className="flex items-center"><span className="text-yellow-400 mr-2">⚡</span> 消耗1点魔力值</li>
                </ul>
              </div>
              
              <div className="mystical-card rounded-lg p-4">
                <h4 className="text-xl font-bold font-mystical text-mystical-text mb-3 flex items-center">
                  <span className="text-2xl mystical-icon mr-2">🌌</span>
                  沙斯亚尔语 → 中文
                </h4>
                <ul className="space-y-2 text-mystical-muted font-mystical text-sm">
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 官方词典精确匹配</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 魔兽世界权威翻译</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 即时查询无需等待</li>
                  <li className="flex items-center"><span className="text-green-400 mr-2">✓</span> 100%准确率保证</li>
                  <li className="flex items-center"><span className="text-blue-400 mr-2">💙</span> 不消耗魔力值</li>
                </ul>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="mystical-card rounded-lg p-4">
                <h4 className="text-lg font-bold font-mystical text-mystical-text mb-3">使用技巧 / Usage Tips</h4>
                <ul className="space-y-2 text-mystical-muted font-mystical text-sm">
                  <li>• 输入文本限制500字以内</li>
                  <li>• 重复的中文会自动匹配数据库</li>
                  <li>• 沙斯亚尔语未找到时显示"破译失败"</li>
                  <li>• 每日重置时间为UTC午夜</li>
                </ul>
              </div>
              
              <div className="mystical-card rounded-lg p-4">
                <h4 className="text-lg font-bold font-mystical text-mystical-text mb-3">快捷功能 / Quick Features</h4>
                <ul className="space-y-2 text-mystical-muted font-mystical text-sm">
                  <li>• 🔄 可编辑翻译结果</li>
                  <li>• 💾 一键确认并保存</li>
                  <li>• 📋 自动复制到剪贴板</li>
                  <li>• 🎯 翻译建议</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Mystical Quote with Enhanced Styling */}
        <div className="text-center py-12">
          <div className="mystical-card rounded-xl p-8 max-w-3xl mx-auto">
            <div className="text-5xl mystical-icon mb-6">🔮</div>
            <blockquote className="text-2xl font-mystical mystical-text-gold mb-6 leading-relaxed">
              "Gul'kafh an'qov N'zoth... 
              <br />
              Vash'jir kul'thrak mor'dun yashu'in talar korrath..."
            </blockquote>
            <footer className="text-mystical-muted font-mystical">
              <div className="w-16 h-px bg-gradient-to-r from-transparent via-mystical-accent to-transparent mx-auto mb-4"></div>
              <p className="text-lg">— 虚空古语 / Ancient Void Saying</p>
              <p className="text-sm mt-2 italic">"凝视恩佐斯的内心... 虚空的力量召唤着我们..."</p>
            </footer>
          </div>
        </div>

        {/* Footer Information */}
        <div className="text-center py-8">
          <div className="mystical-card rounded-lg p-6">
            <p className="text-mystical-muted font-mystical text-sm">
              🌟 沙斯亚尔语翻译器 v1.0.1 | 由古老虚空魔法驱动 
              <br />
              <span className="text-xs opacity-70">
                Powered by Ancient Void Magic • Crafted with Care
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TranslationPage
