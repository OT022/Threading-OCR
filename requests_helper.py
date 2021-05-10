import requests
import logging

def post_image(url:str, headers:dict, image:bytes):
    # POST read request
    # see https://westcentralus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-1-ga/operations/5d986960601faab4bf452005
    response = requests.post(
        url=url, headers=headers, data=image
    )

    if response.status_code == 202:
        return { "response": response, "status_code": response.status_code }
    else:
        json_data = response.json()

        return { "status_code": response.status_code, "code": json_data['error']['code'], "message": json_data['error']['message'] }


def get_read_result(url:str, headers:dict):
    # GET read request
    # see https://westcentralus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-1-ga/operations/5d9869604be85dee480c8750
    response = requests.get(
        url=url, headers=headers
    )

    if response.status_code == 200 or response.status_code == 429:
        return { "response": response, "status_code": response.status_code }
    else:
        json_data = response.json()

        return { "status_code": response.status_code, "code": json_data['error']['code'], "message": json_data['error']['message'] }