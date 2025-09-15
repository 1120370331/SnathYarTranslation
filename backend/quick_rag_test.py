"""
简化版RAG功能测试
Simplified RAG functionality test
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def quick_rag_test():
    """快速RAG功能测试"""
    print("🔮 快速RAG功能测试")
    print("=" * 40)
    
    # 1. 创建第一个翻译（历史数据）
    print("1. 创建历史翻译数据...")
    response1 = requests.post(f"{BASE_URL}/translate", json={
        "text": "黑暗降临大地",
        "source_language": "chinese"
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✓ 历史翻译: '{result1['source_text']}' → '{result1['translated_text']}'")
        translation_id = result1['translation_id']
        
        # 确认这个翻译
        confirm_response = requests.post(f"{BASE_URL}/translate/{translation_id}/confirm", json={
            "edited_text": result1['translated_text']
        })
        if confirm_response.status_code == 200:
            print("✓ 用户确认成功")
        
    else:
        print(f"✗ 创建历史数据失败: {response1.status_code}")
        return
    
    # 2. 创建第二个相似翻译，测试RAG效果
    print("\n2. 测试相似翻译RAG效果...")
    response2 = requests.post(f"{BASE_URL}/translate", json={
        "text": "黑暗降临世界",  # 与"黑暗降临大地"相似
        "source_language": "chinese"
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✓ 新翻译: '{result2['source_text']}' → '{result2['translated_text']}'")
        print(f"  置信度: {result2.get('confidence_score', 'N/A')}")
        
        # 比较两个翻译的相似性
        if result1['translated_text'] and result2['translated_text']:
            # 简单的相似性检查
            words1 = set(result1['translated_text'].lower().split())
            words2 = set(result2['translated_text'].lower().split())
            common = words1 & words2
            if common:
                print(f"✓ RAG效果: 发现共同词汇 {list(common)}")
            else:
                print("? RAG效果: 未发现明显的词汇重用")
    else:
        print(f"✗ 新翻译失败: {response2.status_code}")
        return
    
    # 3. 检查配额消耗
    print("\n3. 检查配额状态...")
    quota_response = requests.get(f"{BASE_URL}/session/quota")
    if quota_response.status_code == 200:
        quota = quota_response.json()
        print(f"✓ 剩余配额: {quota['tokens_remaining']}/500")
        print(f"  今日请求: {quota['total_requests_today']}")
    
    print("\n🎉 RAG功能测试完成！")
    print("注意: RAG功能在AI提示词中工作，通过相似翻译参考提升一致性")

if __name__ == "__main__":
    quick_rag_test()