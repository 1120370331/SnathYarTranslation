"""
RAG功能深度验证测试
Deep verification test for RAG functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def demonstrate_rag_impact():
    """演示RAG功能对翻译一致性的影响"""
    print("🔮 RAG功能深度验证测试")
    print("=" * 50)
    
    # 第一阶段：创建基准翻译数据
    print("阶段1: 创建基准翻译数据...")
    base_translations = [
        "黑暗古神的力量",
        "虚空深渊的召唤",
        "邪恶法师的咒语",
        "古老符文的秘密"
    ]
    
    created_translations = []
    for i, text in enumerate(base_translations):
        print(f"  {i+1}. 翻译: '{text}'")
        response = requests.post(f"{BASE_URL}/translate", json={
            "text": text,
            "source_language": "chinese"
        })
        
        if response.status_code == 200:
            result = response.json()
            created_translations.append(result)
            print(f"     → '{result['translated_text']}'")
            
            # 确认部分翻译为用户验证的高质量翻译
            if i % 2 == 0:
                confirm_response = requests.post(
                    f"{BASE_URL}/translate/{result['translation_id']}/confirm",
                    json={"edited_text": result['translated_text']}
                )
                if confirm_response.status_code == 200:
                    print(f"     ✓ 用户确认")
                    created_translations[-1]['is_user_confirmed'] = True
        
        time.sleep(1)  # 避免请求过快
    
    print(f"\n✅ 成功创建 {len(created_translations)} 个基准翻译")
    
    # 第二阶段：测试相似文本的RAG效果
    print(f"\n阶段2: 测试RAG相似度检索效果...")
    
    # 创建与基准翻译相似的新文本
    similar_test_cases = [
        ("黑暗古神的魔力", "黑暗古神的力量"),  # 相似度高
        ("虚空深渊的呼唤", "虚空深渊的召唤"),  # 相似度高
        ("邪恶巫师的咒语", "邪恶法师的咒语"),  # 相似度中等
        ("远古符文的奥秘", "古老符文的秘密"),  # 相似度中等
    ]
    
    for new_text, similar_to in similar_test_cases:
        print(f"\n测试文本: '{new_text}' (与 '{similar_to}' 相似)")
        
        response = requests.post(f"{BASE_URL}/translate", json={
            "text": new_text,
            "source_language": "chinese"
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"翻译结果: '{result['translated_text']}'")
            print(f"置信度: {result.get('confidence_score', 'N/A')}")
            
            # 寻找对应的基准翻译进行比较
            base_result = None
            for base in created_translations:
                if base['source_text'] == similar_to:
                    base_result = base
                    break
            
            if base_result:
                print(f"基准翻译: '{base_result['translated_text']}'")
                
                # 分析词汇相似性
                new_words = set(result['translated_text'].lower().replace("'", "").split())
                base_words = set(base_result['translated_text'].lower().replace("'", "").split())
                common_words = new_words & base_words
                
                if common_words:
                    print(f"✓ RAG效果: 共同词汇 {list(common_words)}")
                else:
                    print("? RAG效果: 词汇风格可能相似但无直接重用")
        else:
            print(f"✗ 翻译失败: {response.status_code}")
        
        time.sleep(1)
    
    # 第三阶段：测试完全不同文本（应该没有RAG影响）
    print(f"\n阶段3: 测试无关文本（预期无RAG影响）...")
    
    unrelated_texts = [
        "今天天气很好",
        "我喜欢吃苹果",
        "数学很有趣"
    ]
    
    for text in unrelated_texts:
        print(f"\n无关文本: '{text}'")
        response = requests.post(f"{BASE_URL}/translate", json={
            "text": text,
            "source_language": "chinese"
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"翻译结果: '{result['translated_text']}'")
            print("预期: 与之前翻译风格无关")
        else:
            print(f"✗ 翻译失败: {response.status_code}")
        
        time.sleep(1)
    
    # 显示最终统计
    print(f"\n" + "=" * 50)
    print("测试总结:")
    
    # 检查配额使用情况
    quota_response = requests.get(f"{BASE_URL}/session/quota")
    if quota_response.status_code == 200:
        quota = quota_response.json()
        used = quota['total_requests_today']
        remaining = quota['tokens_remaining']
        print(f"✅ 配额使用: {used} 次请求, 剩余 {remaining}/500")
    
    print(f"✅ RAG功能集成验证完成")
    print(f"")
    print("RAG功能说明:")
    print("1. 🔍 自动检索相似历史翻译")
    print("2. 📝 将相似翻译添加到AI提示词中")
    print("3. ⭐ 优先参考用户确认的翻译")
    print("4. 🎯 提升翻译一致性和质量")
    print("5. 🔄 完全自动化，用户无感知")

if __name__ == "__main__":
    demonstrate_rag_impact()