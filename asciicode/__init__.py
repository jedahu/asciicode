'''.
AsciiCode
=========
Jeremy Hughes <jed@jedatwork.com>
0.1.0, 2012-08-03: Initial derivation from adextract.
:asciicode: language=python comments="''' '''".

:AsciiDoc: http://methods.co.nz/asciidoc/[AsciiDoc]

An {AsciiDoc} filter for including source files with AsciiDoc comments.
.'''
import os
import re
import shlex
from StringIO import StringIO

MODELINE_START = ':asciicode:'
MODELINE_END = '.'
DEFAULT_MODELINE_DEPTH = 10

DEFAULT_LANGUAGE = 'text'

COMMENTS = {
    'python': "'\'' '\''",
    'py':     "'\'' '\''",
    'c':      '/* */',
    'c++':    '/* */',
    'cpp':    '/* */',
    'cxx':    '/* */',
    'java':   '/* */',
    }


def is_modeline(line):
  return line.find(MODELINE_START) != -1

def parse_modeline(line):
  start = line.find(MODELINE_START) + len(MODELINE_START)
  end = line.rfind(MODELINE_END)
  pairs = shlex.split(line[start:end])
  conf = {}
  for p in pairs:
    if '=' in p:
      key, val = p.split('=')
      conf[key] = val
    elif p.startswith('no_'):
      conf[p[3:]] = False
    else:
      conf[p] = True
  return conf

def modeline_conf(lines, depth):
  if not depth:
    depth = DEFAULT_MODELINE_DEPTH
  for idx, line in enumerate(lines):
    if is_modeline(line):
      return parse_modeline(line)
    if idx == depth:
      break
  return {}


class AsciiDocBlock(object):

  def __init__(self, arg):
    super(AsciiDocBlock, self).__init__()
    self.content = arg

  def __len__(self):
    return len(self.content)

  def __str__(self):
    return self.content


class CodeBlock(object):

  """CodeBlock is actually a list of source code lines."""

  currentLine = 1
  numbered    = False
  language    = None

  def __init__(self, arg):
    super(CodeBlock, self).__init__()
    self.content  = arg

  def __str__(self):

    res = ""

    if self.content:
      language = self.__class__.language or DEFAULT_LANGUAGE
      attrlist = ['source', language]
      if self.__class__.numbered:
        attrlist.append('numbered')
      res = '[' + ','.join(attrlist) + "]\n"
      res += "----\n"
      res += self.content
      res += "\n"
      res += "----\n"

    return res


def parseBlocks(
    data, output, language=None, src_numbered=False,
    comments=None, **kwargs):

  if not comments and not language:
    raise Exception('No language or comments makes asciicode sad.')

  if not comments and language:
    comments = COMMENTS[language]

  start, end = comments.split()

  CodeBlock.numbered = src_numbered
  CodeBlock.language = language

  startTag = re.escape(start)
  endTag   = re.escape(end)

  asciiDocRE = re.compile( startTag
                         + """\.(.*?)\."""
                         + endTag
                         + """\n?"""
                         , re.DOTALL
                         )

  pos            = 0
  blocks         = []

  while pos < len(data):

    m = asciiDocRE.search(data, pos)

    if not m:
      break

    blocks.append(CodeBlock(data[pos : m.start(0)]))
    blocks.append(AsciiDocBlock(m.group(1)))

    pos = m.end(0)

  blocks.append(CodeBlock(data[pos:]))

  for b in blocks:
    output.write(str(b) + "\n")


def process_string(asciidoc_fn, string, modeline_depth=None, **kwargs):
  conf = modeline_conf(StringIO(string), modeline_depth)
  kwargs.update(conf)
  parsed = StringIO()
  parseBlocks(string, parsed, **kwargs)
  parsed.seek(0)
  out = asciidoc_fn(parsed)
  out.seek(0)
  return out

def process_file(asciidoc_fn, infile, **kwargs):
  string = infile.read()
  return process_string(asciidoc_fn, string, **kwargs)

def process_path(asciidoc_fn, path, modeline_depth=None, **kwargs):
  with open(path) as f:
    conf = modeline_conf(f, modeline_depth)
    kwargs.update(conf)
  ext = os.path.splitext(path)[1][1:]
  if ((ext in ['', 'txt', 'asciidoc'] or ext not in COMMENTS)
      and 'comments' not in kwargs and 'language' not in kwargs):
    # Process as plain AsciiDoc
    out = asciidoc_fn(path)
    out.seek(0)
    return out
  args = {'language': ext, 'comments':COMMENTS.get(ext, None)}
  args.update(kwargs)
  with open(path) as f:
    return process_string(asciidoc_fn, f.read(), **args)

def process_lines(asciidoc_fn, lines, **kwargs):
  return process_string(asciidoc_fn, os.linesep.join(lines), **kwargs)
