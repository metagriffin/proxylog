# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/02/27
# copy: (C) Copyright 2014-EOT metagriffin -- see LICENSE.txt
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

import six
import yaml
import morph
import json

#------------------------------------------------------------------------------
def _writeObject(obj, out, color=True, level=0, indent='  '):
  def _write(obj, level):
    curdent = indent * level
    if morph.isseq(obj):
      out.write('[\n')
      last = len(obj)
      for idx, val in enumerate(obj):
        out.write(curdent)
        out.write(indent)
        _write(val, level=level + 1)
        if idx + 1 < last:
          out.write(',')
        out.write('\n')
      out.write(curdent)
      out.write(']')
      return
    if morph.isdict(obj):
      out.write('{\n')
      last = len(obj)
      for idx, (key, val) in enumerate(obj.items()):
        out.write(curdent)
        out.write(indent)
        _write(key, level=level + 1)
        out.write(': ')
        _write(val, level=level + 1)
        if idx + 1 < last:
          out.write(',')
        out.write('\n')
      out.write(curdent)
      out.write('}')
      return
    out.write(json.dumps(obj))
  return _write(obj, level)

#------------------------------------------------------------------------------
def prettify(input, output=None, strict=True, color=True):
  stream = output or six.StringIO()
  if morph.isstr(input) or isinstance(input, six.binary_type):
    data = input
  else:
    data = input.read()
  try:
    ydata = yaml.load(data)
  except Exception as err:
    if strict:
      raise
    if output:
      output.write(data)
      return
    return data
  _writeObject(ydata, stream, color=True)
  if output:
    return
  return stream.getvalue()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
