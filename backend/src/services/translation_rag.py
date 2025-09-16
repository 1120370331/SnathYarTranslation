"""
Translation RAG Service

检索增强生成(RAG)服务，用于从历史翻译记录中检索相似翻译作为AI参考信息。
Retrieval-Augmented Generation service for finding similar translations from history as AI reference.
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from collections import Counter

from ..models.translation_entry import TranslationEntry
from ..utils.normalize import normalize_text


@dataclass
class SimilarTranslation:
    """相似翻译记录"""
    source_text: str
    translated_text: str
    similarity_score: float
    translation_id: str
    is_ai_generated: bool
    is_user_confirmed: bool
    confidence_score: Optional[float] = None


class TranslationRAG:
    """
    翻译RAG检索服务
    
    Features:
    - 基于词汇重叠的相似度计算
    - 语义关键词提取
    - 长度权重调整
    - 用户确认翻译优先级
    - 结果去重和排序
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.min_similarity_threshold = 0.3  # 最小相似度阈值
        self.max_results = 5  # 最大返回结果数
        
        # 中文停用词 (简化版)
        self.chinese_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '这个', '那个', '什么', '怎么', '为什么', '可以', '能够',
            '！', '？', '。', '，', '、', '；', '：', '"', '"', ''', ''', '（', '）',
            '【', '】', '…', '——', '—', '·', '》', '《'
        }
    
    def find_similar_translations(self, query_text: str, source_language: str, 
                                limit: int = None) -> List[SimilarTranslation]:
        """
        查找相似的历史翻译记录
        
        Args:
            query_text: 查询文本 
            source_language: 源语言 ("chinese" or "shathyar")
            limit: 返回结果数量限制
            
        Returns:
            按相似度排序的相似翻译列表
        """
        
        if limit is None:
            limit = self.max_results
            
        # 规范化查询文本
        normalized_query = normalize_text(query_text)
        if not normalized_query:
            return []
        
        # 提取查询关键词
        query_keywords = self._extract_keywords(query_text, source_language)
        if not query_keywords:
            return []
        
        # 从数据库获取候选翻译记录
        candidates = self._get_translation_candidates(source_language)
        
        # 计算相似度并排序
        similar_translations = []
        for candidate in candidates:
            similarity = self._calculate_similarity(
                query_text, candidate.source_text, 
                query_keywords, source_language
            )
            
            if similarity >= self.min_similarity_threshold:
                similar_translations.append(SimilarTranslation(
                    source_text=candidate.source_text,
                    translated_text=candidate.translated_text,
                    similarity_score=similarity,
                    translation_id=candidate.id,
                    is_ai_generated=candidate.is_ai_generated,
                    is_user_confirmed=candidate.is_user_confirmed,
                    confidence_score=candidate.confidence_score
                ))
        
        # 按相似度排序，用户确认的翻译优先
        similar_translations.sort(
            key=lambda x: (x.is_user_confirmed, x.similarity_score),
            reverse=True
        )
        
        # 去重：如果有多个相似的翻译，保留最好的
        deduplicated = self._deduplicate_translations(similar_translations)
        
        return deduplicated[:limit]
    
    def _get_translation_candidates(self, source_language: str) -> List[TranslationEntry]:
        """获取翻译候选记录"""
        
        # 优先获取用户确认的翻译，然后是AI生成的翻译
        query = self.db_session.query(TranslationEntry).filter(
            TranslationEntry.source_language == source_language
        ).order_by(
            TranslationEntry.is_user_confirmed.desc(),
            TranslationEntry.confidence_score.desc()
        )
        
        # 限制候选数量以提高性能
        return query.limit(1000).all()
    
    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """提取文本关键词"""
        
        if language == "chinese":
            return self._extract_chinese_keywords(text)
        else:
            return self._extract_shathyar_keywords(text)
    
    def _extract_chinese_keywords(self, text: str) -> List[str]:
        """提取中文关键词"""

        # 基础文本清理
        text = normalize_text(text)

        # 简单的中文分词 (基于字符和标点)
        # 这里使用简化方法，实际项目中可考虑使用jieba等专业分词工具
        words = []
        current_word = ""

        for char in text:
            if char.isspace() or char in '，。！？；：、""''（）【】《》…——':
                if current_word and current_word not in self.chinese_stopwords:
                    words.append(current_word)
                current_word = ""
            else:
                current_word += char

        if current_word and current_word not in self.chinese_stopwords:
            words.append(current_word)

        # 提取2-4字的词组作为关键词
        keywords = []
        for word in words:
            if 2 <= len(word) <= 4:
                keywords.append(word)

                # 如果词长度大于2，也添加所有2字子词用于更好的匹配
                if len(word) > 2:
                    for i in range(len(word) - 1):
                        subword = word[i:i+2]
                        if subword not in self.chinese_stopwords:
                            keywords.append(subword)

        # 如果没有合适长度的词，使用单字
        if not keywords:
            keywords = [char for char in text if char not in self.chinese_stopwords
                       and not char.isspace() and char.isalnum()]

        # 去重保持顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords
    
    def _extract_shathyar_keywords(self, text: str) -> List[str]:
        """提取Shathyar关键词"""
        
        # Shathyar使用空格分词
        text = normalize_text(text)
        words = re.findall(r"[a-zA-Z']+", text)
        
        # 过滤短词和常见词
        shathyar_stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [word.lower() for word in words 
                   if len(word) >= 2 and word.lower() not in shathyar_stopwords]
        
        return keywords
    
    def _calculate_similarity(self, query_text: str, candidate_text: str, 
                            query_keywords: List[str], language: str) -> float:
        """计算文本相似度"""
        
        # 提取候选文本关键词
        candidate_keywords = self._extract_keywords(candidate_text, language)
        
        if not query_keywords or not candidate_keywords:
            return 0.0
        
        # 计算关键词重叠相似度 (Jaccard相似度)
        query_set = set(query_keywords)
        candidate_set = set(candidate_keywords)
        
        intersection = len(query_set & candidate_set)
        union = len(query_set | candidate_set)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # 计算词频相似度 (余弦相似度)
        query_counter = Counter(query_keywords)
        candidate_counter = Counter(candidate_keywords)
        
        # 获取所有关键词
        all_keywords = set(query_keywords + candidate_keywords)
        
        # 构建向量
        query_vector = [query_counter.get(keyword, 0) for keyword in all_keywords]
        candidate_vector = [candidate_counter.get(keyword, 0) for keyword in all_keywords]
        
        # 计算余弦相似度
        cosine_similarity = self._cosine_similarity(query_vector, candidate_vector)
        
        # 长度相似度权重
        len_query = len(normalize_text(query_text))
        len_candidate = len(normalize_text(candidate_text))
        
        if len_query == 0 or len_candidate == 0:
            length_similarity = 0.0
        else:
            length_ratio = min(len_query, len_candidate) / max(len_query, len_candidate)
            length_similarity = length_ratio ** 0.5  # 平方根缓解长度差异惩罚
        
        # 综合相似度计算
        # Jaccard: 40%, Cosine: 40%, Length: 20%
        total_similarity = (
            jaccard_similarity * 0.4 + 
            cosine_similarity * 0.4 + 
            length_similarity * 0.2
        )
        
        return total_similarity
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _deduplicate_translations(self, translations: List[SimilarTranslation]) -> List[SimilarTranslation]:
        """去重相似翻译"""
        
        seen_translations = set()
        deduplicated = []
        
        for translation in translations:
            # 使用规范化的翻译文本作为去重键
            normalized_translated = normalize_text(translation.translated_text)
            
            if normalized_translated not in seen_translations:
                seen_translations.add(normalized_translated)
                deduplicated.append(translation)
        
        return deduplicated
    
    def format_rag_context(self, similar_translations: List[SimilarTranslation]) -> Dict[str, Any]:
        """格式化RAG上下文信息供AI使用"""
        
        if not similar_translations:
            return {}
        
        context = {
            "similar_translations": [
                {
                    "source_text": st.source_text,
                    "translated_text": st.translated_text,
                    "similarity_score": round(st.similarity_score, 3),
                    "is_user_confirmed": st.is_user_confirmed,
                    "confidence_score": st.confidence_score
                }
                for st in similar_translations
            ],
            "total_found": len(similar_translations),
            "highest_similarity": round(similar_translations[0].similarity_score, 3),
            "user_confirmed_count": sum(1 for st in similar_translations if st.is_user_confirmed)
        }
        
        return context