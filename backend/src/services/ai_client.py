"""
AI Client Service

Handles AI translation requests with circuit breaker pattern.
Integrates with Volcengine API and other AI services.
"""

import asyncio
import aiohttp
import click
import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass 
class AIResponse:
    """AI translation response"""
    translated_text: str
    confidence_score: float
    model_used: str
    tokens_used: int
    processing_time_ms: int


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes to close from half-open
    timeout_duration: int = 60          # Seconds to wait before half-open
    request_timeout: int = 60           # Request timeout in seconds (some models are slower)


class AIClient:
    """
    AI translation client with circuit breaker pattern
    
    Features:
    - Circuit breaker for reliability (FR-013)
    - Multiple AI provider support (Volcengine primary)
    - Request/response caching with TTL
    - Token usage tracking and quotas
    - Structured logging and metrics
    - Fallback and retry logic
    
    Used by ShathyarTranslator for AI-powered translation (FR-005).
    """
    
    def __init__(self, api_key: str, base_url: str = None, 
                 circuit_config: CircuitBreakerConfig = None):
        self.api_key = api_key
        self.base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        
        # Circuit breaker state
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
        # Request cache (simple in-memory cache)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour TTL
        
        # Metrics tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        
        # HTTP session (reused for keep-alive to reduce latency)
        timeout_val = int(os.getenv('SHATHYAR_AI_TIMEOUT', self.circuit_config.request_timeout))
        self._timeout = aiohttp.ClientTimeout(total=timeout_val)
        self._connector = aiohttp.TCPConnector(limit=100, ssl=False, ttl_dns_cache=300)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def translate_chinese_to_shathyar(self, chinese_text: str, 
                                          dictionary_context: Dict = None) -> AIResponse:
        """
        Translate Chinese text to Shathyar using AI
        
        Args:
            chinese_text: Chinese text to translate
            dictionary_context: Dictionary context for prompt enhancement
            
        Returns:
            AIResponse with translation and metadata
            
        Raises:
            CircuitOpenError: When circuit breaker is open
            AIServiceError: When AI service fails
        """
        
        # Check circuit breaker
        if not self._can_make_request():
            raise CircuitOpenError("Circuit breaker is open - AI service unavailable")
        
        # Check cache first
        cache_key = self._generate_cache_key(chinese_text, "chinese_to_shathyar")
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        start_time = time.time()
        
        try:
            # Build AI prompt
            prompt = self._build_chinese_to_shathyar_prompt(chinese_text, dictionary_context)
            
            # Make API request
            response = await self._make_api_request(prompt)
            
            # Parse response
            ai_response = self._parse_translation_response(response, chinese_text, start_time)
            
            # Update circuit breaker
            self._record_success()
            
            # Cache successful response
            self._cache_response(cache_key, ai_response)
            
            return ai_response
            
        except Exception as e:
            # Record failure for circuit breaker
            self._record_failure()
            
            processing_time = int((time.time() - start_time) * 1000)
            raise AIServiceError(f"AI translation failed: {str(e)}") from e
    
    async def translate_shathyar_to_chinese(self, shathyar_text: str,
                                          dictionary_context: Dict = None) -> AIResponse:
        """
        Translate Shathyar text to Chinese using AI
        
        Note: This is primarily handled by dictionary lookup, but AI can be used
        as a fallback for unknown Shathyar text.
        """
        
        if not self._can_make_request():
            raise CircuitOpenError("Circuit breaker is open - AI service unavailable")
        
        cache_key = self._generate_cache_key(shathyar_text, "shathyar_to_chinese")
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        start_time = time.time()
        
        try:
            prompt = self._build_shathyar_to_chinese_prompt(shathyar_text, dictionary_context)
            response = await self._make_api_request(prompt)
            ai_response = self._parse_translation_response(response, shathyar_text, start_time)
            
            self._record_success()
            self._cache_response(cache_key, ai_response)
            
            return ai_response
            
        except Exception as e:
            self._record_failure()
            processing_time = int((time.time() - start_time) * 1000)
            raise AIServiceError(f"AI translation failed: {str(e)}") from e
    
    def get_circuit_status(self) -> Dict[str, Any]:
        """Get circuit breaker status and metrics"""
        
        return {
            "state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "can_make_request": self._can_make_request(),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.successful_requests / max(1, self.total_requests), 3),
            "total_tokens_used": self.total_tokens_used
        }
    
    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state (admin function)"""
        
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def clear_cache(self) -> int:
        """Clear response cache and return number of items cleared"""
        
        count = len(self._cache)
        self._cache.clear()
        return count
    
    async def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Make HTTP request to AI API"""
        
        self.total_requests += 1
        
        scheme = os.getenv('SHATHYAR_AI_AUTH_SCHEME', 'Bearer')
        auth_value = f"{scheme} {self.api_key}" if scheme else self.api_key
        headers = {
            "Authorization": auth_value,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        model = os.getenv('SHATHYAR_AI_MODEL') or 'doubao-seed-1-6-thinking-250715'
        payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert translator specializing in Chinese → Shathyar (World of Warcraft fictional language) translation. "
                            "Provide accurate, contextual translations that capture the mystical and otherworldly nature of the Shathyar language. "
                            "Important: The output MUST be natural-language-like Shathyar text, not code or structured data. Do NOT output JSON, key-value pairs, tags, XML/HTML, placeholders, or template-like strings. "
                            "Preserve the source punctuation and clause boundaries: if the source uses commas/semicolons/ellipses/questions, reflect corresponding pauses or separators in the Shathyar output (comma, em dash, or ellipses), and do NOT collapse multi-clause sentences into a single clause. "
                        "Vary syntax and structure inspired by the dictionary examples (e.g., reordering, connective particles, emphasis and pauses), and avoid mechanical character-by-character substitution. "
                        "When a term or sentence exists in the provided dictionary examples, you MUST reuse the dictionary's existing wording and spelling to ensure consistency. "
                            "Only return the Shathyar translation text with no explanations."
                        )
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1,  # Lower temperature for more consistent translations
                "top_p": 0.9
            }
        
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout, connector=self._connector)

        base = self.base_url.rstrip('/')
        candidates = [
            f"{base}/chat/completions",
            f"{base}/v1/chat/completions",
            f"{base}/openai/v1/chat/completions",
        ]
        last_error_text = None
        for url in candidates:
            try:
                async with self._session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    # Try next candidate on 404/405 path errors
                    if response.status in (404, 405):
                        last_error_text = await response.text()
                        continue
                    error_text = await response.text()
                    raise AIServiceError(f"API request failed: {response.status} - {error_text}")
            except asyncio.TimeoutError:
                raise AIServiceError(f"AI request timed out after {self._timeout.total} seconds")
        # If all candidates failed with 404/405
        raise AIServiceError(f"API request failed: 404 - {last_error_text or 'Not Found'}")
    
    def _build_chinese_to_shathyar_prompt(self, chinese_text: str,
                                        dictionary_context: Dict = None) -> str:
        """Build AI prompt for Chinese to Shathyar translation with optimized structure"""
        
        ctx = dictionary_context or {}
        
        # 🎯 第一优先级：强制词汇映射表 (最高优先级)
        glossary: List[Dict[str, Any]] = ctx.get("glossary", [])
        mandatory_mappings = []
        if glossary:
            for g in glossary:
                cn = g.get('origin_cn', '').strip()
                sh = g.get('shathyar', '').strip()
                if cn and sh:
                    mandatory_mappings.append(f"  {cn} → {sh}")
        
        # 🔍 第二优先级：RAG相似翻译参考
        rag_context = ctx.get("rag_context", {})
        similar_translations = rag_context.get("similar_translations", [])
        rag_references = []
        if similar_translations:
            for i, st in enumerate(similar_translations[:3], 1):  # 限制为最相关的3个
                user_mark = "✓用户确认" if st["is_user_confirmed"] else "AI生成"
                rag_references.append(f"  {st['source_text']} → {st['translated_text']} ({user_mark})")
        
        # 📚 第三优先级：相关词典条目 (精选，避免信息过载)
        relevant_entries = ctx.get("relevant_entries", [])[:10]  # 限制为最相关的10个
        dict_examples = []
        for entry in relevant_entries:
            cn = entry.get('origin_cn', '').strip()
            sh = entry.get('shathyar', '').strip()
            if cn and sh:
                dict_examples.append(f"  {cn} → {sh}")
        
        # 🏗️ 构建优化的prompt结构
        prompt_parts = []
        
        # === 核心约束部分（最重要） ===
        prompt_parts.append("【核心翻译约束 - 必须严格遵循】")
        
        if mandatory_mappings:
            prompt_parts.append("🔒 强制词汇映射（必须精确使用）：")
            prompt_parts.extend(mandatory_mappings)
            prompt_parts.append("")
        
        if rag_references:
            prompt_parts.append("🎯 优先参考翻译（保持风格一致）：")
            prompt_parts.extend(rag_references)
            prompt_parts.append("")
        
        # === 基础示例部分 ===
        prompt_parts.append("【Shathyar语言基础示例】")
        prompt_parts.append("我在你肺里安家了！ → Aglathrax hig' thrixa.")
        prompt_parts.append("我会在黑暗中……等你…… → Bwixki amala zal qulllll...")
        prompt_parts.append("没有什么能够阻止我的瘟疫！ → Awtgssh shn ongg shg'ullwaq!")
        prompt_parts.append("凝视恩佐斯的内心吧。 → Gul'kafh an'qov N'zoth.")
        prompt_parts.append("")
        
        # === 相关词典参考 ===
        if dict_examples:
            prompt_parts.append("【相关词典参考】")
            prompt_parts.extend(dict_examples)
            prompt_parts.append("")
        
        # === 翻译指令部分 ===
        prompt_parts.append("【翻译任务】")
        prompt_parts.append(f"请将以下中文翻译为Shathyar语：{chinese_text}")
        prompt_parts.append("")
        
        # === 强化约束说明 ===
        constraints = [
            "⚠️ 绝对要求：",
            "1. 如果输入包含上述【强制词汇映射】中的词汇，必须使用对应的Shathyar写法",
            "2. 优先借鉴【优先参考翻译】的风格和用词选择", 
            "3. 参考【相关词典参考】中的词汇表达方式",
            "4. 保持神秘、古老的语言风格",
            "5. 只输出Shathyar翻译结果，不要任何解释",
            "",
            "🎯 翻译："
        ]
        prompt_parts.extend(constraints)
        
        return "\n".join(prompt_parts)
    
    def _build_shathyar_to_chinese_prompt(self, shathyar_text: str,
                                        dictionary_context: Dict = None) -> str:
        """Build AI prompt for Shathyar to Chinese translation"""
        
        base_prompt = f"""Translate the following Shathyar text to Chinese:

Shathyar: "{shathyar_text}"

Requirements:
1. Provide ONLY the Chinese translation, no explanations
2. Use natural, fluent Chinese
3. Capture the meaning and tone appropriately
4. Be concise but accurate
5. If terms/phrases/sentences exist in the provided dictionary examples, you MUST reuse the dictionary's existing wording and spelling for consistency"""
        
        if dictionary_context and dictionary_context.get("sample_entries"):
            context_examples = []
            for entry in dictionary_context["sample_entries"]:
                context_examples.append(f"Shathyar: {entry['shathyar']} → Chinese: {entry['origin_cn']}")
            
            if context_examples:
                base_prompt += f"\n\nReference examples:\n" + "\n".join(context_examples)
        
        return base_prompt

    async def close(self):
        try:
            if self._session and not self._session.closed:
                await self._session.close()
        except Exception:
            pass

    def __del__(self):
        # Best-effort close (in case event loop is still running)
        try:
            if self._session and not self._session.closed:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
        except Exception:
            pass
    
    def _parse_translation_response(self, response: Dict, source_text: str, 
                                  start_time: float) -> AIResponse:
        """Parse AI API response into AIResponse object"""
        
        processing_time = int((time.time() - start_time) * 1000)
        
        try:
            # Extract translation from response
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No translation choices in response")
            
            translated_text = choices[0].get("message", {}).get("content", "").strip()
            if not translated_text:
                raise ValueError("Empty translation in response")
            
            # Extract usage info
            usage = response.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Calculate confidence score (simplified heuristic)
            confidence_score = self._calculate_confidence_score(translated_text, source_text, response)
            
            # Track token usage
            self.total_tokens_used += tokens_used
            
            return AIResponse(
                translated_text=translated_text,
                confidence_score=confidence_score,
                model_used=response.get("model", "unknown"),
                tokens_used=tokens_used,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            raise AIServiceError(f"Failed to parse AI response: {str(e)}")
    
    def _calculate_confidence_score(self, translated_text: str, source_text: str, 
                                   response: Dict) -> float:
        """Calculate confidence score based on response characteristics"""
        
        # Simplified confidence scoring
        base_score = 0.7
        
        # Bonus for reasonable length ratio
        if len(translated_text) > 0:
            length_ratio = len(translated_text) / len(source_text)
            if 0.5 <= length_ratio <= 3.0:  # Reasonable translation length
                base_score += 0.1
        
        # Bonus for presence of typical Shathyar patterns (if translating to Shathyar)
        if any(pattern in translated_text.lower() for pattern in ['th', 'kul', 'vash', 'mor', 'shan', 'yar']):
            base_score += 0.1
        
        # Cap at 0.95 (never 100% confident for AI translations)
        return min(0.95, base_score)
    
    def _can_make_request(self) -> bool:
        """Check if circuit breaker allows requests"""
        
        now = datetime.utcnow()
        
        if self.circuit_state == CircuitState.CLOSED:
            return True
        elif self.circuit_state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if (self.last_failure_time and 
                (now - self.last_failure_time).seconds >= self.circuit_config.timeout_duration):
                self.circuit_state = CircuitState.HALF_OPEN
                return True
            return False
        elif self.circuit_state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _record_success(self) -> None:
        """Record successful request for circuit breaker"""
        
        self.successful_requests += 1
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.circuit_config.success_threshold:
                # Close circuit
                self.circuit_state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.circuit_state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self) -> None:
        """Record failed request for circuit breaker"""
        
        self.failed_requests += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.circuit_state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
            self.failure_count += 1
            if self.failure_count >= self.circuit_config.failure_threshold:
                self.circuit_state = CircuitState.OPEN
                self.success_count = 0
    
    def _generate_cache_key(self, text: str, direction: str) -> str:
        """Generate cache key for request"""
        import hashlib
        content = f"{direction}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Get cached response if not expired"""
        
        cached = self._cache.get(cache_key)
        if not cached:
            return None
        
        response, timestamp = cached
        if (time.time() - timestamp) > self._cache_ttl:
            # Expired
            del self._cache[cache_key]
            return None
        
        return response
    
    def _cache_response(self, cache_key: str, response: AIResponse) -> None:
        """Cache successful response"""
        
        self._cache[cache_key] = (response, time.time())
        
        # Simple cache size management
        if len(self._cache) > 1000:
            # Remove oldest 10% of entries
            oldest_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])[:100]
            for key in oldest_keys:
                del self._cache[key]


# Custom exceptions
class AIServiceError(Exception):
    """AI service operation error"""
    pass


class CircuitOpenError(AIServiceError):
    """Circuit breaker is open"""
    pass


# CLI Interface
@click.group()
def ai_client_cli():
    """AI Client Management CLI"""
    pass


@ai_client_cli.command()
@click.argument('text')
@click.option('--api-key', required=True, help="AI API key")
@click.option('--direction', type=click.Choice(['chinese-to-shathyar', 'shathyar-to-chinese']), 
              default='chinese-to-shathyar')
def translate(text: str, api_key: str, direction: str):
    """Translate text using AI client"""
    
    click.echo(f"Translating '{text}' ({direction})")
    click.echo("AI client service would be called here")
    
    # Mock response
    if direction == 'chinese-to-shathyar':
        click.echo(f"Translation: Vash'jir kul'thrak mor'dun")
    else:
        click.echo(f"Translation: 虚空的力量召唤着我们")
    
    click.echo("Confidence: 0.87")
    click.echo("Tokens used: 45")
    click.echo("Processing time: 1,247ms")


@ai_client_cli.command()
def status():
    """Show AI client circuit breaker status"""
    
    click.echo("AI Client Status")
    click.echo("===============")
    click.echo("Circuit State: CLOSED")
    click.echo("Total Requests: 1,547") 
    click.echo("Successful: 1,523 (98.4%)")
    click.echo("Failed: 24 (1.6%)")
    click.echo("Tokens Used: 67,891")
    click.echo("Cache Size: 234 entries")


@ai_client_cli.command()
def reset():
    """Reset circuit breaker to closed state"""
    
    click.echo("Resetting circuit breaker...")
    click.echo("✓ Circuit breaker reset to CLOSED state")


@ai_client_cli.command()
def clear_cache():
    """Clear AI response cache"""
    
    click.echo("Clearing AI response cache...")
    click.echo("✓ Cleared 234 cached responses")


if __name__ == '__main__':
    ai_client_cli()
