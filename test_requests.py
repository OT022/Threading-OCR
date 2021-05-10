import pytest
import os
import logging
import requests_helper

@pytest.fixture
def valid_post_image():
    return open('_test/src/img001.jpg', 'rb')

@pytest.fixture
def valid_post_url():
    return os.environ['COMPUTER_VISION_ENDPOINT'] + "/vision/v3.0/read/analyze"
    
@pytest.fixture
def valid_headers():
    return {
        'Ocp-Apim-Subscription-Key': os.environ['COMPUTER_VISION_KEY'],
        'Content-Type': 'application/octet-stream'
    }

@pytest.fixture
def valid_get_url():
    return "operation-location"

class MockResponse:
    def __init__(self, json_data, status_code, headers):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers

    def json(self):
        return self.json_data

def test_post_response_is_ok(mocker, valid_post_url, valid_headers, valid_post_image):
    
    mock_post = mocker.patch('requests_helper.requests.post')
    mock_post.return_value = MockResponse(None, 202, { "Operation-Location": "a-valid-url" })
    response = requests_helper.post_image(valid_post_url, valid_headers, valid_post_image)

    assert(response.headers["Operation-Location"]) == "a-valid-url"


def test_post_response_handles_500_error(mocker, valid_post_url, valid_headers, valid_post_image):
    mock_post = mocker.patch('requests_helper.requests.post')
    mock_post.return_value = MockResponse({"error": {"code": "FailedToProcess", "message": "The analyze request could not be started due to a cluster-related issue. Please resubmit the document for processing."}}, 500, {})
    
    response = requests_helper.post_image(valid_post_url, valid_headers, valid_post_image)

    assert response == { "status_code": 500, "code": "FailedToProcess", "message": "The analyze request could not be started due to a cluster-related issue. Please resubmit the document for processing."}

def test_get_read_result_is_ok(mocker, valid_headers):

    mock_get = mocker.patch('requests_helper.requests.get')
    mock_get.return_value = MockResponse( {"analyzeResult": { "lines": [{"text": "this is text"}]}}, 200, {})

    response = requests_helper.get_read_result(valid_get_url, valid_headers)

    assert response.json()["analyzeResult"] is not None

def test_get_read_result_handles_error(mocker, valid_headers, valid_get_url):
    mock_get = mocker.patch('requests_helper.requests.get')
    mock_get.return_value = MockResponse({"error": { "code": "fail", "message": "because"}}, 500, {})

    response = requests_helper.get_read_result(valid_get_url, valid_headers)

    assert response["code"] == "fail"