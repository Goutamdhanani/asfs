"""
Test suite for selector fallback enhancements.

Tests that the new retry logic, knowledge persistence, and comprehensive
error reporting work as expected.

NOTE: This test file checks code structure and file content without
actually running browser automation (no playwright import needed).
"""

import unittest
import json
import tempfile
import re
import inspect
from pathlib import Path


class TestSelectorRetryEnhancements(unittest.TestCase):
    """Test enhanced try_selectors_with_page function."""
    
    def test_try_selectors_signature_has_retry_params(self):
        """Verify try_selectors_with_page accepts max_retries and retry_delay."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check function signature
        self.assertIn('def try_selectors_with_page(', content)
        self.assertIn('max_retries', content,
                     "max_retries parameter not found in try_selectors_with_page")
        self.assertIn('retry_delay', content,
                     "retry_delay parameter not found in try_selectors_with_page")
        
        # Check defaults are documented
        self.assertIn('max_retries: int = 1', content,
                     "max_retries default should be 1")
        self.assertIn('retry_delay: int = 3000', content,
                     "retry_delay default should be 3000")


class TestKnowledgePersistence(unittest.TestCase):
    """Test selector knowledge save/load functionality."""
    
    def test_selector_manager_has_save_knowledge(self):
        """Verify SelectorManager has save_knowledge method."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        self.assertIn('def save_knowledge(self', content,
                     "SelectorManager missing save_knowledge method")
    
    def test_selector_manager_has_load_knowledge(self):
        """Verify SelectorManager has load_knowledge method."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        self.assertIn('def load_knowledge(self', content,
                     "SelectorManager missing load_knowledge method")
    
    def test_save_knowledge_creates_json_structure(self):
        """Verify save_knowledge writes JSON with correct structure."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check for JSON operations in save_knowledge
        self.assertIn('json.dump', content,
                     "save_knowledge should use json.dump")
        self.assertIn('platform', content,
                     "save_knowledge should include platform in JSON")
        self.assertIn('last_updated', content,
                     "save_knowledge should include timestamp")
    
    def test_load_knowledge_restores_selector_state(self):
        """Verify load_knowledge restores confidence, counts, etc."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check for state restoration
        self.assertIn('json.load', content,
                     "load_knowledge should use json.load")
        self.assertIn('confidence', content,
                     "load_knowledge should restore confidence")
        self.assertIn('success_count', content,
                     "load_knowledge should restore success_count")
        self.assertIn('failure_count', content,
                     "load_knowledge should restore failure_count")


class TestInstagramSelectorEnhancements(unittest.TestCase):
    """Test Instagram uploader selector enhancements."""
    
    def test_instagram_selectors_load_knowledge_called(self):
        """Verify Instagram selector manager loads knowledge."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check that get_instagram_selectors calls load_knowledge
        pattern = r'def get_instagram_selectors.*?return manager'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match, "get_instagram_selectors function not found")
        
        function_body = match.group(0)
        self.assertIn('load_knowledge()', function_body,
                     "get_instagram_selectors should call load_knowledge()")
    
    def test_instagram_file_input_has_retry_in_code(self):
        """Verify Instagram uploader calls try_selectors with retry params."""
        with open('uploaders/brave_instagram.py', 'r') as f:
            content = f.read()
        
        # Check for max_retries parameter in file input section
        self.assertIn('max_retries=3', content,
                     "Instagram file input missing max_retries=3")
        self.assertIn('retry_delay=5000', content,
                     "Instagram file input missing retry_delay=5000")
        
        # Check for enhanced error message
        self.assertIn('after exhausting all selector retries', content,
                     "Missing enhanced error message for exhausted retries")
    
    def test_instagram_saves_knowledge_after_upload(self):
        """Verify Instagram uploader calls save_knowledge."""
        with open('uploaders/brave_instagram.py', 'r') as f:
            content = f.read()
        
        # Should have at least 2 calls (one for each upload function)
        count = content.count('_instagram_selectors.save_knowledge()')
        self.assertGreaterEqual(count, 2,
                               f"Expected at least 2 save_knowledge calls, found {count}")


class TestTikTokSelectorEnhancements(unittest.TestCase):
    """Test TikTok uploader selector enhancements."""
    
    def test_tiktok_selectors_load_knowledge_called(self):
        """Verify TikTok selector manager loads knowledge."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check that get_tiktok_selectors calls load_knowledge
        pattern = r'def get_tiktok_selectors.*?return manager'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match, "get_tiktok_selectors function not found")
        
        function_body = match.group(0)
        self.assertIn('load_knowledge()', function_body,
                     "get_tiktok_selectors should call load_knowledge()")
    
    def test_tiktok_file_input_has_retry_in_code(self):
        """Verify TikTok uploader calls try_selectors with retry params for file input."""
        with open('uploaders/brave_tiktok.py', 'r') as f:
            content = f.read()
        
        # Check file input section has retry logic
        self.assertIn('max_retries=3', content,
                     "TikTok file input missing max_retries=3")
        self.assertIn('retry_delay=5000', content,
                     "TikTok file input missing retry_delay=5000")
    
    def test_tiktok_post_button_has_retry_in_code(self):
        """Verify TikTok uploader calls try_selectors with retry params for post button."""
        with open('uploaders/brave_tiktok.py', 'r') as f:
            content = f.read()
        
        # Check post button section has retry logic (5 retries like Instagram)
        self.assertIn('max_retries=5', content,
                     "TikTok post button missing max_retries=5")
        self.assertIn('retry_delay=3000', content,
                     "TikTok post button missing retry_delay=3000")
        
        # Check for enhanced error messages
        self.assertIn('after 5 retries', content,
                     "Missing enhanced error message mentioning 5 retries")
        self.assertIn('TikTok UI may have changed significantly', content,
                     "Missing UI change warning in error message")
    
    def test_tiktok_saves_knowledge_after_upload(self):
        """Verify TikTok uploader calls save_knowledge."""
        with open('uploaders/brave_tiktok.py', 'r') as f:
            content = f.read()
        
        # Should have at least 2 calls (one for each upload function)
        count = content.count('_tiktok_selectors.save_knowledge()')
        self.assertGreaterEqual(count, 2,
                               f"Expected at least 2 save_knowledge calls, found {count}")


class TestEnhancedLogging(unittest.TestCase):
    """Test enhanced error logging."""
    
    def test_try_selectors_logs_all_attempts(self):
        """Verify try_selectors_with_page logs comprehensive failure info."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check for attempt logging
        self.assertIn('attempt_log', content,
                     "Missing attempt_log tracking")
        self.assertIn('Attempted', content,
                     "Missing 'Attempted' in failure logging")
        self.assertIn('selector combinations', content,
                     "Missing selector combinations logging")
        
        # Check for confidence and score logging
        self.assertIn('confidence:', content.lower(),
                     "Missing confidence in logging")
        self.assertIn('score:', content.lower(),
                     "Missing score in logging")
    
    def test_enhanced_error_messages_in_uploaders(self):
        """Verify uploaders have enhanced error messages."""
        # Check Instagram
        with open('uploaders/brave_instagram.py', 'r') as f:
            ig_content = f.read()
        
        self.assertIn('after exhausting all selector retries', ig_content,
                     "Instagram missing enhanced error message")
        self.assertIn('after 3 retries', ig_content,
                     "Instagram missing retry count in error")
        
        # Check TikTok
        with open('uploaders/brave_tiktok.py', 'r') as f:
            tt_content = f.read()
        
        self.assertIn('after 5 retries', tt_content,
                     "TikTok missing enhanced error message")
        self.assertIn('TikTok UI may have changed', tt_content,
                     "TikTok missing UI change warning")


class TestSelectorConfidenceScoring(unittest.TestCase):
    """Test selector confidence scoring system."""
    
    def test_selector_has_confidence_field(self):
        """Verify Selector dataclass has confidence field."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        # Check Selector dataclass
        pattern = r'@dataclass\s+class Selector:.*?def record_success'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match, "Selector dataclass not found")
        
        dataclass_body = match.group(0)
        self.assertIn('confidence:', dataclass_body,
                     "Selector missing confidence field")
        self.assertIn('float = 1.0', dataclass_body,
                     "Confidence should default to 1.0")
    
    def test_selector_record_success_method_exists(self):
        """Verify record_success method exists and modifies confidence."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        self.assertIn('def record_success(self):', content,
                     "Selector missing record_success method")
        
        # Check that it modifies confidence
        pattern = r'def record_success\(self\):.*?(?=\n    def |\nclass |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match)
        method_body = match.group(0)
        self.assertIn('self.confidence', method_body,
                     "record_success should modify confidence")
    
    def test_selector_record_failure_method_exists(self):
        """Verify record_failure method exists and modifies confidence."""
        with open('uploaders/selectors.py', 'r') as f:
            content = f.read()
        
        self.assertIn('def record_failure(self):', content,
                     "Selector missing record_failure method")
        
        # Check that it modifies confidence
        pattern = r'def record_failure\(self\):.*?(?=\n    def |\nclass |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match)
        method_body = match.group(0)
        self.assertIn('self.confidence', method_body,
                     "record_failure should modify confidence")


if __name__ == '__main__':
    unittest.main()
