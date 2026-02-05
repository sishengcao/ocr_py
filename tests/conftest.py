"""
Pytest configuration and fixtures for OCR service tests.

This module sets up necessary mocks for tests that require torch/transformers.
"""

import sys
from unittest.mock import MagicMock
import pytest


# Mock torch and transformers at module level for all tests
# This allows tests to run without requiring actual torch installation
sys.modules['torch'] = MagicMock()
sys.modules['torch.cuda'] = MagicMock()
sys.modules['torch.backends'] = MagicMock()
sys.modules['transformers'] = MagicMock()

# Configure torch mocks
torch_mock = sys.modules['torch']
torch_mock.cuda.is_available.return_value = False
torch_mock.backends.mps.is_available.return_value = False
torch_mock.float16 = 'float16'
torch_mock.bfloat16 = 'bfloat16'
