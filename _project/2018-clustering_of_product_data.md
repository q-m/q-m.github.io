---
layout: project
title: Clustering of product data
priority: 5
status: open
contact: wvengen
---
{% include JB/setup %}

Questionmark gathers data points about food products from multiple sources. Multiple data points may describe the same product. In order to construct one definitive description of a product we would like to use as many of its data points as possible. Therefore it is vital to be able to cluster data points belonging to the same product.

If we are lucky the data points include an EAN code; data points with matching EAN codes belong to the same product. In practice however, many sources do not provide EAN codes at all. In some cases they provide multiple EAN codes for one data point.

To be able to take into account data points from such sources, an alternative means of clustering is needed.

## Goal

_Cluster data points so that one cluster represents one product._

* It should reach beyond matching EAN codes.
* Ideally data points are augmented with a fingerprint that identifies a unique product.

## Considerations

### Varying information

Data points may contain varying information, but it can be assumed that the following information is mostly available: product name, brand name, ingredients, and nutritional values. However, an upfront analysis of the information could be profitable.

### Technology

We prefer to use open source software, because it is better maintainable, but quality, performance and support are also important.

### Links

- [Semantic3 on UPC unversality](https://blog.semantics3.com/why-the-u-in-upc-doesnt-mean-universal-a1a675eea0ea) does something similar to this project.
- [Comparing and matching product names from different stores/suppliers](https://stackoverflow.com/questions/19770113/comparing-and-matching-product-names-from-different-stores-suppliers) (Stack Overflow)
- [Matching product strings](https://stackoverflow.com/questions/11980000/best-machine-learning-technique-for-matching-product-strings) (Stack Overflow)
- [Unsupervised clustering of over-the-counter healthcare products into product categories](https://www.sciencedirect.com/science/article/pii/S1532046407000287) (Journal of Biomedical Informatics)
- [Matching Unstructured Offers to Structured Product Descriptions ](https://www.microsoft.com/en-us/research/publication/matching-unstructured-offers-to-structured-product-descriptions/?from=http%3A%2F%2Fresearch.microsoft.com%2Fpubs%2F148339%2Foffermatching_kdd.pdf) - how Bing was grouping products.
- [Weaviate](https://www.semi.technology/documentation/weaviate/current/) may be interesting to try out.
