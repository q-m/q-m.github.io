#!/usr/bin/env python3
#
# Quick script to convert OpenFoodFacts ingredients.txt to RDF.
#
# Usage: python3 ingredients_to_turtle.py <ingredients.txt >ingredients.ttl
#
# See:
# - https://github.com/openfoodfacts/openfoodfacts-server/raw/master/taxonomies/ingredients.txt
# - https://wiki.openfoodfacts.org/Project:Ingredients_ontology
#
# Copyright 2020 by Stichting Questionmark <willem@thequestionmark.org>
# Licensed under the MIT license.
#
import sys
import re

class Entry:
  def __init__(self):
    self.attrs = {}

  def is_empty(self):
    return 'en' not in self.attrs

  def id(self):
    return self._make_id(self.attrs['en'][0])

  def to_turtle(self):
    return self._to_turtle_ancestors() + self._to_turtle_id() + '\n' + self._to_turtle_type() + ';\n' + self._to_turtle_attrs() + '.'

  def _to_turtle_id(self):
    return '<#%s>' % self.id()

  def _to_turtle_type(self):
    return '  a qm:ingredient'

  def _to_turtle_attrs(self):
    r = []

    if 'description' in self.attrs:
      r.append('qm:description "%s"' % self._escape(self.attrs['description']))
    if 'comment' in self.attrs:
      r.append('qm:comment "%s"' % self._escape(self.attrs['comment']))
    if 'wikidata' in self.attrs:
      r.append('qm:wikidata "%s"' % self._escape(self.attrs['wikidata']))
    if 'wikipedia' in self.attrs:
      r.append('qm:wikipedia "%s"' % self._escape(self.attrs['wikipedia']))

    for lang in ['en', 'nl']:
      if not lang in self.attrs: continue
      labels = [self._escape(s) for s in self.attrs[lang]]
      # first entry is preflabel, rest are altlabels
      r.append('skos:prefLabel "%s"@%s' % (labels[0], lang))
      for s in labels[1:-1]:
        r.append('skos:altLabel "%s"@%s' % (s, lang))

    return '  ' + ';\n  '.join([s for s in r if s])

  def _to_turtle_ancestors(self):
    r = []

    if 'ancestors' in self.attrs:
      ancestors = [self._make_id(s) for s in self.attrs['ancestors']] + [self.id()]
      for i in range(1, len(ancestors)):
        r.append('<#%s> skos:broader <#%s>.' % (ancestors[i], ancestors[i-1]))
    
    if len(r) > 0:
      return '\n'.join(r) + '\n'
    else:
      return ''

  def _make_id(self, s):
    return re.sub(r'[^A-Za-z0-9_-]', '_', s)

  def _escape(self, s):
    return s.replace('"', '\\"')

def parse_file(f):
  entry = Entry()

  for line in sys.stdin:
    line = line.strip()

    # skip empty lines
    if line == '':
      if not entry.is_empty(): yield entry
      entry = Entry()
      continue

    # optional description preceding ingredient
    m = re.search(r'^\s*(?:#\s*)?description(\w\w):(.*)$', line)
    if m:
      if m.group(1) == 'en':
        s = m.group(2).strip()
        if s != '': entry.attrs['description'] = s
      continue

    # optional comment preceding ingredient
    m = re.search(r'^\s*(?:#\s*)?comment:(\w\w):(.*)$', line)
    if m:
      if m.group(1) == 'en':
        s = m.group(2).strip()
        if s != '': entry.attrs['comment'] = s
      continue

    # parents in hierarchy
    m = re.search(r'^\s*(?:#\s*)?<(\w\w):(.*)$', line)
    if m:
      if m.group(1) == 'en':
        if 'ancestors' not in entry.attrs: entry.attrs['ancestors'] = []
        s = m.group(2).strip()
        if s != '': entry.attrs['ancestors'].append(s)
      continue

    # wikidata
    m = re.search(r'^\s*wikidata:(\w\w):(.*)$', line)
    if m:
      if m.group(1) == 'en':
        s = m.group(2).strip()
        if s != '': entry.attrs['wikidata'] = s
      continue
    
    # wikipedia
    m = re.search(r'^\s*wikipedia:(?:(\w\w):)?(.*)$', line)
    if m:
      if m.group(1) == 'en':
        s = m.group(2).strip()
        if s != '': entry.attrs['wikipedia'] = s
      continue

    # skip comments
    m = re.search(r'^\s*#', line)
    if m:
      continue

    # labels
    m = re.search(r'^(\w\w):(.*)$', line)
    if m:
      if m.group(1) not in entry.attrs: entry.attrs[m.group(1)] = []
      for s in m.group(2).split(','):
        s = s.strip()
        if s != '': entry.attrs[m.group(1)].append(s)
      continue

  if not entry.is_empty():
      yield entry

print('''
@prefix qm: <http://thequestionmark.org/rdf/product#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

''')
for entry in parse_file(sys.stdin):
  print('\n' + entry.to_turtle())
 
# vim:ts=2:sw=2:expandtab:
