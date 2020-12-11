---
layout: post
title: Matching ingredients with linked data
author: wvengen
tags: [data, linked data]
image: 
---
With a slow rise in the awareness of the climate emergency, there is surfacing
some commitment to take action on this, also by governments. One action is to
reduce the use of animal-based food, because it has a large impact on the planet,
and we don't really need it to live (as supported by the [Netherlands Nutrition
Centre](https://www.voedingscentrum.nl/nl/service/english.aspx), which lays out
the framework for a healthy diet in the country).

One recent ambition is to reduce the amount of animal-based vs. plant-based proteins
from 60% animal-based and 40% plant-based to 40% animal-based and 60% plant-based
in 2050 ([Transitieagenda Biomassa en voedsel](https://www.rijksoverheid.nl/documenten/rapporten/2018/01/15/bijlage-5-transitieagenda-biomassa-en-voedsel)).

With [Superlist](https://www.superlijst.org/) we will compare supermarkets on
how they are taking their responsibility in this transition. Hence the need to
analyze food-products on the source of their proteins.

# Ingredient analysis

At [Questionmark](https://www.thequestionmark.org/en) we gather and analyse data
of food products. One thing we do is parse the ingredient-declaration into the
individual ingredients (with the help of [food-ingredient-parser-ruby](https://github.com/q-m/food-ingredient-parser-ruby),
something that deserves a later blog article). When we have the ingredients, we'd
like to know if it is an animal-based protein or not. While we do have a system
in place to help with that analysis, it could be better. And why do all the
work ourselves, when there are existing databases that already know properties
of ingredients?

Well, it turns out, there are several of these databases, but data quality is
an issue: if we need to review and complete a lot manually, it's less work to
tag the data we need by hand. [In this gist](https://gist.github.com/wvengen/0d202dafb78070baa6c269117f8bbf9e)
I've played with [OpenFoodFacts](https://openfoodfacts.org) linked data and
[Wikidata](https://www.wikidata.org/) before, but the result wasn't that usable
yet.

In this blog article, I'll look at the OpenFoodfacts ingredients database,
as [explained here](https://wiki.openfoodfacts.org/Project:Ingredients_ontology).
It will be converted to RDF and linked to a fictional product, so that we
can analyse its ingredients.

For those new to [linked data](https://en.wikipedia.org/wiki/Linked_data), it
is structured data, like a relational database, but instead of tables being the
central idiom, it's relations that are central. Everything consists a
subject-relation-object triple, which is called a triplet.

# A fictional product

We'll use the [Turtle](https://www.w3.org/2007/02/turtle/primer/) file-format
to specify what our sample product looks like:

```turtle
@prefix qm: <http://thequestionmark.org/rdf/product#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<#pastasauce>
  a qm:product;
  rdfs:label "Pasta saus"@nl;
  qm:ingredientsText "tomaten, room, paprika, ui, aroma's"@nl;
  qm:containsIngredient
    [ rdfs:label "tomaten"@nl ],
    [ rdfs:label "room"@nl ],
    [ rdfs:label "paprika"@nl ],
    [ rdfs:label "ui"@nl ],
    [ rdfs:label "aroma's"@nl ].
```

In short, we have a pasta sauce product with Dutch label _Pasta saus_,
the ingredients as text, and a list of ingredients. We'd like to link
those ingredients to other entities, which we know more of.

This file is stored as `product.ttl`.

For more information about how to encode food-product-data like this,
you could look at [this article](https://www.sciencedirect.com/science/article/pii/S1319157818312680).

# The OpenFoodFacts ingredients

OpenFoodFacts has an [ingredients list](https://github.com/openfoodfacts/openfoodfacts-server/raw/master/taxonomies/ingredients.txt),
and the file-format is described on [this wiki-page](https://wiki.openfoodfacts.org/Project:Ingredients_ontology).

Before we can query this data, the file needs to be converted to Turtle.
That required writing a script, [ingredients_to_turtle.py](../assets/ingredients_to_turtle.py).

```sh
# get the conversion script
wget https://developers.thequestionmark.org/assets/ingredients_to_turtle.py
# download the ingredients file
wget https://github.com/openfoodfacts/openfoodfacts-server/raw/master/taxonomies/ingredients.txt
# convert it to the Turtle file format
python3 ingredients_to_turtle.py <ingredients.txt >ingredients.ttl
# and check that it is a valid Turtle file (optional, requires raptor2-utils on Debian/Ubuntu)
rapper -i turtle -c ingredients.ttl
# => rapper: Parsing URI file:ingredients.ttl with parser turtle
# => rapper: Parsing returned 13781 triples
```

# Querying

Now that we have the data, let's see if we can ask it some questions. For that, we'll
use [RDFlib](https://rdflib.dev/), a Python package for working with linked data. Let's
do that interactively with `IPython`.

In short, we'll load the Turtle files into a graph (a triple store, a linked data database), 
then ask it questions using the [SPARQL](https://en.wikipedia.org/wiki/SPARQL) query language.

```python
import rdflib

# Create a new graph (triple store).
g = rdflib.Graph()

# Load the product and the ingredients.
g.load('product.ttl', format='turtle')
g.load('ingredients.ttl', format='turtle')

# How many triplets do we have?
len(g)
# => 13733

# Let's see if we can find "pectins" in the ingredients.
g.query('''
  PREFIX qm: <http://thequestionmark.org/rdf/product#>
  PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

  SELECT ?label_en WHERE {
    ?i
      a qm:ingredient;
      skos:prefLabel ?label_en;
      skos:prefLabel|skos:altLabel "pectins"@en.
    FILTER(lang(?label_en) = "en")
  }
''').result
# => [(rdflib.term.Literal('pectin', lang='en'),)]
#
# So it can be found, and the preferred label for it is 'pectin'.

# Let's see if we can find the product's ingredients.
list(g.query('''
  PREFIX qm: <http://thequestionmark.org/rdf/product#>
  PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  SELECT ?ingredient_name WHERE {
    ?p
      a qm:product;
      qm:containsIngredient [ rdfs:label ?ingredient_name ].
  }
'''))
# => [(rdflib.term.Literal('ui'),),
#     (rdflib.term.Literal("aroma's"),),
#     (rdflib.term.Literal('tomaten'),),
#     (rdflib.term.Literal('room'),),
#     (rdflib.term.Literal('paprika'),)]
#
# That's a list of the ingredient names, seems fine.

# Now match them with the ingredients in the triple store
list(g.query('''
  PREFIX qm: <http://thequestionmark.org/rdf/product#>
  PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  SELECT ?ingredient_name ?i_label_en ?wikipedia WHERE {
    ?p
      a qm:product;
      qm:containsIngredient [ rdfs:label ?ingredient_name ].

    OPTIONAL {
      ?i skos:prefLabel|skos:altLabel ?ingredient_name;
         skos:prefLabel ?i_label_en.

      OPTIONAL { ?i qm:wikipedia ?wikipedia. }

      FILTER(lang(?i_label_en) = "en")
    }
  }
'''))
# => [(rdflib.term.Literal('room', lang='nl'),
#       rdflib.term.Literal('cream', lang='en'),
#       rdflib.term.Literal('https://en.wikipedia.org/wiki/Cream')),
#     (rdflib.term.Literal('ui', lang='nl'),
#       rdflib.term.Literal('onion', lang='en'),
#       rdflib.term.Literal('https://en.wikipedia.org/wiki/Onion')),
#     (rdflib.term.Literal("aroma's", lang='nl'),
#       rdflib.term.Literal('flavouring', lang='en'),
#       None),
#     (rdflib.term.Literal('paprika', lang='nl'),
#       rdflib.term.Literal('bell pepper', lang='en'),
#       rdflib.term.Literal('https://en.wikipedia.org/wiki/Bell_pepper')),
#     (rdflib.term.Literal('tomaten', lang='nl'),
#       None,
#       None)]
#
# And here we have the same list of ingredient names, but now with extra info.
```

So with the last query, we could get the list of the product's ingredient names
and lookup these names in the list of ingredients, returning the English preferred name,
and for some ingredients a link to the Wikipedia page.

_Tomaten_ was not found, so perhaps the list only contains singular nouns, or has
incomplete Dutch labels. Looking into the ingredients, it becomes clear that _tomato_
is present, but _tomatoes_ not. These are small things that could be improved,
so for now it looks as if it could be of use to us. But a test on many real-world products
would be necessary.

We don't know yet how to see if the ingredient is animal- or plant-based, but
we're one step further already, and leave that for later.
