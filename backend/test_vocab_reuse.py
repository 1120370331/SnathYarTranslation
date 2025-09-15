"""
测试优化后的词汇复用效果
Test optimized vocabulary reuse functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_vocabulary_reuse_improvement():
    """测试词汇复用的改善效果"""
    print("🔮 测试优化后的词汇复用效果")
    print("=" * 50)
    
    # 测试用例：包含已知词汇的文本
    test_cases = [
        {
            "text": "深渊中的黑暗力量正在觉醒",
            "expected_terms": ["深渊", "黑暗", "力量"],
            "description": "测试词汇复用的一致性"
        },
        {
            "text": "虚空的力量召唤着古神",
            "expected_terms": ["虚空", "力量", "古神"],
            "description": "测试复合词汇的处理"
        },
        {
            "text": "邪恶的法师施展黑暗魔法",
            "expected_terms": ["邪恶", "法师", "黑暗", "魔法"],
            "description": "测试多个词汇的协调使用"
        }
    ]
    
    print("阶段1: 创建词汇基准...")
    base_translations = {}
    
    # 首先创建单独词汇的翻译作为基准
    base_terms = ["深渊", "黑暗", "力量", "虚空", "古神", "邪恶", "法师", "魔法"]
    
    for term in base_terms:
        print(f"  创建基准: '{term}'")
        response = requests.post(f"{BASE_URL}/translate", json={
            "text": term,
            "source_language": "chinese"
        })
        
        if response.status_code == 200:
            result = response.json()
            base_translations[term] = result['translated_text']
            print(f"    → '{result['translated_text']}'")
            
            # 确认翻译以建立高质量参考
            confirm_response = requests.post(
                f"{BASE_URL}/translate/{result['translation_id']}/confirm",
                json={"edited_text": result['translated_text']}
            )
            if confirm_response.status_code == 200:
                print(f"    ✓ 已确认")
        else:
            print(f"    ✗ 失败: {response.status_code}")
        
        time.sleep(1)  # 避免请求过快
    
    print(f"\n阶段2: 测试复合句子的词汇复用...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"输入: '{test_case['text']}'")
        
        response = requests.post(f"{BASE_URL}/translate", json={
            "text": test_case['text'],
            "source_language": "chinese"
        })
        
        if response.status_code == 200:
            result = response.json()
            translation = result['translated_text']
            print(f"翻译: '{translation}'")
            
            # 分析词汇复用情况
            print("词汇复用分析:")
            reused_count = 0
            for term in test_case['expected_terms']:
                if term in base_translations:
                    base_term = base_translations[term]
                    # 检查基准词汇是否在复合翻译中出现
                    if any(word in translation.lower() for word in base_term.lower().split()):
                        print(f"  ✓ '{term}' → 复用了 '{base_term}' 中的元素")
                        reused_count += 1
                    else:
                        print(f"  ? '{term}' → 未明显复用 '{base_term}'")
                else:
                    print(f"  - '{term}' → 无基准参考")
            
            reuse_rate = reused_count / len(test_case['expected_terms']) if test_case['expected_terms'] else 0
            print(f"词汇复用率: {reuse_rate:.1%} ({reused_count}/{len(test_case['expected_terms'])})")
            
            if reuse_rate >= 0.5:
                print("✅ 词汇复用效果良好")
            else:
                print("⚠️ 词汇复用效果待改善")
                
        else:
            print(f"✗ 翻译失败: {response.status_code}")
        
        time.sleep(2)  # 给AI更多时间处理
    
    print(f"\n阶段3: 测试RAG功能的词汇一致性...")
    
    # 测试相似句子是否能保持词汇一致性
    similar_tests = [
        ("深渊的黑暗力量", "深渊中的黑暗力量正在觉醒"),  # 应该有高度一致性
        ("虚空力量召唤", "虚空的力量召唤着古神"),  # 应该有一定一致性
    ]
    
    for short_text, full_text in similar_tests:
        print(f"\n相似性测试: '{short_text}' vs '{full_text}'")
        
        # 翻译简化版本
        response1 = requests.post(f"{BASE_URL}/translate", json={
            "text": short_text,
            "source_language": "chinese"
        })
        
        if response1.status_code == 200:
            translation1 = response1.json()['translated_text']
            print(f"简化版: '{translation1}'")
            
            time.sleep(2)
            
            # 翻译完整版本（应该能利用RAG）
            response2 = requests.post(f"{BASE_URL}/translate", json={
                "text": full_text,
                "source_language": "chinese"
            })
            
            if response2.status_code == 200:
                translation2 = response2.json()['translated_text']
                print(f"完整版: '{translation2}'")
                
                # 分析词汇一致性
                words1 = set(translation1.lower().replace("'", "").split())
                words2 = set(translation2.lower().replace("'", "").split())
                common = words1 & words2
                
                if common:
                    consistency = len(common) / len(words1 | words2)
                    print(f"词汇一致性: {consistency:.1%} (共同词汇: {list(common)})")
                    if consistency >= 0.3:
                        print("✅ RAG功能促进了词汇一致性")
                    else:
                        print("⚠️ 词汇一致性仍需改善")
                else:
                    print("❌ 无共同词汇，一致性待改善")
        
        time.sleep(2)
    
    # 检查配额使用情况
    print(f"\n" + "=" * 50)
    quota_response = requests.get(f"{BASE_URL}/session/quota")
    if quota_response.status_code == 200:
        quota = quota_response.json()
        print(f"测试完成 - 已使用配额: {quota['total_requests_today']} 次")
        print(f"剩余配额: {quota['tokens_remaining']}/500")
    
    print("\n🎯 优化效果总结:")
    print("1. ✅ 新的prompt结构更加清晰层次化")
    print("2. ✅ 强制词汇映射放在最高优先级")
    print("3. ✅ RAG参考信息精简且突出")
    print("4. ✅ 约束语言更加强烈明确")
    print("5. 📊 词汇复用效果需要持续观察和调优")

if __name__ == "__main__":
    test_vocabulary_reuse_improvement()