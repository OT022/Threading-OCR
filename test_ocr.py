import ocr
import pytest
import requests_helper
from os import path
from pathlib import Path

def test_check_multipage_function_returns_true_when_pdf_is_multiple_page():
    is_multi_page = ocr.check_multi_page(Path('_test/src/redact-test-doc.pdf'))
    assert is_multi_page

def test_check_multi_page_returns_false_when_pdf_is_not_multiple_page():
    is_multi_page = ocr.check_multi_page(Path("_test/src/img003.pdf"))
    assert is_multi_page == False

def test_multiple_page_pdfs_creates_dir_if_not_exists():
    ocr.handle_multi_page("_test/src", Path("_test/src/redact-test-doc.pdf"))
    assert path.exists("_test/src/redact-test-doc/redact-test-doc-001.pdf")

def test_multiple_page_pdfs_replaces_files_in_dir_if_exists():
    ocr.handle_multi_page("_test/src", Path("_test/src/redact-test-doc.pdf"))
    assert path.exists("_test/src/redact-test-doc/redact-test-doc-001.pdf") and path.exists("_test/src/redact-test-doc/redact-test-doc-002.pdf") and path.exists("_test/src/redact-test-doc/redact-test-doc-003.pdf")

def test_multiple_page_pdf_suffix_is_left_padded_for_page_ordering():
    ocr.handle_multi_page("_test/src", Path("_test/src/redact-test-doc.pdf"))
    assert path.exists("_test/src/redact-test-doc/redact-test-doc-002.pdf")