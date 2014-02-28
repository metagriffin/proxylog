# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@uberdev.org>
# date: 2013/12/14
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
#------------------------------------------------------------------------------
# This software is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#------------------------------------------------------------------------------

import unittest
import six
from aadict import aadict

from .engine import parseSedExpression, ReplayServer, \
    MultiLogger, StreamLogger, DisplayLogger, LoggingRequestHandler
from .cli import getDefaultMarkup

#------------------------------------------------------------------------------
class TestProxylog(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_input_xml(self):
    yaml = '''\
---
content: null
headers:
  host: host.example.com:80
meta:
  client: 127.0.0.1:1234
  isRequest: true
  processID: 1
  requestID: 1
  server: 127.0.0.1:80
  ts: 1234567890.0
rline: GET /path/to/data.xml HTTP/1.1
---
content: '<root ><node attr="value"/></root>'
headers:
  content-length: '34'
  content-type: application/xml
  date: Fri, 13 Feb 2009 23:31:30 GMT
  last-modified: Fri, 13 Feb 2009 23:31:30 GMT
  server: SimpleHTTP/0.6 Python/2.7.3
meta:
  client: 127.0.0.1:1234
  isRequest: false
  processID: 1
  requestID: 1
  server: 127.0.0.1:80
  ts: 1234567890.1
rline: HTTP/1.? 200 OK
'''
    chk = u'''\
[1m[35m[1234567890.000] 127.0.0.1:1234 --> 127.0.0.1:80 (00000001.00000001)(B[m
[31m  00000001.00000001 > (B[m[1mGET /path/to/data.xml HTTP/1.1(B[m
[31m  00000001.00000001 > (B[m(B[mHost: (B[mhost.example.com:80
[31m  00000001.00000001 > (B[m
[1m[35m[1234567890.100] 127.0.0.1:1234 <-- 127.0.0.1:80 (00000001.00000001)(B[m
[32m  00000001.00000001 < (B[m[1mHTTP/1.? 200 OK(B[m
[32m  00000001.00000001 < (B[m(B[mDate: (B[mFri, 13 Feb 2009 23:31:30 GMT
[32m  00000001.00000001 < (B[m(B[mLast-Modified: (B[mFri, 13 Feb 2009 23:31:30 GMT
[32m  00000001.00000001 < (B[m(B[mContent-Length: (B[m34
[32m  00000001.00000001 < (B[m(B[mContent-Type: (B[mapplication/xml
[32m  00000001.00000001 < (B[m(B[mServer: (B[mSimpleHTTP/0.6 Python/2.7.3
[32m  00000001.00000001 < (B[m
[32m  00000001.00000001 < (B[m[38;5;30m<?xml version="1.0" encoding="UTF-8"?>[39m
[32m  00000001.00000001 < (B[m[38;5;90;01m<root[39;00m[38;5;90;01m>[39;00m
[32m  00000001.00000001 < (B[m  [38;5;90;01m<node[39;00m [38;5;64mattr=[39m[38;5;167m"value"[39m[38;5;90;01m/>[39;00m
[32m  00000001.00000001 < (B[m[38;5;90;01m</root>[39;00m
[32m  00000001.00000001 < (B[m
'''
    options = aadict(
      color     = True,
      format    = True,
      infile    = six.StringIO(yaml),
      output    = six.StringIO(),
      markup    = getDefaultMarkup(True),
    )
    server = ReplayServer(options, options.infile)
    server.options = options
    server.logger  = DisplayLogger(options.output, options=options)
    server.serve_forever()
    self.assertMultiLineEqual(options.output.getvalue(), chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
