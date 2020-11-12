---
layout: project
title: A semantic web of food
priority: 3
status: open
contact: wvengen
---
{% include JB/setup %}

Questionmark maintains a database of food products sold in Dutch supermarkets. At the moment,
much is stored in a SQL database. When we'd like to experiment with integrating new data on
supermarkets, brands, products or ingredients, we currently have two options: either do it
in a spreadsheet, linking data manually (which is often labor-intensive and error-prone),
or add the data to our database (which requires modeling of the data and development). Both
are less than ideal.

## Approach

One way to make this better, could be to (also) keep our data in an RDF triple store, which
allows much easier linking to other (RDF) datasets. It might combine the ease of spreadsheets
(one can link data from different sources) with the reproducability of databases (the queries
are easy to run again), combining data from different datastores (e.g. using federated SPARQL).

### Triple store

A first step would be to convert the product data to RDF triplets. Hopefully we can re-use
an existing ontology, but perhaps not completely (I've yet to encounter fully parsed ingredient
declarations, for example).

Then put the data in a triple store, and see how we can return results for existing questions, like:

* Show product details (name, brand, package size, nutrients, ingredients, certifications).
* What are categories for a certain brand, with product amounts?
* What are the min/average/max sugar and salt amounts for all second-level categories?
* What share of pizza's have one or more meat-ingredients?

### Connect

Then connect this data to other data, e.g. Wikidata or FoodVoc
(see [this gist](https://gist.github.com/wvengen/0d202dafb78070baa6c269117f8bbf9e) for an example
on OpenFoodFacts data).


### Links

* Ontologies / vocabularies
  * OpenFoodFacts: [Ontology](https://wiki.openfoodfacts.org/Structured_Data) and [Ingredients Ontology](https://wiki.openfoodfacts.org/Project:Ingredients_ontology)
  * [FoodVoc](http://foodvoc.org/) (from [e-foodlab](https://www.commit-nl.nl/projects/e-foodlab))
  * [FoodOn](https://foodon.org/)
  * FoodWiki [article](https://dx.doi.org/10.1155%2F2015%2F475410)
  * [Product Types Ontology](http://www.productontology.org/)
