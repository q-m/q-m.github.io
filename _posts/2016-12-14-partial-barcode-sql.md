---
layout: post
title: Finding partial barcodes in SQL
author: wvengen
tags: [data, sql]
image: https://upload.wikimedia.org/wikipedia/commons/5/5d/UPC-A-036000291452.png
---
{% include JB/setup %}

With the [Questionmark App](http://www.thequestionmark.org/download) you can scan the barcode of a supermarket product,
and see how sustainable it is compared to other products. This barcode is generally a 13 or 8 digit 
[international article number](https://en.wikipedia.org/wiki/International_Article_Number)
([EAN/UPC](http://www.gs1.org/barcodes/ean-upc)), which identifies the product. These numbers are handed out by
the international [GS1](http://www.gs1.org/) organisation.

## Barcode: a unique identifier?

This number is like a unique identifier for a (consumer) product. Pretty uniquely. But not completely.
There are [rules](http://www.gs1.org/1/gtinrules) for this
(also [NL](https://www.gs1.nl/aan-de-slag/gs1-barcodes/toekennen-nieuwe-gtin)-specific ones). These aren't
always followed perfectly, however. And for us, the precise composition and sourcing of the product is
important. So a small change in sugar or salt content, for example (or even a gradual change over time),
may not warrant a new EAN-code. Bigger changes, e.g. when the brand name changes, would generally result
in a new code.

So our Questionmark products generally have one barcode, sometimes more. We can't really do much about different
products with the same barcode - and thus we take the latest information we have.
That fits with our goal of improving competition on sustainability and health.

## GS1 prefixes

But there's more. Each EAN-number starts with a [GS1](http://www.gs1.org/company-prefix) [Prefix](https://en.wikipedia.org/wiki/List_of_GS1_country_codes),
which is a 3-digit country code, handed out by the country's GS1 member organisation. Some prefixes, however,
are meant to be used internally by companies. These identifiers are _not_ global. This is the range `020`-`029`.

## Store-packaged products

In some supermarkets fruits and vegetables can be weighed by the consumer, where a barcode is printed on
the spot. This barcode is a special one, where part is product number, and part is weight, quantity or
price. These prefixes all start with `2`. How these are handled exactly depends on the GS1 member organisation.
Sweden has a good [explanation](http://www.gs1.se/en/GS1-in-practice/Items-with-variable-weight), and the
Dutch situation is explained in section 2.2.14 and 3.3.1 of their [handbook](http://images.gs1.nl/pdf/handboekupdate2010.pdf)
(which is in Dutch).

The bad news is that the same number is often used by different companies. We have found many store-packaged
EAN-codes (we call them _partial barcodes_) that are completely different products in different supermarkets.

## Finding barcodes

Now to the more technical part of this post. Say a user of our app scans a barcode, and we'd like to locate
the product associated to it. For 'regular' barcodes, we can just search by number, but for store-packaged
barcodes, the match is slightly more complicated.

Let's see how we can search using the [PostgreSQL](http://www.postgresql.org/) database.

### Dutch rules for weighted products

Dutch EAN-codes that consist of a product code (`i`) and a price (`e`) or weight (`w`), together
with check digits (`c`), have the following format:

* `21` `iiii` `c` `eeeee` `c`: price in euro cents
* `22` `iiii` `c` `eeeee` `c`: price in euro cents
* `23` `iiiii` `c` `eeee` `c`: price in euro cents (nationally unique)
* `28` `iiii` `c` `wwwww` `c`: weight in grams

For example, the EAN-code `2164941000227` would have product code `6494` and cost 0.22 euro's.

### Setup a sample database

```sql
--- some barcodes with their product name
CREATE TABLE barcodes (barcode VARCHAR PRIMARY KEY, name VARCHAR);
INSERT INTO barcodes VALUES
  ('8712439020109', 'Jori Pindakaas 350g'),
  ('8713576100129', 'TerraSana Pindakaas 250g'),
  ('2164941000227', 'EkoPlaza Appel Elstar'),
  ('2232072000000', 'Jumbo Jonagold'),
  ('2232140001472', 'Jumbo Elstar Appels'),
  ('125645',        'Jumbo Appel Jonagold');
```

### Find by 'regular' barcode

Finding the 'regular' barcode `8712439020109` is easy:

```sql
SELECT name FROM barcodes WHERE barcode = '8712439020109';
--- => 'Jori Pindakaas 350g'
```

### Find by 'partial' barcode

But for the weighted product `2232073001136`, we need something else. In this case, the
identifying product number is only the first 6 digits, so we can query using:

```sql
SELECT name FROM barcodes WHERE
  barcode LIKE '223207%' AND LENGTH(barcode) = 13;
--- => 'Jumbo Jonagold'
```

But say we have a list of barcodes we want to find, that needs a bit more intelligence. Let's
first construct a list of barcodes (`8712439020109`, `2232140001481`, `21987`), with the number of digits to compare:

```sql
SELECT
    barcode,
    CASE WHEN LENGTH(barcode) = 13 THEN
      CASE LEFT(barcode, 2)
        WHEN '21' THEN 6
        WHEN '22' THEN 6
        WHEN '23' THEN 7
        WHEN '28' THEN 6
        ELSE 13
      END
      ELSE LENGTH(barcode)
    END AS id_len
  FROM (
    VALUES ('8712439020109'), ('2232140001481'), ('21987')
  ) search (barcode);
--- => '8712439020109'  13
--- => '2232140001481'   6
--- => '21987'           5
```

Applying this search to the barcodes table, we get:

```sql
SELECT barcodes.barcode, barcodes.name FROM barcodes
  INNER JOIN (
    SELECT
      barcode, 
      CASE WHEN LENGTH(barcode) = 13 THEN
        CASE LEFT(barcode, 2)
          WHEN '21' THEN 6
          WHEN '22' THEN 6
          WHEN '23' THEN 7
          WHEN '28' THEN 6
          ELSE 13
        END
        ELSE LENGTH(barcode)
      END AS id_len
      FROM (
        VALUES ('8712439020109'), ('2232140001481'), ('21987')
      ) s (barcode)
  ) s ON
    LENGTH(barcodes.barcode) = LENGTH(s.barcode) AND
    LEFT(barcodes.barcode, s.id_len) = LEFT(s.barcode, s.id_len);
--- => '8712439020109'  'Jori Pindakaas 350g'
--- => '2232140001472'  'Jumbo Elstar Appels'
```

This is even applicable when `JOIN`ing another table with barcodes instead of the list used here.

_**edit** While this approach works, it is not very performant (as you may have guessed). A cleaner
solution may be to normalize barcodes on ingress. This is what we currenty do. Perhaps that will be
discussed in a future blog post._

