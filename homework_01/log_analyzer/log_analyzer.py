#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import os
import glob
import gzip
import re
import json
import argparse
import sys
# from datetime import date


LOG_DATE = re.compile(r'nginx-access-ui.log-(?P<full_date>(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}))')
URL_RT = re.compile(r'\"\w+ (?P<url>(.*?)) HTTP.* (?P<rt>[0-9.]+)$')
MARKER = '$table_json'

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "TEMPLATE": "./report.html",
    "DIGITS": 3
}


def get_last_log_file():
    list_of_files = glob.glob(os.path.join(config['LOG_DIR'], '*'))
    list_of_logs_filtered = (el for el in list_of_files if LOG_DATE.search(el))
    list_of_logs = ((LOG_DATE.search(el).group('full_date'), el)
                    for el in list_of_logs_filtered)
    try:
        last = max(list_of_logs, key=lambda x: x[0])
        return last[1]
    except ValueError:
        return None


# def get_open_func(filename):
#     _, ext = os.path.splitext(filename)
#     if ext == '.gz':
#         return gzip.open
#     else:
#         return open

def get_open_func(filename):
    opener = gzip.open if filename.endswith('.gz') else open
    log_file = opener(filename, "rt")
    for line in log_file:
        yield line
    log_file.close()


def get_url_rt(line):
    m = URL_RT.search(line)
    if m:
        return m.group('url'), float(m.group('rt'))
    return None, 0


def parse_log(filename):
    urls = {}
    total_count = 0
    total_time = 0
    open_func = get_open_func(filename)
    # with open_func(filename, mode='r') as log:
    # log = open_func(filename, mode='r')
    # for line in log:
    for line in open_func:
        line = line.strip()
        url, rt = get_url_rt(line)
        total_count += 1
        total_time += rt
        if url not in urls:
            urls[url] = [rt]
        else:
            urls[url].append(rt)
        # print(urls)
    return total_count, total_time, urls


def process_data(data):
    ndigits = config['DIGITS']
    total_count, total_time, urls = data
    result = []
    for url in urls:
        count = len(urls[url])
        count_perc = round(100 * float(count) / total_count, ndigits)
        time_avg = round(sum(urls[url]) / count, ndigits)
        time_max = round(max(urls[url]), ndigits)
        time_med = round(median(sorted(urls[url])), ndigits)
        time_sum = round(sum(urls[url]), ndigits)
        time_perc = round(100 * time_sum / total_time, ndigits)
        result.append({
            "url": url,
            "count": count,
            "count_perc": count_perc,
            "time_avg": time_avg,
            "time_max": time_max,
            "time_med": time_med,
            "time_perc": time_perc,
            "time_sum": time_sum,
        })
    result.sort(key=lambda x: x['time_sum'], reverse=True)
    # print(result)
    return result


def bytes_to_string(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    raise TypeError('Object of type %s is not JSON serializable' % type(obj).__name__)


def save_to_html(filename, data):
    try:
        with open(config['TEMPLATE'], mode='r') as template:
            with open(filename, mode='w') as report:
                for line in template:
                    if MARKER in line:
                        report.write(line.replace(MARKER, json.dumps(data, default=bytes_to_string)))
                    else:
                        report.write(line)
    except IOError as ex:
        print(ex)


def save_to_json(filename, data):
    try:
        with open(filename, mode='w') as report:
            report.write(json.dumps(data))
    except IOError as ex:
        print(ex)


def median(values):
    if len(values) % 2 == 0:
        return (values[(len(values) // 2) - 1] + values[len(values) // 2]) // 2.0

    elif len(values) % 2 != 0:
        return values[int((len(values) // 2))]


def gen_report_name(log_filename, report_format):
    """Generate report name."""
    m = LOG_DATE.search(log_filename)
    if m:
        report_filename = 'report-{0}.{1}.{2}.{3}'.format(m.group('year'),
                                                          m.group('month'),
                                                          m.group('day'),
                                                          report_format)
        return os.path.join(config['REPORT_DIR'], report_filename)
    else:
        return None


def get_report_formatters():
    return {
        'json': save_to_json,
        'html': save_to_html
    }


def main(log, report, formatter):
    data = parse_log(log)
    result = process_data(data)
    formatter(report, result)
    # print(data)
    # print(result)


if __name__ == "__main__":
    """Log file must be in format nginx-access-ui.log-YYYYMMDD[.gz]"""
    parser = argparse.ArgumentParser(description='Parse web server logs.')
    parser.add_argument('--log_path', dest='log_path', help='path to the file')
    parser.add_argument('--report_format', dest='report_format', default='html', choices=['html', 'json'],
                        help='report format')
    parser.add_argument('--report_size', dest='report_size', default=config['REPORT_SIZE'], help='report size in lines')
    parsed_args = parser.parse_args()
    formatter_func = get_report_formatters()[parsed_args.report_format]

    last_log = get_last_log_file()

    if not last_log:
        sys.stderr.write('Can not find last log file\n')
        sys.stderr.flush()
        sys.exit(1)

    report_filename = gen_report_name(last_log, parsed_args.report_format)

    # if  report_filename:
    #     sys.stderr.write('Can not parse date from {0} filename.\n'.format(last_log))
    #     sys.stderr.flush()
    #     sys.exit(1)

    if os.path.exists(report_filename):
        sys.stderr.write('For log-file {0} exist report {1}.\n'.format(last_log, report_filename))
        sys.stderr.flush()
        sys.exit(1)

    main(last_log, report_filename, formatter_func)

    # print(report_filename)
    # print(process_data)
    # print(parse_log('./log\\nginx-access-ui.log-20170630'))
