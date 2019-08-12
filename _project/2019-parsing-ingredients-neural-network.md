---
layout: project
title: Parsing ingredients with a neural network
priority: 12
status: open
contact: wvengen
---
{% include JB/setup %}

To be able to say something about whether food products contain a certain
ingredient, and how that ingredient may consist of other ingredients, one needs
to parse an ingredient description. This is not very straightforward on real-world
data. There are many ways in which this is encoded. On top of that, data may be
extracted using OCR resulting in small errors (even in sources which are assumed
to be checked). 

For simple ingredient declarations is it straightforward. For simple declarations like
`ingredients: water, aroma` it is straightforward: remove any prefix (`ingredients: `)
and separate by comma. Then nested ingredients need to be recognized (`water, aroma (plant extracts, E123)`),
percentages (`water (80%), aroma (10%)`). And many many variants of the previous,
using semicolons, linebreaks, etc. as well footnotes in various styles.

We wrote a [parser](https://github.com/q-m/food-ingredient-parser-ruby) that parses about 80% of the
declarations in the Dutch market (and one that parses everything with a larger error margin), see
[test cases](https://github.com/q-m/food-ingredient-parser-ruby/blob/master/data/test-cases) for what it recognizes.
But this traditional parser fails in many cases, including [these](https://github.com/q-m/food-ingredient-parser-ruby/blob/master/data/test-samples-with-issues).

## Goal

Parse ingredient declarations appearing on (Dutch) food products correctly,
possible correcting for (e.g. OCR) errors.

## Approach

While a traditional syntax-based parser with some added rules parses about 80%,
a sequence-to-sequence neural network can include word context and may give a
better performance.

The existing parser can be used to generate a training set (after some cleaning up).
Alternatively, Questionmark could generate a list from its database which has been
corrected to some extent already.

Then each word in the training set can be automatically labelled (e.g. opening parenthesis,
separator, footnote, etc.) This can be fed to a sequence model.

## Links

- [seq2seq parser](https://github.com/bcmi220/seq2seq_parser) - sequence to sequence model for dependency parsing
- [seq2seq](https://github.com/farizrahman4u/seq2seq) - sequence to sequence learning with Keras
- [seq2seq with Tensorflow](https://apimirror.com/tensorflow~guide/tutorials/seq2seq)
