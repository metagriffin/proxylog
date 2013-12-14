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
  def test_csv_input(self):
    csv = '''\
timestamp,rline,content-type,data
1234567890.0,GET /path/to/resource HTTP/1.1,,
1234567890.1,HTTP/1.? 200 OK,text/xml,"<root ><node attr=""value""/></root>"
'''
    chk = u'''\
[1m[35m[1234567890.000] local:0 --> remote:0 (00000000.00000001)(B[m
[31m  00000000.00000001 > (B[m[1mGET /path/to/resource HTTP/1.1(B[m
[31m  00000000.00000001 > (B[m
[1m[35m[1234567890.100] local:0 <-- remote:0 (00000000.00000002)(B[m
[32m  00000000.00000002 < (B[m[1mHTTP/1.? 200 OK(B[m
[32m  00000000.00000002 < (B[m(B[mContent-Type: (B[mtext/xml
[32m  00000000.00000002 < (B[m
[32m  00000000.00000002 < (B[m[32m<?xml version="1.0" encoding="UTF-8"?>(B[m
[32m  00000000.00000002 < (B[m[1m[35m<(B[m[1m[34mroot(B[m[1m[35m>(B[m
[32m  00000000.00000002 < (B[m  [1m[35m<(B[m[1m[34mnode(B[m [1m[34mattr(B[m[1m[35m="(B[mvalue[1m[35m"(B[m[1m[35m/>(B[m
[32m  00000000.00000002 < (B[m[1m[35m</(B[m[1m[34mroot(B[m[1m[35m>(B[m
[32m  00000000.00000002 < (B[m
'''
    options = aadict(
      csv       = True,
      color     = True,
      prettify  = True,
      infile    = six.StringIO(csv),
      output    = six.StringIO(),
      errput    = six.StringIO(),
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
