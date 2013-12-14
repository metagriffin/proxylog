# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@uberdev.org>
# date: 2010/12/21
# copy: (C) Copyright 2010-EOT metagriffin -- see LICENSE.txt
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

import os
import sys
import six
import gzip
import BaseHTTPServer
# todo: replace with six.urllib...
import urllib2
import time
import pickle
import csv
import re
import pxml
from aadict import aadict
from requests.structures import CaseInsensitiveDict as idict

from .i18n import _

#------------------------------------------------------------------------------
def mkdirp(path):
  if os.path.isdir(path):
    return
  os.makedirs(path)

#------------------------------------------------------------------------------
def gunzip(data):
  if data is None:
    return data
  return gzip.GzipFile(fileobj=six.StringIO(data)).read()

#------------------------------------------------------------------------------
def headerCase(h):
  return '-'.join([e.capitalize() for e in h.split('-')])

#------------------------------------------------------------------------------
class Logger(object):
  def __init__(self, options=None):
    self.options = aadict(
      showIndent       = True,
      showPacket       = True,
      showRequestLine  = True,
      showHeaders      = True,
      showRaw          = False,
      ).update(options or [])
  def logMessage(self, messageInfo, rLine, headers, body):
    raise NotImplementedError()
  def close(self):
    pass

#------------------------------------------------------------------------------
class DisplayLogger(Logger):
  def __init__(self, stream, *args, **kw):
    super(DisplayLogger, self).__init__(*args, **kw)
    self.stream = stream
  def logMessage(self, msg, rLine, headers, body):
    if self.options.showIndent:
      indent = self.options.markup['requestPrefix' if msg.isRequest else 'responsePrefix'](
        '  {:08x}.{:08x} {} '.format(
          msg.processID, msg.requestID, '>' if msg.isRequest else '<'))
    else:
      indent = ''
    content = body
    if content and self.options.uncompress \
       and headers.get('content-encoding') == 'gzip':
      content = gunzip(content)
    if content and self.options.prettify:
      output = six.StringIO()
      pxml.prettify(six.StringIO(content.strip()), output,
                    strict=False, color=self.options.color)
      content = output.getvalue() or content
    if self.options.showPacket:
      print >>self.stream, self.options.markup.packet(
        '[{:0.3f}] {}:{} {} {}:{} ({:08x}.{:08x})'.format(
          msg.ts,
          msg.client[0], msg.client[1],
          '-->' if msg.isRequest else '<--',
          msg.server[0], msg.server[1],
          msg.processID, msg.requestID,
          ))
    if self.options.showRequestLine:
      print >>self.stream, indent + self.options.markup.rline(rLine)
    if self.options.showHeaders:
      for k,v in headers.items():
        print >>self.stream, indent + '{}: {}'.format(
          self.options.markup.headerName(headerCase(k)),
          self.options.markup.headerValue(v))
      print >>self.stream, indent
    if content is not None:
      if self.options.showRaw:
        self.stream.write(content)
      else:
        print >>self.stream, indent + ('\n' + indent).join(content.split('\n'))
    self.stream.flush()

#------------------------------------------------------------------------------
class MultiLogger(Logger):
  def __init__(self, loggers=None, *args, **kw):
    super(MultiLogger, self).__init__(*args, **kw)
    self.loggers = loggers or []
  def logMessage(self, messageInfo, rLine, headers, body):
    for logger in self.loggers:
      logger.logMessage(messageInfo, rLine, headers, body)
  def close(self):
    for logger in self.loggers:
      logger.close()

#------------------------------------------------------------------------------
class LoggingRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

  REQUESTNUM = 0

  #----------------------------------------------------------------------------
  def __init__(self, request, client_address, server):
    self.options = server.options
    self.logger  = server.logger
    LoggingRequestHandler.REQUESTNUM += 1
    self.rid = LoggingRequestHandler.REQUESTNUM
    self.pid = os.getpid()
    if self.options.verbose:
      print >>self.options.errput, \
        _('[  ] connection from client: {}:{}', *client_address)
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

  #----------------------------------------------------------------------------
  def do_GET(self):
    self.logRequest(None)
    self.sendRequest(None)
    self.logger.close()

  #----------------------------------------------------------------------------
  def do_POST(self):
    data = self.rfile.read(int(self.headers.get('content-length','0')))
    self.logRequest(data)
    self.sendRequest(data, method='POST')
    self.logger.close()

  #----------------------------------------------------------------------------
  def do_PUT(self):
    data = self.rfile.read(int(self.headers.get('content-length','0')))
    self.logRequest(data)
    self.sendRequest(data, method='PUT')
    self.logger.close()

  #----------------------------------------------------------------------------
  def sendRequest(self, content, method='GET'):
    req = urllib2.Request('%s://%s:%d%s' % (self.options.ssl and 'https' or 'http',
                                            self.options.remote[0],
                                            self.options.remote[1],
                                            self.path),
                          None, self.headers)

    # not using the build_opener as i want to handle 302s...
    #   opener  = urllib2.build_opener()
    opener = urllib2.OpenerDirector()
    opener.add_handler(urllib2.HTTPSHandler())
    opener.add_handler(urllib2.HTTPHandler())

    req.add_header('Host', '%s:%d' % (self.options.remote[0], self.options.remote[1]))

    if method not in 'GET':
      req.get_method = lambda: method

    if content is not None:
      resp = opener.open(req, content)
    else:
      resp = opener.open(req)

    info = resp.info()
    data = resp.read()

    def sedform(data):
      for xform in self.options.responseSed:
        data = xform(data)
      return data

    data = sedform(data)
    headers = idict({k: sedform(v) for k, v in info.items()})

    self.logResponse(resp, headers, data)
    self.sendResponse(resp, headers, data)

  #----------------------------------------------------------------------------
  def sendResponse(self, resp, info, data):
    # todo: is there really no way of determining the response HTTP version???
    self.wfile.write('%s %s %s\r\n' % ('HTTP/1.0', resp.code, resp.msg))
    self.wfile.write('Connection: close\r\n')
    for k,v in info.items():
      if k in ('connection', 'transfer-encoding'): continue
      # todo: encode headers in any way?
      self.wfile.write('%s: %s\r\n' % (headerCase(k), v))
    self.wfile.write('\r\n')
    self.wfile.write(data)

  #----------------------------------------------------------------------------
  def logRequest(self, content):
    self.logger.logMessage(aadict(
      ts        = time.time(),
      requestID = self.rid,
      processID = self.pid,
      isRequest = True,
      client    = (self.client_address[0], self.client_address[1]),
      server    = (self.options.remote[0], self.options.remote[1]),
      ), '%s %s %s' % (self.command, self.path, self.request_version),
      self.headers, content)

  #----------------------------------------------------------------------------
  def logResponse(self, response, headers, content):
    self.logger.logMessage(aadict(
      ts        = time.time(),
      requestID = self.rid,
      processID = self.pid,
      isRequest = False,
      client    = (self.client_address[0], self.client_address[1]),
      server    = (self.options.remote[0], self.options.remote[1]),
      ), '%s %s %s' % ('HTTP/1.?', response.code, response.msg),
      # todo: is there really no way of determining the response HTTP version???
      headers, content)

#------------------------------------------------------------------------------
class StreamLogger(Logger):
  def __init__(self, stream, *args, **kw):
    super(StreamLogger, self).__init__(*args, **kw)
    self.stream = stream
    if self.options.csv:
      self.stream = csv.writer(self.stream, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
      self.stream.writerow(['timestamp', 'rline', 'content-type', 'data'])
  def logMessage(self, msg, rLine, headers, body):
    if self.options.csv:
      self.stream.writerow(
        [msg.ts,
         rLine,
         headers.get('content-type', None),
         body,
         ])
    else:
      pickle.dump(['v0', dict(msg), rLine, dict(headers), body], self.stream)

#------------------------------------------------------------------------------
# shamelessly scrubbed from:
#   http://stackoverflow.com/questions/6556078/how-to-read-a-csv-file-from-a-stream-and-process-each-line-as-it-is-written
class UnbufferedReadlineIterator(object):
  'An iterator that calls readline() to get its next value.'
  def __init__(self, f): self.f = f
  def __iter__(self): return self
  def next(self):
    line = self.f.readline()
    if line:
      return line
    raise StopIteration

#------------------------------------------------------------------------------
# todo: perhaps the replay-server could first try pickle, then fallback to csv?
class ReplayServer(object):
  def __init__(self, options, stream):
    self.options  = options
    self.stream   = stream
  def serve_forever(self):
    if self.options.csv:
      return self._replayCsv(self.stream)
    return self._replayPickle(self.stream)
  def _replayCsv(self, stream):
    reader  = csv.reader(UnbufferedReadlineIterator(stream))
    headers = ['timestamp', 'rline', 'content-type', 'data']
    count   = 0
    for record in reader:
      if 'timestamp' == record[0]:
        headers = record
        continue
      count += 1
      msg = aadict(zip(headers, record))
      msg.ts        = float(msg.timestamp)
      msg.isRequest = not msg.rline.startswith('HTTP')
      msg.processID = 0
      msg.requestID = count
      msg.headers   = idict()
      if msg.get('content-type'):
        msg.headers['content-type'] = msg.get('content-type')
      msg.client    = ('local', 0)
      msg.server    = ('remote', 0)
      self.logger.logMessage(msg, msg.rline, msg.headers, msg.data or None)
  def _replayPickle(self, stream):
    unpkl = pickle.Unpickler(stream)
    while True:
      try:
        xaction = unpkl.load()
        if xaction[0] != 'v0':
          raise Exception(_(
            'invalid proxylog dump or unsupported version: {!r}',
            xaction[0]))
        msg = aadict(xaction[1])
        self.logger.logMessage(msg, xaction[2], xaction[3], xaction[4])
      except EOFError:
        break

#------------------------------------------------------------------------------
# TODO: replace with `reparse` once it has been converted to a library...
def parseSedExpression(expr):
  if expr[0] != 's':
    raise NotImplementedError(_('only sed operator "s" is functional'))
  expr = expr.split(expr[1])
  if len(expr) != 4:
    raise TypeError(_('invalid sed "s" expression'))
  flags = 0
  for c in expr[3].upper():
    flags |= getattr(re, c, 0)
  regex = re.compile(expr[1], flags=flags)
  def xform(data):
    return regex.sub(expr[2], data)
  return xform

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
