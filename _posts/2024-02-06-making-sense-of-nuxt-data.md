---
layout: post
title: Making sense of Nuxt data
author: wvengen
tags: [javascript, data, spiders]
image: /assets/nuxt-green.png
---
To be able to quantify how supermarkets help society to eat healthily and
sustainably, we need to what is on the shelves. Sometimes we need to go into
the shops and look at the physical products, but more often we can collect data
online.

In the past, all websites were server-rendered HTML only, with interactions
being handle on the server side as well. Nowadays, most web applications are
client-side Javascript applications, providing more direct interaction. Still,
to be able to show the content on search engines and on older devices that may
not support all the newest features, pages are often also server-rendered.

So most dynamic websites are also viewable without Javascript, yet provide a
way for the Javascript application to take it from there. Any subsequent
interactions talk directly to APIs, instead of letting the server render
everything to HTML. And any data that is already obtained when the server
renders the page, is transferred to the application, so that it doesn't
need to load data for things already present on the page.

For Next.js, this is stored in a `script` element with `id` `__NEXT_DATA__`,
for example:

```html
<script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"locale":"en-US","id":1234}}}
</script>
```

For Nuxt.js, we see something similar:

```html
<script id="__NUXT_DATA__" type="application/json">
[
  ["Reactive", 1],
  {"props": 2},
  {"pageProps": 3},
  {"locale": 4, "id": 5},
  "en-US",
  1234
]
</script>
```

Similar, but different. 

In this simple example, you can already see the relation: the Nuxt state is an
array. The first entry is a kind of magic header `["Reactive", 1]`. The second
element is the root, here we have an object with a single key `props`. Its value
points to the index in the top-level array, which is an object with key `pageProps`.
Its value is 3, again an index in the top-level array. 

To get the full JSON from this, we can use a small Python script:

```python
#!/usr/bin/env python3
import json

data = '[["Reactive",1],{"props":2},{"pageProps":3},{"locale":4,"id":5},"en-US",1234]'

def parseNuxtData(data):
  j = json.loads(data)
  if not type(j) is list: return
  if not len(j) > 1: return
  if not j[0] == ["Reactive", 1]: return
  return _parseNuxtDict(j, j[1])

def _parseNuxtDict(j, d):
  if type(d) is dict:
    return {k: _parseNuxtDict(j, j[v]) for k,v in d.items()}
  else:
    return d

print(json.dumps(parseNuxtData(data)))
```

And indeed, this returns the expected JSON object:

```json
{"props": {"pageProps": {"locale": "en-US", "id": 1234}}}
```

The nice thing about this format of dehydrating the state, is that if the same
object is referenced from the state in multiple places, it only needs to be
serialized once (and the same index in the root array can be used).

Do note that the above is not production-level code, it uses recursion without
a limit and can explode. But it shows how to interpret this data.
