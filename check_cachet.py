#!/usr/bin/env python3

import bs4
import sys
import argparse
import requests

STATUS_OK = 0
STATUS_WARN = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3


class CheckCachet():
    class_components = ["list-group-item", "sub-component"]

    status_code = {
            "status-1": STATUS_OK,
            "greens": STATUS_OK,
            "status-2": STATUS_WARN,  # performances issues
            "yellows": STATUS_WARN,
            "blues": STATUS_WARN,
            "status-3": STATUS_WARN,  # Partial outage
            "status-4": STATUS_CRITICAL,
            "status-5": STATUS_CRITICAL,
            "reds": STATUS_CRITICAL,
            }

    def __init__(self, url):
        self.url = url
        self.status_list = list(self.status_code.keys())

    def probe(self):
        data = requests.get(self.url, timeout=10)
        if int(data.status_code) != 200:
            return (STATUS_UNKNOWN, f'Unable to request url "{self.url}"')

        html = bs4.BeautifulSoup(data.text, features="lxml")
        items_list = html.find_all('li')
        return_items = []
        for item in items_list:
            # print("item:", item)
            item_classes = item.get('class')
            if not item_classes:
                continue
            if len(list(set(self.class_components) & set(item_classes))) != 2:
                continue

            small = item.small.extract()
            small_classes = small.get('class')
            item_text = item.get_text().strip()
            item_status = small.get_text().strip()
            # print("item_classes", small_classes)
            class_status = list(set(self.status_list) & set(small_classes))
            if len(class_status) != 1:
                print("multiple status class found ! Keeping first one")
            # print("class status:", class_status)
            class_status = class_status[0]
            class_statuscode = self.status_code[class_status]

            if class_statuscode != STATUS_OK:
                item_text = f"{item_text}: {item_status}"

            return_items.append((class_statuscode, item_text),)

        return return_items


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type=str,
                        help="URL to the cachet instance", required=True)
    parser.add_argument('-w', '--warning', default=0, type=int)
    parser.add_argument('-c', '--critical', default=0, type=int)
    args = parser.parse_args()

    url = args.url
    if url[:4] != 'http':
        url = 'https://' + url

    check = CheckCachet(url)
    items = check.probe()

    if not items:
        items.append((STATUS_UNKNOWN, 'Unable to parse "' + url + '".'),)

    return_code = max([x[0] for x in items])

    items_ok = [x[1] for x in items if x[0] == STATUS_OK]
    items_warn = [x[1] for x in items if x[0] == STATUS_WARN]
    items_critical = [x[1] for x in items if x[0] == STATUS_CRITICAL]
    items_unknown = [x[1] for x in items if x[0] == STATUS_UNKNOWN]

    result_string = []
    if items_unknown:
        result_string.append("UNKNOWN: " + ", ".join(items_unknown))
    if items_critical:
        result_string.append("CRITICAL: " + ", ".join(items_critical))
    if items_warn:
        result_string.append("WARNING: " + ", ".join(items_warn))
    if items_ok:
        result_string.append("OK: " + ", ".join(items_ok))

    print("\n".join(result_string))
    sys.exit(return_code)


if __name__ == "__main__":
    run()
