'''.
AsciiCode
=========
Jeremy Hughes <jed@jedatwork.com>
0.1.0, 2012-08-03: Initial derivation from adextract.
:asciicode-language: python

:AsciiDoc: http://methods.co.nz/asciidoc/[AsciiDoc]

An {AsciiDoc} filter for including source files with AsciiDoc comments.
.'''
import os
import re
import ast
from StringIO import StringIO

MODELINE = re.compile('''^.*?:asciicode-([^:]+):\s+(.+?)\s*$''')
DEFAULT_MODELINE_DEPTH = 10

DEFAULT_LANGUAGE = 'text'

COMMENTS = {
    'python': ("'''.", None, ".'''"),
    'py':     ("'''.", None, ".'''"),
    'c':      ('/*.', None, '.*/'),
    'c++':    ('/*.', None, '.*/'),
    'cpp':    ('/*.', None, '.*/'),
    'cxx':    ('/*.', None, '.*/'),
    'java':   ('/*.', None, '.*/')
    }


class EAsciiCode(Exception):
  pass

'''.
Modelines
---------

Modelines are
.'''

def is_modeline(line):
  match = MODELINE.match(line)
  if match:
    attr = match.groups()[0]
    val = match.groups()[1]
    return (attr, val)
  return None

def parse_attr_val(name, string):
  if name == 'numbered':
    return {name: string.lower() not in ('no', 'false', '0')}
  elif name == 'comments':
    return {name: ast.literal_eval(string)}
  else:
    return {name: string}

def modeline_conf(lines, depth):
  if not depth:
    depth = DEFAULT_MODELINE_DEPTH
  conf = {}
  for idx, line in enumerate(lines):
    args = is_modeline(line)
    if args:
      conf.update(parse_attr_val(*args))
    if idx == depth:
      break
  return conf


def parse_blocks(
    stream, output, language=DEFAULT_LANGUAGE, numbered=False,
    comments=None, **kwargs):

  if not comments and not language:
    raise EAsciiCode, 'No language or comments makes asciicode sad.'

  if language == 'text':
    for line in stream:
      output.write(line)
    return

  if not comments and language:
    comments = COMMENTS[language]

  start, mid, end = comments

  startTag = re.escape(start)
  midTag = re.escape(mid) if mid else None
  endTag   = re.escape(end)

  startRE = re.compile('''^(\s*?)''' + startTag + '''\s*$''')
  midRE = None
  if mid:
    midRE = re.compile('''^(\s*?''' + midTag + ''')''')
  endRE = re.compile('''^(\s*?)''' + endTag + '''\s*$''')

  doc_block = False
  code_block = False
  indent = 0

  for line in stream:

    start_match = startRE.match(line)
    if not doc_block and start_match:
      if code_block:
        output.write("-----\n\n")
      code_block = False
      doc_block = True
      indent = len(start_match.groups()[0])
    elif doc_block and endRE.match(line):
      doc_block = False
    elif doc_block:
      line = line[indent:]
      if midRE:
        mid_match = midRE.match(line)
        if not mid_match:
          raise EAsciiCode, 'Could not find comment: %s' % mid
        mid_indent = len(mid_match.groups()[0]) + 1
        line = line[mid_indent:]
      output.write(line)
    else:
      if not code_block:
        attrlist = ['source', language]
        if numbered:
          attrlist.append('numbered')
        output.write('[' + ','.join(attrlist) + "]\n")
        output.write("-----\n")
        code_block = True
      output.write(line)

  if code_block:
    output.write("-----\n")


def process_string(asciidoc_fn, stream, modeline_depth=None, asciidoc_args={}, **kwargs):
  conf = modeline_conf(stream, modeline_depth)
  if hasattr(stream, 'seek'):
    stream.seek(0)
  kwargs.update(conf)
  parsed = StringIO()
  parse_blocks(stream, parsed, **kwargs)
  with open('/tmp/out.txt', 'w') as f:
    f.write(parsed.getvalue())
  parsed.seek(0)
  out = StringIO()
  asciidoc_fn(parsed, out, **asciidoc_args)
  out.seek(0)
  return out

def process_file(asciidoc_fn, infile, **kwargs):
  return process_string(asciidoc_fn, infile, **kwargs)

def process_path(asciidoc_fn, path, modeline_depth=None, asciidoc_args={}, **kwargs):
  path = os.path.abspath(path)
  if 'inpath' not in asciidoc_args:
    asciidoc_args['inpath'] = path
  with open(path) as f:
    conf = modeline_conf(f, modeline_depth)
    kwargs.update(conf)
  ext = os.path.splitext(path)[1][1:]
  if ((ext in ['', 'txt', 'asciidoc'] or ext not in COMMENTS)
      and 'comments' not in kwargs and 'language' not in kwargs):
    # Process as plain AsciiDoc
    with open(path) as infile:
      out = StringIO()
      asciidoc_fn(infile, out, **asciidoc_args)
      out.seek(0)
      return out
  args = {'language': ext, 'comments':COMMENTS.get(ext, None)}
  args.update(kwargs)
  with open(path) as f:
    return process_string(asciidoc_fn, f, asciidoc_args=asciidoc_args, **args)

def process_lines(asciidoc_fn, lines, append_line_sep=False, **kwargs):
  if append_line_sep:
    lines = [line + "\n" for line in lines]
  return process_string(asciidoc_fn, lines, **kwargs)

def asciidoc_filter(lines, asciidoc_fn=None, **kwargs):
  return process_lines(asciidoc_fn, lines, append_line_sep=True, **kwargs)
