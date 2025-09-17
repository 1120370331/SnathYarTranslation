/**
 * MagicPowerIndicator Component
 * 
 * Displays magic power quota with mystical theming and visual feedback.
 * Shows remaining translations, total limit, and reset countdown when exhausted.
 */

import React, { useState, useEffect } from 'react';

export interface MagicPowerIndicatorProps {
  remaining: number;
  total: number;
  resetTime?: string;
}

export const MagicPowerIndicator: React.FC<MagicPowerIndicatorProps> = ({
  remaining,
  total,
  resetTime
}) => {
  const [timeToReset, setTimeToReset] = useState<string>('');

  // Calculate percentage for progress bar
  const safeTotal = total > 0 ? total : 0;
  const percentage = safeTotal > 0 ? Math.round((remaining / safeTotal) * 100) : 100;

  // Determine power level state for styling
  const getPowerLevelClass = (): string => {
    const safeTotal = total > 0 ? total : 0;
    const ratio = safeTotal > 0 ? remaining / safeTotal : 1;
    if (ratio >= 0.8) return 'high';
    if (ratio >= 0.3) return 'medium';
    return 'low';
  };

  // Format countdown to reset time
  useEffect(() => {
    if (!resetTime || remaining > 0) {
      setTimeToReset('');
      return;
    }

    const updateCountdown = () => {
      const now = new Date();
      const reset = new Date(resetTime);
      const diff = reset.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeToReset('即将重置');
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        setTimeToReset(`${hours}小时${minutes}分钟后重置`);
      } else {
        setTimeToReset(`${minutes}分钟后重置`);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [resetTime, remaining]);

  const powerLevelClass = getPowerLevelClass();
  const isExhausted = remaining === 0;

  return (
    <div 
      className={`mystical-magic-power-indicator p-4 bg-mystical-darker rounded-lg border border-mystical-border shadow-mystical ${powerLevelClass}`}
      data-testid="magic-power-indicator"
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-mystical text-mystical-text">
          魔力值 / Magic Power
        </span>
        <span className={`text-lg font-bold font-mystical ${
          isExhausted ? 'text-red-400' : 
          powerLevelClass === 'low' ? 'text-yellow-400' :
          powerLevelClass === 'medium' ? 'text-blue-400' : 
          'text-green-400'
        }`}>
          {remaining}/{total > 0 ? total : '—'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 bg-mystical-dark rounded-full overflow-hidden mb-2">
        <div 
          className={`h-full transition-all duration-500 ${
            isExhausted ? 'bg-red-500' :
            powerLevelClass === 'low' ? 'bg-yellow-500' :
            powerLevelClass === 'medium' ? 'bg-blue-500' :
            'bg-green-500'
          } ${powerLevelClass === 'high' ? 'shadow-mystical-glow' : ''}`}
          style={{ width: `${percentage}%` }}
          data-testid="magic-power-bar"
          role="progressbar"
          aria-valuenow={remaining}
          aria-valuemin={0}
          aria-valuemax={total}
        />
      </div>

      {/* Status Messages */}
      {isExhausted && (
        <div className="mt-2 space-y-1">
          <div className="text-red-400 text-sm font-mystical">
            魔力耗尽 / Magic Exhausted
          </div>
          {resetTime && (
            <div className="text-mystical-muted text-xs font-mystical">
              明日重置 / Tomorrow Reset
            </div>
          )}
          {timeToReset && (
            <div 
              className="text-mystical-accent text-xs font-mystical animate-pulse"
              data-testid="reset-countdown"
            >
              {timeToReset}
            </div>
          )}
        </div>
      )}

      {/* Power Level Indicator */}
      {!isExhausted && (
        <div className="mt-2">
          <div className={`text-xs font-mystical ${
            powerLevelClass === 'low' ? 'text-yellow-400' :
            powerLevelClass === 'medium' ? 'text-blue-400' :
            'text-green-400'
          }`}>
            {powerLevelClass === 'high' && '充沛 / Abundant'}
            {powerLevelClass === 'medium' && '充足 / Sufficient'} 
            {powerLevelClass === 'low' && '不足 / Low'}
          </div>
        </div>
      )}
    </div>
  );
};