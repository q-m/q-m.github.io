---
layout: post
title: Product classification using a pattern matching-based expert system
author: s-andringa
tags: [classification, pattern matching, expert system]
image: /assets/hierarchy.png
---
A vital part of Questionmark's activities is gathering, interpreting and augmenting food stuff data. By doing so Questionmark is able to gain useful sustainability and health-related insights into the assortments of the largest food retailers in the Netherlands. An important step in this process is classifying products. Knowing a product's category makes it possible to infer all kinds of important information that might otherwise be unavailable, such as serving size and substance density.

Every week thousands of products need to be categorized into 1500+ categories, so clearly the goal is to automate as much as possible. For this purpose Questionmark combines two different systems: one based on machine learning and one which is a so-called _expert system_. This article focusses on the latter. It describes the expert system's rationale, design, and preliminary conclusions.

## Expert systems

An expert system is a system that uses domain specific knowledge in order to make predictions about entities or processes. In our case it must predict what category a product belongs to based on other information. This could for example be an ingredient list, a brand, or other category information.

It could, for instance, implement rules such as:

> If the product contains added sugars it is never fresh produce.

> If its brand is Kellogg's it must a cereal.

> If at source X it is categorized as either milk or yoghurt then it must be dairy.

### What are the benefits of an expert system?

First of all, it can help narrowing down machine learning predictions. For instance, if at a generic level the expert system determines that a given product must be non-food, we can rule out all machine learning predictions for categories that are not in the same subtree of the category taxonomy, in this case food categories.

Additionally, a machine learning-based system needs a growing amount of validated training data in order to improve itself. This means that its predictions will need to be manually validated and corrected where necessary, before they can be fed back to the system. Contrarily, predictions made by an expert system do not always require manual validation. Not only does this save manual labour, it can also automatically generate legitimate training data and therefore help improving machine learning predictions.

Finally an expert system is not a black box like some machine learning solutions, such as neural networks. This makes it easier to inspect, debug and adapt.

Of course it also has its drawbacks. Foremost, it requires knowledge and this knowledge needs to be inserted and managed. This still requires manual labour and can be a tedious practice.

## Design

As we have seen, the rules in an expert system can take all kinds of information as their input, such as a list of ingredients or a brand. A fair share of the data points gathered by Questionmark include some form of category information. Since the desired output is also a category, it seems logical to start there.

Here's an example of such information:

- food > fruit > apple

It represents a path through some category tree: from a generic category on the left to more specific categories to the right.

Unfortunately, different sources use different taxonomies for categorizing their products. We might also encounter the following paths:

- food > fruit > apple > gala
- fruit and vegetables > fruit > apple
- food > produce > fresh fruit > apples

In our case all of these must be mapped to the target category "Fruit > Apples". How could we describe an expert rule that tells the system to map products with any of the listed paths to their target category?

> If any part of the category contains "fruit" and a following part is either "apple" or "apples" then the target category is "Fruit > Apples".

Imagine a massive registry of rules in this form. It will be hard to find specific rules and writing them all out like this can be time consuming. Not to mention that in practice the rules are rarely as simple as in this example. We need a better manageable way to define rules.

## Pattern matching

Pattern matching is a technique used to match a pattern against sequences of tokens. The pattern describes what a sequence must look like in order to match. Probably the most common example of pattern matching is _regular expressions_. Using a regular expression the conditions from the above rule can be expressed as:

```
fruit.*>\s*apples?(\s*>|$)
```

There are some problems with regular expressions that make it a suboptimal choice for describing our rules. They are hard to learn, they quickly become complex and hard to read, and they are too generic and powerful. All of this increases the chance of mistakes, especially when non-technical users must use them.

An interesting alternative is PostgreSQL's [ltree](https://www.postgresql.org/docs/current/ltree.html) extension. It features a language specifically designed to match tree paths. Unfortunately it does not have all the features that we require. And it has been implemented for PostgreSQL only. But if that's what you're using it might be worth taking a look at.

### Tiered Category Expressions

We ended up creating a custom pattern matching language, similar to ltree's, but tailored to our needs. We have named it _Tiered Category Expressions_ (TCEs).

It is designed to be easy to learn for non-technical users, and easy to read and understand. In the simplest scenario an expression mimics the category it is supposed to match, e.g. "fruit > apple" can be matched with the expression `fruit > apple`.

Using a TCE the above rule is expressed as:

```
>> %fruit% >> apple | apples
```

TCE features a.o. child and descendant matching, wildcard matching, and negation. Expressions match subtrees by default. Whitespace and special characters are ignored and matching is always case insensitive. Read more about these and other language features in the [TCE language reference](https://github.com/q-m/tiered_category_expressions/blob/master/LANGREF.md). Also TCEs can be transpiled to regular expressions, so the actual matching can be delegated to any platform that supports regular expressions. The Ruby implementation can be found [here](https://github.com/q-m/tiered_category_expressions).

## Conclusions

We only recently started using TCEs with our expert system, though here are some preliminary conclusions and observations.

- It still takes time to write proper rules. This is mostly an up-front task. Once you have a set of good, change-resilient rules, you'll only need to check and update rules when you integrate new sources.
- Writing rules requires a lot of precision and care. TCE features like wildcards or negation can easily undermine strict unambiguous rules.
- Non-technical users still need time to get familiar with the TCE syntax.
- When creating rules, having some validated data provides invaluable insight into real world categories, how they map to target categories, and what exceptions may occur.
- With a registry of hundreds of rules it becomes hard to detect possible duplicates or overlapping rules (when two rules apply to a single category path).
- We needed to extend our system to deal with some exceptions. E.g. sometimes a rule must only apply to a specific source and then take precedence over more generic rules.
- Source data cannot always be trusted to be correct, you might still need some sort of manual validation or error detection in place.
