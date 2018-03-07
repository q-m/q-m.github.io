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

We prefer to use open source software, because it is better maintainable, but quality and performance is at least as important.
