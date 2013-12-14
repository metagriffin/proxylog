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

import sys
import argparse
import BaseHTTPServer
import threading
from aadict import aadict
import morph
import blessings
import atexit

from .engine import parseSedExpression, ReplayServer, \
    MultiLogger, StreamLogger, DisplayLogger, LoggingRequestHandler
from .i18n import _

#------------------------------------------------------------------------------
def breaklines(options):
  while True:
    sys.stdin.read()
    print '\r\n' * options.breaklines

#------------------------------------------------------------------------------
def getDefaultMarkup(color):
  term = blessings.Terminal(force_styling=True)
  markup = aadict(
    packet           = term.bold_magenta,
    rline            = term.bold,
    headerName       = lambda msg: term.normal() + msg,
    headerValue      = lambda msg: term.normal() + msg,
    requestPrefix    = term.red,
    responsePrefix   = term.green,
    )
  if not color:
    for key in markup.keys():
      markup[key] = lambda msg: msg
  return markup

#------------------------------------------------------------------------------
def main(argv=None):

  cli = argparse.ArgumentParser(
    description='A simple, xml-prettifying, colorizing, logging, HTTP proxy.',
    )

  cli.add_argument(
    _('-v'), _('--verbose'),
    dest='verbose', default=0, action='count',
    help=_('enable verbose output to STDERR (multiple'
           ' invocations increase verbosity)'))

  # cli.add_argument(
  #   _('--ssl'),
  #   dest='ssl', default=False, action='store_true',
  #   help=_('upgrade outbound requests to HTTPS'))

  cli.add_argument(
    _('-p'), _('--port'), metavar=_('PORT'),
    dest='local', default=80, action='store', type=int,
    help=_('specify the local port to listen on for new'
           ' connections'))

  cli.add_argument(
    _('-r'), _('--remote'), metavar=_('HOSTPORT'),
    dest='remote', default=None, action='store',
    help=_('specify the remote server and optionally port (e.g.'
           ' "host" or "host:port")'))

  # cli.add_argument(
  #   _('-H'), _('--rewrite-host'),
  #   dest='rewriteHost', default=False, action='store_true',
  #   help=_('(TODO: IMPLEMENT) rewrite the outbound HTTP "Host"'
  #          ' header, if present, to that specified by --remote'))

  cli.add_argument(
    _('-s'), _('--response-sed'), metavar=_('SED-EXPR'),
    dest='responseSed', default=[], action='append',
    help=_('use sed-like transformation of the response body'))

  cli.add_argument(
    _('-o'), _('--output'), metavar=_('FILENAME'),
    dest='outfile', default=None, action='store',
    help=_('store all transactions to the specified file'
           ' in binary format so that it can later be replayed'
           ' with --input'))

  cli.add_argument(
    _('-a'), _('--append'), metavar=_('FILENAME'),
    dest='appfile', default=None, action='store',
    help=_('same as "--output", but append to the current'
           ' content, if the file exists'))

  cli.add_argument(
    _('-i'), _('--input'), metavar=_('FILENAME'),
    dest='infile', default=None, action='store',
    help=_('replay previous transactions recorded with'
           ' "--output" (implies "--display")'))

  cli.add_argument(
    _('--csv'),
    dest='csv', default=False, action='store_true',
    help=_('in output mode, generate CSV output; in replay'
           ' mode, read CSV data'))

  cli.add_argument(
    _('-d'), _('--display'),
    dest='display', default=False, action='store_true',
    help=_('display all transactions to STDOUT in human-'
           'readable form'))

  cli.add_argument(
    _('-c'), _('--color'),
    dest='color', default=False, action='store_true',
    help=_('use terminal color codes to differentiate HTTP'
           ' headers, content, requests and responses'
           ' (implies "--display")'))

  cli.add_argument(
    _('-u'), _('--uncompress'),
    dest='uncompress', default=False, action='store_true',
    help=_('uncompress body data (if compressed) before'
           ' displaying it (implies "--display")'))

  cli.add_argument(
    _('-x'), _('--prettify'),
    dest='prettify', default=False, action='store_true',
    help=_('known formats will be "prettified", including'
           ' XML (implies "--uncompress" and "--display")'))

  cli.add_argument(
    _('-b'), _('--breaklines'), metavar=_('COUNT'),
    dest='breaklines', default=60, type=int,
    help=_('number of lines to output to STDOUT when ^D'
           ' (Control-D) is pressed'))

  #----------------------------------------------------------------------------

  options = cli.parse_args(argv)

  if not options.remote and not options.infile:
    cli.error(_('please specify the remote server ("--remote") or input'
                ' file ("--input")'))

  if options.appfile and options.outfile:
    cli.error(_('only one of "--output" or "--append" can be specified'))

  if options.remote and options.infile:
    cli.error(_('only one of "--remote" or "--input" can be specified'))

  options.responseSed = [parseSedExpression(expr)
                         for expr in options.responseSed]

  # convert options to a dict
  options = aadict(morph.omit(options))

  options.errput = sys.stderr

  #----------------------------------------------------------------------------

  if options.infile:
    options.display = True
    if options.infile == '-':
      options.infile = sys.stdin
      if options.verbose:
        print >>sys.stderr, _('[  ] replaying transactions from <STDIN>')
    else:
      if options.verbose:
        print >>sys.stderr, _('[  ] replaying transactions from "{}"', options.infile)
      options.infile = open(options.infile, 'rb')
      atexit.register(options.infile.close)
    server = ReplayServer(options, options.infile)
  else:
    # port = options.ssl and 443 or 80
    port = 80
    if options.remote.find(':') >= 0:
      options.remote, port = options.remote.split(':', 1)
      port = int(port)
    options.remote = (options.remote, port)
    options.local = ('localhost', options.local)
    server = BaseHTTPServer.HTTPServer(options.local, LoggingRequestHandler)
    if options.verbose:
      print >>sys.stderr, _('[  ] accepting connections on {}:{}', *options.local)

  server.options = options
  server.logger  = MultiLogger()

  if options.prettify:
    options.uncompress = True

  if options.color or options.uncompress:
    options.display = True

  options.markup = getDefaultMarkup(options.color)

  append = False
  if options.appfile:
    options.outfile = options.appfile
    append = True

  if options.outfile:
    if options.outfile == '-':
      server.logger.loggers.append(StreamLogger(sys.stdout, options=options))
    else:
      fstream = open(options.outfile, 'ab' if append else 'wb')
      server.logger.loggers.append(StreamLogger(fstream, options=options))
      atexit.register(fstream.close)

  if options.display:
    server.logger.loggers.append(DisplayLogger(sys.stdout, options=options))

  if not ( options.infile or options.outfile or options.display ):
    print >>sys.stderr, _('[--] warning: no logging/displaying configured - acting as a simple proxy')

  try:
    if not options.infile:
      t = threading.Thread(target=breaklines, args=(options,))
      t.daemon = True
      t.start()
    server.serve_forever()
  except KeyboardInterrupt:
    if options.verbose:
      print >>sys.stderr, _('[  ] exiting')

  return 0

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
