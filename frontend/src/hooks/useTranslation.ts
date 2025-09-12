/**
 * useTranslation Hook
 * 
 * React hook for handling translation API calls with proper PRD compliance.
 * Includes database matching, correct magic power consumption, and direct save/copy functionality.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export interface TranslationRequest {
  text: string;
  source_language: 'chinese' | 'shathyar';
}

export interface TranslationResponse {
  translated_text: string;
  source_text: string;
  is_cached: boolean;
  is_ai_generated: boolean;
  can_edit: boolean;
  confidence_score?: number;
  translation_id?: string;
  magic_power_remaining?: number;
  source: 'cache' | 'dictionary' | 'ai_generated';
}

export interface UseTranslationResult {
  mutate: (data: TranslationRequest) => void;
  mutateAsync: (data: TranslationRequest) => Promise<TranslationResponse>;
  data: TranslationResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  reset: () => void;
}

// Database simulation for proper PRD compliance
const simulatedDatabase = new Map<string, { translation: string; created_at: string }>();

// Simulate the shasiyaer.csv official dictionary
const officialDictionary: Record<string, string> = {
  "Gul'kafh an'qov N'zoth": "凝视恩佐斯的内心吧",
  "Aglathrax hig' thrixa": "我在你肺里安家了！",
  "Bwaxa za' raga xil": "你的盟友喜欢看着你死去",
  "Bwixki amala zal qulllll": "我会在黑暗中……等你……",
  "Awtgssh shn ongg shg'ullwaq": "没有什么能够阻止我的瘟疫！",
  "Al'ksh syq iir awan? Iilth sythn aqev": "这是真的还是幻觉？你疯了……疯了……疯了……",
  "AN'zig wgah qam za zyqtahg": "戈霍恩是无法阻止的……",
  "Ez Shuul'wah! Sk'woth'gl yu'gaz yoh'ghyl iilth": "哦死亡之翼！您忠实的仆人辜负了您！"
};

// Magic power tracker (simulates server-side state)
let currentMagicPower = 500;

// Mock API client with proper PRD business logic
const mockApiClient = {
  async translate(data: TranslationRequest): Promise<TranslationResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    if (data.source_language === 'chinese') {
      // 中文 → 沙斯亚尔语 (按PRD要求)
      
      // 1. 先检查数据库中是否已有相同的中文
      const cachedTranslation = simulatedDatabase.get(data.text);
      if (cachedTranslation) {
        // 找到缓存，直接返回，不消耗魔力
        return {
          translated_text: cachedTranslation.translation,
          source_text: data.text,
          is_cached: true,
          is_ai_generated: false,
          can_edit: false,
          confidence_score: 1.0,
          translation_id: 'cache_' + Date.now(),
          magic_power_remaining: currentMagicPower, // 不消耗魔力
          source: 'cache'
        };
      }
      
      // 2. 检查魔力值是否足够
      if (currentMagicPower <= 0) {
        throw new Error('魔力耗尽，请等待重置 / Magic power exhausted, please wait for reset');
      }
      
      // 3. 消耗魔力值（在点击翻译时消耗）
      currentMagicPower -= 1;
      
      // 4. 生成AI翻译
      const aiTranslation = generateShathyarStyleTranslation(data.text);
      
      return {
        translated_text: aiTranslation,
        source_text: data.text,
        is_cached: false,
        is_ai_generated: true,
        can_edit: true,
        confidence_score: 0.85,
        translation_id: 'ai_' + Date.now(),
        magic_power_remaining: currentMagicPower,
        source: 'ai_generated'
      };
      
    } else {
      // 沙斯亚尔语 → 中文 (按PRD要求)
      
      // 1. 先检查官方词典
      const dictionaryTranslation = officialDictionary[data.text];
      if (dictionaryTranslation) {
        return {
          translated_text: dictionaryTranslation,
          source_text: data.text,
          is_cached: true,
          is_ai_generated: false,
          can_edit: false,
          confidence_score: 1.0,
          translation_id: 'dict_' + Date.now(),
          magic_power_remaining: currentMagicPower, // 不消耗魔力
          source: 'dictionary'
        };
      }
      
      // 2. 检查用户数据库
      const reverseCache = Array.from(simulatedDatabase.entries())
        .find(([chinese, data]) => data.translation === data.text);
      
      if (reverseCache) {
        return {
          translated_text: reverseCache[0],
          source_text: data.text,
          is_cached: true,
          is_ai_generated: false,
          can_edit: false,
          confidence_score: 1.0,
          translation_id: 'cache_' + Date.now(),
          magic_power_remaining: currentMagicPower,
          source: 'cache'
        };
      }
      
      // 3. 未找到翻译，返回"破译失败"
      throw new Error('破译失败...');
    }
  },

  async confirmTranslation(translationId: string, editedText: string, originalChinese: string): Promise<TranslationResponse> {
    // 模拟确认翻译API
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // 保存到数据库
    simulatedDatabase.set(originalChinese, {
      translation: editedText,
      created_at: new Date().toISOString()
    });

    return {
      translated_text: editedText,
      source_text: originalChinese,
      is_cached: true,
      is_ai_generated: true,
      can_edit: false,
      confidence_score: 1.0,
      translation_id: translationId,
      magic_power_remaining: currentMagicPower,
      source: 'cache'
    };
  }
};

// Generate Shathyar-style translation based on linguistic patterns (improved version)
function generateShathyarStyleTranslation(chineseText: string): string {
  // Enhanced Shathyar phonemes and patterns from the dictionary
  const shathyarSyllables = [
    'ak', 'an', 'ag', 'al', 'aw', 'bw', 'ez', 'gul', 'hig', 'iil', 'ka', 
    'ma', 'nh', 'qu', 'ra', 'sh', 'sy', 'th', 'ul', 'wa', 'za', 'zi',
    'kafh', 'qov', 'thri', 'uhn', 'wah', 'lll', 'oth', 'gaz', 'yoh',
    'agth', 'shir', 'vwah', 'xixa', 'zyq', 'shuul', 'wgah', 'qulll',
    'vash', 'jir', 'kul', 'thrak', 'mor', 'dun', 'yashu', 'talar', 'korrath'
  ];
  
  const shathyarEndings = ["'ah", "'gl", "'xa", "'th", "'ov", "'uq", "'wn", "'ksh"];
  const shathyarConnectors = ["'", "gh'", "h'", "q'"];
  
  // More sophisticated word generation based on Chinese text characteristics
  const characters = Array.from(chineseText);
  const wordCount = Math.max(1, Math.min(5, Math.ceil(characters.length / 2)));
  
  let result = [];
  
  for (let i = 0; i < wordCount; i++) {
    let word = '';
    
    // Add 1-3 syllables per word, weighted towards 2
    const syllableCount = Math.random() > 0.7 ? 3 : Math.random() > 0.3 ? 2 : 1;
    
    for (let j = 0; j < syllableCount; j++) {
      if (j === 0) {
        // First syllable - can be any
        word += shathyarSyllables[Math.floor(Math.random() * shathyarSyllables.length)];
      } else {
        // Additional syllables
        if (Math.random() > 0.6) {
          word += shathyarConnectors[Math.floor(Math.random() * shathyarConnectors.length)];
        }
        word += shathyarSyllables[Math.floor(Math.random() * shathyarSyllables.length)];
      }
    }
    
    // Sometimes add ending
    if (Math.random() > 0.5) {
      word += shathyarEndings[Math.floor(Math.random() * shathyarEndings.length)];
    }
    
    result.push(word);
  }
  
  // Capitalize first letter of each word and add some punctuation
  const finalResult = result.map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
  
  // Add some mystical punctuation
  if (chineseText.includes('！') || chineseText.includes('!')) {
    return finalResult + '!';
  } else if (chineseText.includes('？') || chineseText.includes('?')) {
    return finalResult + '?';
  } else if (chineseText.includes('。') || chineseText.includes('.')) {
    return finalResult + '.';
  } else if (Math.random() > 0.7) {
    return finalResult + '...';
  }
  
  return finalResult;
}

export const useTranslation = (): UseTranslationResult => {
  const queryClient = useQueryClient();
  
  const mutation = useMutation<TranslationResponse, Error, TranslationRequest>({
    mutationFn: mockApiClient.translate,
    onSuccess: (data) => {
      // Invalidate related queries on successful translation
      queryClient.invalidateQueries(['magic-power']);
      queryClient.invalidateQueries(['translation-history']);
    },
    onError: (error) => {
      console.error('Translation failed:', error);
    }
  });

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    data: mutation.data,
    isLoading: mutation.isLoading,
    error: mutation.error,
    reset: mutation.reset
  };
};

// Export confirmation function for direct use
export const useConfirmTranslation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ translationId, editedText, originalChinese }: { translationId: string, editedText: string, originalChinese: string }) => 
      mockApiClient.confirmTranslation(translationId, editedText, originalChinese),
    onSuccess: () => {
      queryClient.invalidateQueries(['translation-history']);
    }
  });
};