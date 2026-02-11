# Selector Fallback Enhancement Implementation Summary

## Problem Statement

Automated uploads to TikTok and Instagram were failing when primary selectors timed out. The logs revealed:
- Code tried only primary selector and one alternate, then failed
- No structured fallback or confidence ranking
- No logging of which selectors were successful historically
- No retry loop or stateful/knowledge-driven fallback

## Solution Implemented

### 1. Enhanced Retry Logic (`uploaders/selectors.py`)

**Before:**
```python
def try_selectors_with_page(page, selector_group, timeout=10000, state="visible"):
    # Single pass through selectors - no retry
    for selector in ranked_selectors:
        try:
            element = page.wait_for_selector(selector.value, timeout=timeout)
            if element:
                return selector.value, element
        except Exception:
            continue
    return None, None  # Fails immediately if all selectors timeout
```

**After:**
```python
def try_selectors_with_page(
    page, 
    selector_group, 
    timeout=10000, 
    state="visible",
    max_retries=1,      # NEW: Configurable retry attempts
    retry_delay=3000    # NEW: Configurable delay between retries
):
    attempt_log = []  # NEW: Track all attempts for error reporting
    
    for retry in range(max_retries):  # NEW: Retry loop
        if retry > 0:
            page.wait_for_timeout(retry_delay)  # NEW: Wait between retries
        
        for selector in ranked_selectors:
            try:
                element = page.wait_for_selector(selector.value, timeout=timeout)
                if element:
                    # NEW: Comprehensive success logging
                    logger.info(f"✓ Selector succeeded: {selector.value} "
                               f"(confidence: {selector.confidence:.2f}, attempt: {retry + 1})")
                    selector_group.record_success(selector.value)
                    return selector.value, element
            except Exception as e:
                # NEW: Track failed attempts
                attempt_log.append({
                    "selector": selector.value,
                    "result": "timeout",
                    "confidence": selector.confidence,
                    "attempt": retry + 1
                })
                selector_group.record_failure(selector.value)
    
    # NEW: Comprehensive failure logging
    logger.error(f"All selectors failed after {max_retries} attempts:")
    for i, attempt in enumerate(attempt_log, 1):
        logger.error(f"  {i}. {attempt['selector']} - {attempt['result']} "
                    f"(confidence: {attempt['confidence']:.2f})")
    
    return None, None
```

### 2. Knowledge Persistence (`uploaders/selectors.py`)

**New Features:**
- `SelectorManager.save_knowledge()` - Saves selector success/failure history to JSON
- `SelectorManager.load_knowledge()` - Loads previous knowledge to prioritize working selectors
- Knowledge files: `knowledge/instagram_selectors.json`, `knowledge/tiktok_selectors.json`

**Knowledge File Structure:**
```json
{
  "platform": "tiktok",
  "last_updated": "2026-02-11T05:30:00",
  "groups": {
    "post_button": {
      "description": "Post/Submit button",
      "selectors": [
        {
          "value": "button[data-e2e=\"post_video_button\"]",
          "priority": 1,
          "confidence": 1.0,
          "success_count": 5,
          "failure_count": 0,
          "last_used": "2026-02-11T05:29:45"
        }
      ]
    }
  }
}
```

### 3. Instagram Uploader Improvements (`uploaders/brave_instagram.py`)

**File Input Enhancement:**
```python
# Before: Single attempt, immediate failure
selector_value, file_input = try_selectors_with_page(
    page, file_input_group, timeout=15000, state="attached"
)
if not file_input:
    raise Exception("File input not found")

# After: 3 total attempts with 5s delays
selector_value, file_input = try_selectors_with_page(
    page,
    file_input_group,
    timeout=15000,
    state="attached",
    max_retries=3,      # 3 total attempts (1 initial + 2 retries)
    retry_delay=5000    # Wait 5s between attempts
)
if not file_input:
    logger.error("Failed to find file input after 3 retries")
    logger.error("This indicates Instagram UI may have changed significantly")
    raise Exception("File input not found after exhausting all selector retries")
```

**Knowledge Persistence:**
```python
# After successful upload
_instagram_selectors.save_knowledge()  # NEW: Save learned selector performance
```

### 4. TikTok Uploader Improvements (`uploaders/brave_tiktok.py`)

**File Input Enhancement:**
```python
# After: 3 total attempts with 5s delays
selector_value, file_input = try_selectors_with_page(
    page,
    file_input_group,
    timeout=30000,
    state="attached",
    max_retries=3,      # 3 total attempts
    retry_delay=5000    # Wait 5s between attempts
)
```

**Post Button Enhancement (Most Critical Fix):**
```python
# Before: Single attempt, no retry
selector_value, post_button = try_selectors_with_page(
    page, post_button_group, timeout=30000, state="visible"
)
if not post_button:
    raise Exception("TikTok Post button not found")

# After: 5 total attempts with 3s delays
selector_value, post_button = try_selectors_with_page(
    page,
    post_button_group,
    timeout=30000,
    state="visible",
    max_retries=5,      # 5 total attempts (1 initial + 4 retries) for extra resilience
    retry_delay=3000    # Wait 3s between attempts
)
if not post_button:
    logger.error("Post button not found with any selector after 5 retries")
    logger.error("This indicates TikTok UI may have changed significantly")
    raise Exception("TikTok Post button not found after exhausting all selector retries")
```

**Knowledge Persistence:**
```python
# After successful upload
_tiktok_selectors.save_knowledge()  # NEW: Save learned selector performance
```

## Testing

Created comprehensive test suite (`test_selector_fallback_enhancements.py`) with 17 tests:

**Test Coverage:**
- ✅ Retry logic with max_retries and retry_delay parameters
- ✅ Knowledge persistence (save/load methods)
- ✅ Instagram uses retry logic correctly (3 attempts for file input)
- ✅ TikTok uses retry logic correctly (3 attempts for file input, 5 for post button)
- ✅ Enhanced error logging with all attempts enumerated
- ✅ Selector confidence scoring system

**All tests passing:**
```
Ran 17 tests in 0.003s
OK
```

## Benefits

### 1. Self-Healing
- System learns which selectors work over time
- Most recently successful selectors are tried first
- Confidence scores adjust based on success/failure history

### 2. Resilient
- Up to 5 retry attempts for critical actions (TikTok post button)
- Configurable delays between retries prevent race conditions
- Comprehensive fallback strategy tries all viable selectors

### 3. Debuggable
- Every selector attempt is logged with:
  - Selector value
  - Confidence score
  - Attempt number
  - Success/failure result
- Final error messages enumerate ALL attempted selectors

### 4. Maintainable
- Knowledge persists across runs in JSON files
- Easy to add new selectors to existing groups
- Clear separation of concerns (selectors.py vs. uploaders)

## Example Log Output

**Success Case:**
```
DEBUG: Trying selector: file_input - input[type="file"] (score: 0.85, confidence: 0.95, priority: 3, attempt: 1/3)
INFO: ✓ Selector succeeded: file_input - input[type="file"] (confidence: 0.95, attempt: 1/3)
INFO: Saved selector knowledge to /knowledge/tiktok_selectors.json
```

**Failure Case with Retry:**
```
DEBUG: Trying selector: post_button - button[data-e2e="post_video_button"] (score: 1.0, confidence: 1.0, priority: 1, attempt: 1/5)
DEBUG: ✗ Selector timeout: button[data-e2e="post_video_button"] (confidence: 1.0)
DEBUG: Trying selector: post_button - [data-e2e="post-button"] (score: 0.9, confidence: 0.9, priority: 1, attempt: 1/5)
DEBUG: ✗ Selector timeout: [data-e2e="post-button"] (confidence: 0.9)
INFO: Retrying selector group 'post_button' (attempt 2/5)
... (attempts 3, 4, 5)
ERROR: All selectors failed for: post_button after 5 attempts
ERROR: Attempted 25 selector combinations:
ERROR:   1. button[data-e2e="post_video_button"] - timeout (confidence: 0.80, score: 0.85, attempt: 1)
ERROR:   2. [data-e2e="post-button"] - timeout (confidence: 0.70, score: 0.75, attempt: 1)
...
ERROR: Post button not found with any selector after 5 retries
ERROR: This indicates TikTok UI may have changed significantly
```

## Migration Notes

### Backward Compatibility
- Default `max_retries=1` means single attempt (no change from previous behavior)
- Existing code continues to work without modifications
- Enhanced features opt-in via parameters

### Breaking Changes
- None - all changes are additive

### Performance Impact
- Minimal: Only retries on failure
- Configurable delays prevent unnecessary waiting
- Knowledge files are small (<10KB)

## Files Modified

1. `uploaders/selectors.py` - Core selector system enhancements
2. `uploaders/brave_instagram.py` - Instagram uploader improvements
3. `uploaders/brave_tiktok.py` - TikTok uploader improvements
4. `test_selector_fallback_enhancements.py` - Comprehensive test suite (NEW)

## Acceptance Criteria Met

✅ When UI changes and primary selector fails, alternate selectors are tried automatically (with confidence/recency order)
✅ Full info is logged about what was tried and why
✅ Next pipeline run remembers working selectors
✅ Fails only after all confidence-ranked selectors are attempted, providing comprehensive failure feedback

## Next Steps

1. Monitor production logs for knowledge file accumulation
2. Review knowledge files periodically to identify UI patterns
3. Add new selectors based on learned patterns
4. Consider expanding retry logic to other uploaders (YouTube, Facebook, etc.)
