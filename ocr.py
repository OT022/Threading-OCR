from array import array
import os
import sys
import json
import requests
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
from io import BytesIO
import csv
import logging
from pathlib import Path
import requests_helper
from PyPDF2 import PdfFileWriter, PdfFileReader

import sqlite3

def main():
    # Add your Computer Vision subscription key to your environment variables.
    if 'COMPUTER_VISION_KEY' in os.environ:
        subscription_key = os.environ['COMPUTER_VISION_KEY']
    else:
        print("\nSet the COMPUTER_VISION_KEY  environment variable.\n**Restart your shell or IDE for changes to take effect.**")
        sys.exit()
    # Add your Computer Vision endpoint to your environment variables.
    if 'COMPUTER_VISION_ENDPOINT' in os.environ:
        endpoint = os.environ['COMPUTER_VISION_ENDPOINT']
    else:
        print("\nSet the COMPUTER_VISION_ENDPOINT environment variable.\n**Restart your shell or IDE for changes to take effect.**")
        sys.exit()
    
    src_dir = 'src'
    out_dir = '_output'

    db_location = out_dir + "/ocr-results.db"

    conn = sqlite3.connect(db_location)
    db = conn.cursor()
    
    create_result_table_if_not_exists(db)
    create_error_table_if_not_exists(db)

    do_work(src_dir, out_dir,subscription_key, endpoint, db, conn)

    conn.close()
        
# def show_plot(image_path):
#     # Display the image and overlay it with the extracted text.
#     image = Image.open(image_path)
#     ax = plt.imshow(image)
#     for polygon in polygons:
#         vertices = [(polygon[0][i], polygon[0][i+1])
#                     for i in range(0, len(polygon[0]), 2)]
#         text = polygon[1]
#         patch = Polygon(vertices, closed=True, fill=False, linewidth=2, color='y')
#         ax.axes.add_patch(patch)
#         plt.text(vertices[0][0], vertices[0][1], text, fontsize=20, va="top")
#     plt.show()

def check_multi_page(input_pdf):
    """ checks to see if the pdf is multipaged returns true or false
    """
    is_multi_page: bool
    f = open(input_pdf, "rb")
    inputpdf = PdfFileReader(f)
    
    is_multi_page = inputpdf.numPages > 1

    f.close()

    return is_multi_page

def check_size_pdf(input_pdf):
    """
    - checks to see if pdf is over 50 mb
    """
    return input_pdf.stat().st_size >  49000000

def handle_multi_page(src_dir, input_pdf):
    print("input_pdf is multiple pages")
    pdf = PdfFileReader(open(input_pdf, "rb"))
    num_pages = pdf.numPages
    create_dir = "{}/{}".format(src_dir, input_pdf.stem)

    if not os.path.exists(create_dir):
        os.mkdir(create_dir)
        
    new_dir = Path(create_dir)
    if num_pages > 1:
        for i in range(num_pages):
            output = PdfFileWriter()
            output.addPage(pdf.getPage(i))
            with open("{}/{}-{}.pdf".format(new_dir, input_pdf.stem,  str(i+1).zfill(3)), "wb") as outputStream:
                output.write(outputStream)

    return new_dir

def post_and_request(f, out, url, headers):
    # get name without file extensions
    kvp = []
    kvp.append(f.stem)
    page_text = ""
    post_response = requests_helper.post_image(url=url, headers=headers, image=open(f, 'rb'))

    if post_response["status_code"] == 202:
        
        result = {}
        poll = True
        while poll:
            get_response = requests_helper.get_read_result(url=post_response["response"].headers["Operation-Location"], headers=headers)

            if get_response["status_code"] == 200:
                json_response = get_response["response"].json()

                if json_response["status"] == "notStarted":
                    print("sleep 1s- notStarted")
                    time.sleep(0.5)
                if json_response["status"] == "running":
                    print("sleep 1s- running")
                    time.sleep(0.5)
                elif json_response["status"] == "succeeded":
                    print("{} succeeded".format(f.stem))

                    text = []
                    if ("analyzeResult" in json_response):
                        text = json_response["analyzeResult"]["readResults"][0]["lines"]
                        
                    # change this to a string, rather than a file
                    # add it as a row value to our output .csv
                    for line in text:
                        page_text += " " + line["text"] + "\n"

                    kvp.append(page_text)

                    poll = False
                else:
                    kvp.append("No Text Found")
                    poll = False
                    

            elif get_response["status_code"] == 429:
                print("sleep 10s - 429")
                time.sleep(10)
            else:
                kvp.append("No Text Found")
                raise Exception("status code was wrong?")
    else:
        kvp.append("ocring failed")
        raise Exception("status code was wrong?")
    
    return kvp


def do_work(src_dir, out_dir, subscription_key, endpoint, db, conn):

    src = Path(src_dir)
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())

    out = open('{}/{}.csv'.format(out_dir, timestamp), "w", encoding="utf-8")
    # add column headers to .csv
    out.write("Control Number {} Extracted Text\n".format(chr(166)))

    url = endpoint + "/vision/v3.0/read/analyze"

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'application/octet-stream'
    }    

    logging.basicConfig(filename='{}/{}.log'.format(out_dir,timestamp), level=logging.INFO)

    for f in src.iterdir():

        try:
            # only make call iff a supported type (suffix) -> .png, .jpg/jpeg, .pdf, .tiff
            # keep a record in log if not

            suffix = f.suffix.lower()

            if suffix not in [".png", ".jpg", ".jpeg", ".pdf", ".bmp", ".tiff"]:
                logging.warning("%s:UnsupportedFileType:%s", f.stem, f.suffix)
                continue
            
            if does_record_already_exist(db, conn, f.stem):
                print("already exists")
                continue

            if (suffix == ".pdf" and check_multi_page(f)) and check_size_pdf(f):
                new_dir = handle_multi_page(src_dir, f)
                text_pages = []
                for page in new_dir.iterdir():
                    text_pages.append(post_and_request(page, out, url, headers))

                multi_page_str = ""

                out.write("{} {} ".format(f.stem, chr(166))) # using ¦ as a delimiter for the .csv - works with RDC
                count = 1
                for text in text_pages:
                    out.write(text[1])
                    multi_page_str += text[1] + "\n ----------------- page {} -----------------\n".format(count)
                    count += 1
                    
                insert_result(db, conn, f.stem, multi_page_str)
                out.write("\n")

                os.rmdir(new_dir)

            else:
                kvp = post_and_request(f, out, url, headers)
                insert_result(db, conn, kvp[0], kvp[1])

                out.write("{} {} {}\n".format(kvp[0], chr(166), kvp[1]))
        except Exception as e:          
            insert_error(db, conn, f.stem, str(e))
            continue

    out.close()

def create_result_table_if_not_exists(db: sqlite3.Cursor):
    # create result table
    db.execute('''CREATE TABLE IF NOT EXISTS results (
        control_number text PRIMARY KEY,
        azure_extracted_text text
        )''')

def insert_result(db: sqlite3.Cursor, conn: sqlite3.Connection, control_number, azure_extracted_text):
    db.execute('INSERT INTO results VALUES (?,?)', (control_number, azure_extracted_text))
    conn.commit()

def create_error_table_if_not_exists(db: sqlite3.Cursor):
    # create result table
    db.execute('''CREATE TABLE IF NOT EXISTS errors (
        row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        control_number TEXT,
        message TEXT
        )''')
    
def insert_error(db: sqlite3.Cursor, conn: sqlite3.Connection, control_number, message):
    db.execute('INSERT INTO errors VALUES (?,?,?)', (None,control_number, message))
    conn.commit()

def does_record_already_exist(db: sqlite3.Cursor, conn: sqlite3.Connection, control_number):
    query = db.execute('SELECT * FROM results WHERE control_number=?', (str(control_number),))

    result = query.fetchone()

    if result is None:
        return False

    return True


if __name__ == "__main__":
    main()