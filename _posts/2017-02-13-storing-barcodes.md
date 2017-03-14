---
layout: post
title: Storing barcodes
author: wvengen
tags: [data, sql]
image: https://upload.wikimedia.org/wikipedia/commons/5/5d/UPC-A-036000291452.png
---
{% include JB/setup %}

In a [previous blogpost](/2016/12/14/partial-barcode-sql), we talked about barcodes and EAN-numbers, and
how in some cases barcodes with different numbers still reference the same product. The solution for
searching there was not very performant, and wouldn't scale to more than a handful of barcodes to check.

This post describes how to store barcodes in the [PostgreSQL](http://www.postgresql.org/) database in a
normalized way, so that searching can be done without slowing down queries. As a bonus, we get a stronger
uniqueness constraint.


## Partial barcodes

Let's quickly summarize why this is important again. Barcodes, we'll focus on EAN-numbers, consist of
a 3-digit country code, and a product identifier. Some of these country codes are reserved, however,
and each country can use them as they wish. In The Netherlands, the country codes `21`, `22`, `23`
and `28` are reserved for codes that include a short product indentifier as well as a price or weight.
This allows for example supermarkets to weigh apples, and print a barcode with product identifier
and weight.

Since we are just interested in the product identifier, and want to find any matching product
(regardless its price or weight); and we want to be sure that we only have one product in our database,
we'd like to store barcodes without price or weight.


## Normalized barcodes

First we need a set of functions to normalize a barcode, so that for partial barcodes any price or weight
is cleared:

```sql
--- number of digits of the product identification part of the barcode
CREATE FUNCTION ean13_nl_id_length(text) RETURNS integer
    LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE
    AS $_$
BEGIN
    RETURN CASE
        WHEN LENGTH($1) = 13 THEN
            CASE LEFT($1, 2)
                WHEN '21' THEN 6
                WHEN '22' THEN 6
                WHEN '23' THEN 7
                WHEN '28' THEN 6
                ELSE 13
            END
        ELSE LENGTH($1)
    END;
END;
$_$;

--- barcode with weight or price removed
CREATE FUNCTION ean13_nl_id(text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE
    AS $_$
BEGIN
    RETURN LEFT($1, ean13_nl_id_length($1));
END;
$_$;

--- normalized barcode
CREATE FUNCTION ean13_nl_normalize(text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE
    AS $_$
BEGIN
    RETURN CASE
        WHEN LENGTH($1) = 13 THEN
            RPAD(ean13_nl_id($1), 13, '0')
        ELSE $1
    END;
END;
$_$;
```

What do these functions do? Let's find out:

```sql
SELECT
    ean,
    ean13_nl_id_length(ean) AS id_length,
    ean13_nl_id(ean) AS id,
    ean13_nl_normalize(ean) AS normalized
  FROM UNNEST(ARRAY['1234', '12345', '0000000000000', '2201234567890', '2301234567890']) ean;
--- => ean              id_length  id               normalized
--- => '1234'           4          '1234'           '1234'
--- => '12345'          5          '12345'          '12345'
--- => '0000000000000'  13         '0000000000000'  '0000000000000'
--- => '2201234567890'  6          '220123'         '2201230000000'
--- => '2301234567890'  7          '2301234'        '2301234000000'
```

## The `ean13_nl` data type

In PostgreSQL, one can define a new data type (which is called a `DOMAIN`), and place restrictions on
its contents. This references the last function we just created:

```sql
CREATE DOMAIN ean13_nl AS text
	CONSTRAINT ean13_nl_check CHECK ((VALUE = ean13_nl_normalize(VALUE)));
```

## Setup a sample database

Let's put it to use in a table:

```sql
CREATE TABLE barcodes (barcode ean13_nl PRIMARY KEY, name VARCHAR);
INSERT INTO barcodes VALUES
  (ean13_nl_normalize('8712439020109'), 'Jori Pindakaas 350g'),
  (ean13_nl_normalize('8713576100129'), 'TerraSana Pindakaas 250g'),
  (ean13_nl_normalize('2164941000227'), 'EkoPlaza Appel Elstar'),
  (ean13_nl_normalize('2232072000000'), 'Jumbo Jonagold'),
  (ean13_nl_normalize('2232140001472'), 'Jumbo Elstar Appels'),
  (ean13_nl_normalize('125645'),        'Jumbo Appel Jonagold');
```

Let's have a look at what's in the table now:

```sql
SELECT * FROM barcodes`;
--- => '8712439020109'  'Jori Pindakaas 350g'
--- => '8713576100129'  'TerraSana Pindakaas 250g'
--- => '2164940000000'  'EkoPlaza Appel Elstar'
--- => '2232070000000'  'Jumbo Jonagold'
--- => '2232140000000'  'Jumbo Elstar Appels'
--- => '125645'         'Jumbo Appel Jonagold'
```

Note that it isn't possible to insert a non-normalized barcode, which helps to
maintain consistency:

```sql
INSERT INTO barcodes VALUES ('2164941000238', 'Foo');
--- ERROR:  value for domain ean13_nl violates check constraint "ean13_nl_check"
```

## Find by barcode

Just make sure to feed each barcode through the `ean13_nl_normalize` function:

```sql
SELECT name FROM barcodes WHERE barcode = ean13_nl_normalize('2232140001481');
--- => 'Jumbo Elstar Appels'
```

One can also join by barcode:

```sql
SELECT a.* FROM barcodes a
INNER JOIN
  UNNEST(ARRAY['8712439020109', '2232140001481', '21987']) b
  ON a.barcode = ean13_nl_normalize(b);
--- => '8712439020109'  'Jori Pindakaas 350g'
--- => '2232140001472'  'Jumbo Elstar Appels'
```

## Finding multiple barcodes

To make it just a bit easier to find multiple barcodes, one can create another function:

```sql
--- normalized barcodes
CREATE FUNCTION ean13_nl_normalize(text[]) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $_$
BEGIN
    RETURN ARRAY(SELECT DISTINCT ean13_nl_normalize(g.i) FROM unnest($1) g(i));
END;
$_$;
```

This can be used to search for multiple barcodes:

```sql
SELECT * FROM barcodes
WHERE barcode = ANY(ean13_nl_normalize(ARRAY['8712439020109', '2232140001481', '21987']));
--- => '8712439020109'  'Jori Pindakaas 350g'
--- => '2232140001472'  'Jumbo Elstar Appels'
```

This may be slightly easier in complex queries.
