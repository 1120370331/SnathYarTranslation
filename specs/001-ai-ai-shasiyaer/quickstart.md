# Quickstart Guide: Shathyar Translation Application

**Version**: 1.0.1
**Date**: 2025-09-11
**Purpose**: End-to-end validation of core translation workflows

## Overview

This quickstart guide validates the complete Shathyar translation application through realistic user scenarios. Each scenario exercises specific functional requirements and can be used for both manual testing and automated integration tests.

## Prerequisites

- Backend API running on `http://localhost:8000`
- Frontend application running on `http://localhost:3000`
- Official dictionary (`shasiyaer.csv`) loaded in database
- AI service integration configured with valid API key

## Core User Workflows

### Workflow 1: Chinese to Shathyar Translation (FR-001, FR-005)

**Scenario**: A World of Warcraft fan wants to translate Chinese text to Shathyar for roleplaying.

**Steps**:
1. **Open Application**
   - Navigate to `http://localhost:3000`
   - Verify mystical UI theme is applied (dark background, mystical colors)
   - Check that "魔力值" (magic power) indicator shows 500/500

2. **Select Translation Mode**
   - Select "中文" (Chinese) from language dropdown
   - Input field should show placeholder: "输入中文文本..."

3. **Enter Test Text**
   - Input: `虚空的力量召唤着我们`
   - Verify character counter shows "12/500"
   - Verify input validation (no error messages)

4. **Execute Translation**
   - Click translate button (should show mystical loading animation)
   - Wait for AI response (typically 2-5 seconds)
   - Verify translation appears in output area

5. **Validate Results**
   - Check translation contains Shathyar-style text
   - Verify "魔力值" decreased by 1 (now shows 499/500)
   - Confirm "复制" (copy) button is available
   - Verify edit functionality is enabled for AI-generated translations

**Expected API Calls**:
```
POST /api/v1/translate
{
  "text": "虚空的力量召唤着我们",
  "source_language": "chinese"
}

Response: 200 OK
{
  "translated_text": "Vash'jir kul'thrak mor'dun vel",
  "source_text": "虚空的力量召唤着我们",
  "is_cached": false,
  "is_ai_generated": true,
  "can_edit": true,
  "magic_power_remaining": 499,
  "confidence_score": 0.89,
  "translation_id": "uuid-here"
}
```

### Workflow 2: Shathyar to Chinese Translation (FR-004, FR-009)

**Scenario**: User wants to decode an existing Shathyar phrase from the game.

**Steps**:
1. **Switch Translation Direction**
   - Select "沙斯亚尔语" (Shathyar) from language dropdown
   - Input field should show placeholder: "输入沙斯亚尔语文本..."

2. **Enter Official Dictionary Text**
   - Input: `Mor'dun kul'thrak` (assuming this exists in shasiyaer.csv)
   - Verify input accepts Shathyar character patterns

3. **Execute Translation**
   - Click translate button
   - Should return quickly (dictionary lookup, no AI call)
   - Verify translation appears immediately

4. **Validate Dictionary Match**
   - Check translation matches expected Chinese meaning
   - Verify "魔力值" does NOT decrease (dictionary lookup is free)
   - Confirm edit functionality is disabled (authoritative source)

**Expected API Calls**:
```
POST /api/v1/translate
{
  "text": "Mor'dun kul'thrak",
  "source_language": "shathyar"
}

Response: 200 OK
{
  "translated_text": "黑暗力量",
  "source_text": "Mor'dun kul'thrak", 
  "is_cached": true,
  "is_ai_generated": false,
  "can_edit": false,
  "magic_power_remaining": 499
}
```

### Workflow 3: Translation Not Found (FR-009)

**Scenario**: User tries to translate unknown Shathyar text.

**Steps**:
1. **Enter Unknown Shathyar Text**
   - Input: `Zyx'qwerty unknown` (text not in dictionary)
   - Click translate button

2. **Validate Error Response**
   - Should display: "破译失败..." 
   - Verify mystical error styling
   - Confirm "魔力值" remains unchanged
   - Check that user can try different input

**Expected API Response**:
```
Response: 404 Not Found
{
  "error": "dictionary_entry_not_found",
  "message": "破译失败...",
  "details": "No matching entries found in official dictionary"
}
```

### Workflow 4: Edit AI Translation (FR-006, FR-007, FR-008)

**Scenario**: User wants to refine an AI-generated translation.

**Steps**:
1. **Generate AI Translation**
   - Use Workflow 1 to get an AI-generated Shathyar translation
   - Note the `translation_id` from response

2. **Edit Translation**
   - Click edit button on translation result
   - Modify the Shathyar text (e.g., add/remove words)
   - Original: `Vash'jir kul'thrak mor'dun vel`
   - Edited: `Vash'jir kul'thrak mor'dun vel'koz`

3. **Confirm Changes**
   - Click "确认" (confirm) button
   - Should show success message: "翻译已保存至古老典籍中"
   - Verify copy button functionality

4. **Validate Persistence**
   - Repeat the same Chinese input
   - Should now return the edited version from database cache
   - Verify `is_cached: true` and edit functionality disabled

**Expected API Calls**:
```
POST /api/v1/translate/uuid-here/confirm
{
  "edited_text": "Vash'jir kul'thrak mor'dun vel'koz"
}

Response: 200 OK
{
  "success": true,
  "copy_text": "Vash'jir kul'thrak mor'dun vel'koz",
  "message": "翻译已保存至古老典籍中"
}
```

### Workflow 5: Rate Limiting (FR-010, FR-011)

**Scenario**: User approaches and exceeds daily translation limit.

**Steps**:
1. **Check Initial Quota**
   - Open browser developer tools, check network tab
   - Should see quota calls showing 500/500 magic power

2. **Simulate High Usage**
   - For testing: temporarily set daily limit to 3 translations
   - Perform 3 Chinese→Shathyar translations
   - Watch "魔力值" decrease: 500→499→498→497

3. **Hit Rate Limit**
   - Attempt 4th translation
   - Should receive error: "魔力耗尽！今日翻译次数已达上限。"
   - Verify translation button is disabled
   - Check quota display shows 0/500

4. **Validate Reset Time**
   - Error message should include reset time
   - UI should show countdown to next day reset

**Expected API Response**:
```
Response: 429 Too Many Requests
{
  "error": "rate_limit_exceeded", 
  "message": "魔力耗尽！今日翻译次数已达上限。",
  "details": "Daily limit of 500 translations exceeded",
  "magic_power_remaining": 0,
  "reset_time": "2025-09-12T00:00:00Z"
}
```

### Workflow 6: Input Validation (FR-012)

**Scenario**: User tries to submit invalid input.

**Steps**:
1. **Test Empty Input**
   - Leave input field empty
   - Click translate
   - Should show client-side validation error

2. **Test Oversized Input**
   - Enter 501+ characters of text
   - Should prevent submission with message about character limit
   - Character counter should show red when >500

3. **Test Invalid Characters** (optional)
   - For Shathyar input, test with clearly non-Shathyar characters
   - Should either warn user or handle gracefully

**Expected Client-Side Validation**:
- Input field should prevent submission of invalid data
- Clear error messages in mystical theme
- Character counter updates in real-time

## Performance Benchmarks

### Response Time Expectations
- **Dictionary lookup**: <100ms (95th percentile)
- **Cached translation**: <200ms (95th percentile) 
- **AI translation**: <5000ms (95th percentile)
- **Rate limit check**: <50ms (95th percentile)

### Concurrent User Testing
- **Simultaneous users**: Support 10+ concurrent translation requests
- **Database performance**: <1s response time with 100+ concurrent sessions
- **UI responsiveness**: No blocking operations in frontend

## Error Scenarios Testing

### Network Issues
1. **Offline Behavior**
   - Disconnect internet
   - Attempt translation
   - Should show appropriate offline message

2. **API Timeout**
   - Simulate slow AI service response (>30s)
   - Should show timeout error with retry option

### Service Degradation
1. **AI Service Unavailable**
   - Mock AI API to return 503 errors
   - Should gracefully degrade to cached/dictionary lookups
   - Display: "翻译法阵暂时失效，请稍后重试。"

2. **Database Issues**
   - Simulate database connection issues
   - Should display appropriate error messages
   - Maintain basic functionality where possible

## Security Validation

### Input Sanitization
- Test XSS attempts in translation input
- Verify HTML/script tags are properly escaped
- Confirm no code injection possible

### Rate Limit Bypass Attempts  
- Test multiple IP addresses (if available)
- Attempt header spoofing (X-Forwarded-For)
- Verify server-side enforcement

## Acceptance Criteria

**✅ Pass Conditions**:
- All 6 core workflows complete successfully
- Performance benchmarks met
- Error scenarios handled gracefully
- Security tests pass
- UI maintains mystical theme throughout

**❌ Fail Conditions**:
- Any workflow step fails unexpectedly
- Performance degradation beyond acceptable limits
- Security vulnerabilities discovered
- User experience breaks mystical immersion

## Automated Testing Integration

This quickstart can be automated using:

**Backend Integration Tests** (pytest):
```python
def test_quickstart_workflow_1_chinese_to_shathyar():
    # Implement API calls from Workflow 1
    response = client.post("/api/v1/translate", json={
        "text": "虚空的力量召唤着我们",
        "source_language": "chinese"
    })
    assert response.status_code == 200
    assert response.json()["is_ai_generated"] is True
```

**Frontend E2E Tests** (Playwright/Cypress):
```javascript
test('Quickstart Workflow 1: Chinese to Shathyar', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.selectOption('[data-testid=language-select]', 'chinese');
  await page.fill('[data-testid=input-text]', '虚空的力量召唤着我们');
  await page.click('[data-testid=translate-button]');
  await expect(page.locator('[data-testid=translation-result]')).toBeVisible();
});
```

This quickstart guide ensures comprehensive validation of the Shathyar translation application's core functionality, performance, and user experience requirements.