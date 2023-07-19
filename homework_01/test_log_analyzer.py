#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import log_analyzer


class LogAnalyzerTests(unittest.TestCase):

    def test_parse_log(self):
        line_1 = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300]\
                  "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-"\
                  "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5"\
                  "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'

        self.assertEqual(log_analyzer.get_url_rt(line_1),
                         ('/api/v2/banner/25019354', 0.390))

    def test_median(self):
        # медиана для четного количества
        self.assertEqual(log_analyzer.median([1, 2, 3, 4, 5]), 3)
        # медиана для нечетного количества
        self.assertEqual(log_analyzer.median([1, 2, 4, 5]), 3)
        # медиана для одного значения
        self.assertEqual(log_analyzer.median([1]), 1)

    def test_process_data(self):
        log_list = [
            1,
            3,
            ({
                '/api/v2/banner/25019354': [0.390],

            }),

            ]
        result = [
            {
                "url": '/api/v2/banner/25019354',
                "count": 1,
                "count_perc": 100.0,
                "time_avg": 0.390,
                "time_max": 0.390,
                "time_med": 0.390,
                "time_perc": 13.0,
                "time_sum": 0.390,
            }
        ]

        self.assertEqual(log_analyzer.process_data(log_list), result)


if __name__ == "__main__":
    unittest.main()
