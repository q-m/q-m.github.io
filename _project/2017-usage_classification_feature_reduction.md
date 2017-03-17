---
layout: project
title: Feature reduction in product classification
priority: 5
status: taken
contact: wvengen
---
{% include JB/setup %}

After our [first step](/2017/01/31/product-categorization-with-machine-learning) in machine learning,
where products are automatically assigned a category, there are many directions for improvement. This
page describes a number of next steps that could be taken.


## A proper measure of success

### Clusters of items

While there are standard evaluation metrics to evaluate classification, there is a property of our
dataset that makes the standard measures a bit too good: there is a lot of (almost) duplicate data.
The reason is that we have manually categorized _clusters_ of training items, and there are many
(almost) duplicate training items within the same cluster.

Consider the following list of (imaginary) training items:

| name               | brand      | product_id | category          |
|--------------------|------------|------------|-------------------|
| Coca Cola 1.5L     | Coca Cola  | 25         | Cola              |
| Coca Cola 1 1/2L   | Coca Cola  | 25         | Cola              |
| Coca Cola          | Coca Cola  | 25         | Cola              |
| Cola (Coca)        | Coca Cola  | 25         | Cola              |
| Fanta 1.5L         | Fanta      | 30         | Softdrink, orange |
| Fanta Classic      | Fanta      | 30         | Softdrink, orange |
| Fanta Classical    | Fanta      | 30         | Softdrink, orange |
| Fanta              | Fanta      | 30         | Softdrink, orange |
| Coca Cola 6x       | Coca Cola  | 12         | Cola              |
| Coca Cola (can)    | Coca Cola  | 12         | Cola              |
| Coca Cola          | Coca Cola  | 12         | Cola              |

When validating the algorithm, common practice is to leave out a small random part of the training
items, train on the remaining items, and test if the predicted category of the leaved out items
match their original categories. One can do this several times, to cover the whole dataset, which
is called [cross-validation](https://en.wikipedia.org/wiki/Machine_learning#Model_assessments).

If we'd do plain n-fold cross-validation on this dataset, we'd get really good results. That's because
a single product's training items are all giving the same result. In reality, we are interested to
see how one or more _new_ training items perform in assigning a category.

A solution would be to split training and validation sets by product_id in n-fold cross-validation.


### Cross-check with rules

Apart from a classification algorithm, we also have static rules to derive a category from an
item. This is not always possible, or doesn't always give the desired result, that's why we still
need machine learning. It would be interesting to cross-check these rules with classification
output. This would give a measure for consistency of classification and rules.

If we could see which rules and categories have least consistency, that would help finding
bugs in the static rules and/or machine learning approach.


### Take rules into account

Since our production system uses both rules and classification to assign a category, our _real_
accuracy is the result of both. To have a real-world idea of the performance of a trained
algorithm, it would be useful to take into account both. That means, cross-validation where
training is done on the data as now, but validation is done on the classifier plus rules.


## Feature reduction

Feature extraction is currently pretty crude: all words found are taken as features for
training the support vector machine. Looking at the numbers, there are 111k training items,
resulting in 34k features (for 1k categories). That's on the high side, and there are ways
to reduce this. Benefits would be possibly higher accuracy (recall), but also a lot less
memory use, which could make the classification (and training) process quite a bit faster.

Hints:
- Before training, remove features occuring less than x times.
- Add a layer between feature extraction and classification to compress features. One
  way would be to use [variational auto-encoders](https://en.wikipedia.org/wiki/Autoencoder)
  to 'compress' the feature set. This could use training items without a category.


## Multi-class classification

Until now, we've only classified on one category. But the problem is probably more suited
to multi-class classification. We're determining a place in a hierarchy of categories,
this means that parent categories are also valid classifications.

It would be interesting to try multi-class classification. This may improve accuracy,
and may even return a parent category if it is unclear which of the child categories is more
appropriate. This improves accuracy.

