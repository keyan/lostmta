from typing import List

import json
import socketserver
import urllib.request
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler

URL = 'http://advisory.mtanyct.info/LPUWebServices/CurrentLostProperty.aspx'
CATEGORY_ATTRIB = 'Category'
SUBCATEGORY_ATTRIB = 'SubCategory'
COUNT_ATTRIB = 'count'

CATEGORY_SWAPS = {
    "Cell Phone/Telephone/Communication Device": "Communication Device",
    "Entertainment (Music/Movies/Games)": "Entertainment",
    "Carry Bag / Luggage": "Luggage",
}


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """
    A wrapper around SimpleHTTPRequestHandler that provides CORS support.
    """
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


def fetch_xml_text() -> str:
    req = urllib.request.Request(URL, method='GET')
    resp = urllib.request.urlopen(req)
    if resp.code != 200:
        print(f'Request failed - code: {resp.code}')

    return resp.readline()


def convert_xml_to_csv(xml_text: str) -> None:
    root = ET.fromstring(xml_text)
    freqs = open('frequencies.csv', 'w')

    for child in root:
        if child.tag != CATEGORY_ATTRIB:
            continue

        category = child.attrib[CATEGORY_ATTRIB]
        for sub in child:
            sub_name = sub.attrib[SUBCATEGORY_ATTRIB].replace('-', '')
            count = sub.attrib[COUNT_ATTRIB]
            freqs.write(f'{category}-{sub_name},{count}\n')

    freqs.close()


def convert_xml_to_json(xml_text: str) -> None:
    root = ET.fromstring(xml_text)

    content = {'name': 'flare', 'children': []}
    for child in root:
        if child.tag != CATEGORY_ATTRIB:
            continue

        category = child.attrib[CATEGORY_ATTRIB]
        category_name = CATEGORY_SWAPS.get(category, category).strip()
        category_node = {'name': category_name, 'children': []}
        for sub in child:
            sub_name = sub.attrib[SUBCATEGORY_ATTRIB]
            count = int(sub.attrib[COUNT_ATTRIB])
            category_node['children'].append({'name': sub_name, 'value': count})
        content['children'].append(category_node)

    with open('flare.json', 'w') as f:
        json.dump(content, f)


def serve_files():
    PORT = 8000
    handler = CORSRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("serving at port", PORT)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()


if __name__ == '__main__':
    txt = fetch_xml_text()
    convert_xml_to_csv(txt)
    convert_xml_to_json(txt)
    # serve_files()
