---
layout: post
title: PostgreSQL FDW and custom domains
author: wvengen
tags: [data, postgresql]
image: /assets/postgresql.png
---
We are using [PostgreSQL](https://www.postgresql.org/) as a database, with much success.
Two of our main datastores are one containing raw product data and another processed product
data. Usually this separation holds well, but there are times we'd like to lay them side by side.

[PostgreSQL FDW](https://www.postgresql.org/docs/current/postgres-fdw.html) allows querying
external data sources from within the database. We use it to connect from the processed to the
raw database. In these cases there is a limited list of products we'd like to inspect, augmenting
it with raw data.

## A basic example

This worked fairly well in many cases. To illustrate, I'll give a small example. We assume
that you have created the databases `sources` and `products` and have superuser privileges.
In this example we'll have one database server with two databases, in reality these would
be on different physical servers.

```sql
-- populate the sources database
\c sources
CREATE TABLE sources (id INTEGER, source VARCHAR, barcode VARCHAR, name VARCHAR);
INSERT INTO sources VALUES
  (1002, 'Retailer A', '2162130000000', 'Pumpkin (whole)'),
  (1003, 'Retailer B', '2162130000000', 'Pumpkin'),
  (1004, 'Retailer A', '8718452095551', 'Cake'),
  (1005, 'Retailer C', '8718452095551', 'Farmer cake'),
  (1006, 'Retailer B', '8719326012759', 'Coffee'),
  (1007, 'Retailer C', '8719326012759', 'Holy beans');

-- populate the products database
\c products
CREATE TABLE products (id INTEGER, barcode VARCHAR, name VARCHAR);
INSERT INTO products VALUES
  (1, '2162130000000', 'Pumpkin'),
  (2, '8718452095551', 'Farmer''s Cake'),
  (3, '8719326012759', 'Holy beans coffee');
```

Now that the tables are set up and have some data, we can query them separately.

```sql
\c sources
SELECT * FROM sources WHERE barcode = '8718452095551';
```
```
┌──────┬────────────┬───────────────┬─────────────┐
│  id  │   source   │    barcode    │    name     │
├──────┼────────────┼───────────────┼─────────────┤
│ 1004 │ Retailer A │ 8718452095551 │ Cake        │
│ 1005 │ Retailer C │ 8718452095551 │ Farmer cake │
└──────┴────────────┴───────────────┴─────────────┘
```
```sql
\c products
SELECT * FROM products WHERE barcode = '8718452095551';
```
```
┌────┬───────────────┬───────────────┐
│ id │    barcode    │     name      │
├────┼───────────────┼───────────────┤
│  2 │ 8718452095551 │ Farmer's Cake │
└────┴───────────────┴───────────────┘
```

## A federated database connection

At this moment, the two databases can be queried separately. But we also want to put
data of both side by side. For that, we setup a federated database connection.

```sql
\c sources
CREATE USER sources_user PASSWORD 'test321';
GRANT ALL ON TABLE sources TO sources_user;

\c products
CREATE EXTENSION postgres_fdw;
CREATE SERVER sources_fdw FOREIGN DATA WRAPPER postgres_fdw OPTIONS (dbname 'sources', host 'localhost', port '5432');
CREATE USER MAPPING FOR USER SERVER sources_fdw OPTIONS (user 'sources_user', password 'test321');

CREATE SCHEMA sources_fdw;
IMPORT FOREIGN SCHEMA public FROM SERVER sources_fdw INTO sources_fdw;
```

Let's see if we can query the sources from the products database. Note that we do the queries
on the `sources_fdw` schema, because we've `IMPORT`ed the foreign tables in that schema above.

```sql
\c products
SELECT * FROM sources_fdw.sources WHERE barcode = '8718452095551';
```
```
┌──────┬────────────┬───────────────┬─────────────┐
│  id  │   source   │    barcode    │    name     │
├──────┼────────────┼───────────────┼─────────────┤
│ 1004 │ Retailer A │ 8718452095551 │ Cake        │
│ 1005 │ Retailer C │ 8718452095551 │ Farmer cake │
└──────┴────────────┴───────────────┴─────────────┘
```

That looks good. Let's check out the query plan for this:

```sql
\c products
EXPLAIN VERBOSE SELECT * FROM sources_fdw.sources WHERE barcode = '8718452095551';
```
```
Foreign Scan on sources_fdw.sources  (cost=100.00..118.31 rows=3 width=100)                                  
  Output: id, source, barcode, name                                                                          
  Remote SQL: SELECT id, source, barcode, name FROM public.sources WHERE ((barcode = '8718452095551'::text)) 
```

You can see that the query is executed completely on the `sources` database (remote).

The best part is that we can now `JOIN` data between tables in the different databases.

```sql
\c products
SELECT p.id, p.barcode, p.name, s.source, s.name AS source_name
FROM products p
LEFT JOIN sources_fdw.sources s ON s.barcode = p.barcode
WHERE p.id = 2;
```
```
┌────┬───────────────┬───────────────┬────────────┬─────────────┐
│ id │    barcode    │     name      │   source   │ source_name │
├────┼───────────────┼───────────────┼────────────┼─────────────┤
│  2 │ 8718452095551 │ Farmer's Cake │ Retailer A │ Cake        │
│  2 │ 8718452095551 │ Farmer's Cake │ Retailer C │ Farmer cake │
└────┴───────────────┴───────────────┴────────────┴─────────────┘
```

Looking again at the query plan, you can see that data is combined from both databases.

```sql
\c products
EXPLAIN VERBOSE SELECT p.id, p.barcode, p.name, s.source, s.name AS source_name
FROM products p
LEFT JOIN sources_fdw.sources s ON s.barcode = p.barcode
WHERE p.barcode = '8718452095551';
```
```
Nested Loop Left Join  (cost=100.00..139.40 rows=12 width=132)                                                        
  Output: p.id, p.barcode, p.name, s.source, s.name                                                                   
  Join Filter: ((s.barcode)::text = (p.barcode)::text)                                                                
  ->  Seq Scan on public.products p  (cost=0.00..20.62 rows=4 width=68)                                               
        Output: p.id, p.barcode, p.name                                                                               
        Filter: ((p.barcode)::text = '8718452095551 '::text)                                                          
  ->  Materialize  (cost=100.00..118.60 rows=3 width=96)                                                              
        Output: s.source, s.name, s.barcode                                                                           
        ->  Foreign Scan on sources_fdw.sources s  (cost=100.00..118.59 rows=3 width=96)                              
              Output: s.source, s.name, s.barcode                                                                     
              Remote SQL: SELECT source, barcode, name FROM public.sources WHERE ((barcode = '8718452095551 '::text)) 
```


## Entering a custom domain

So far, so good. Now we'd like to add a check to the `barcode`, so that we can only store valid
barcodes in the database. [Domain types](https://www.postgresql.org/docs/current/domains.html) are great for that.
For this example, we'll require the length to be 8 or longer (in reality one may want to verify the check digit,
and [normalize it a bit](/2017/02/13/storing-barcodes)). We'll add the check both to the `sources` and the `products`
database.

```sql
\c sources
CREATE DOMAIN barcode AS VARCHAR CHECK (CHAR_LENGTH(TRIM (LEADING '0' FROM VALUE)) >= 8);
ALTER TABLE sources ALTER COLUMN barcode TYPE barcode;

\c products
CREATE DOMAIN barcode AS VARCHAR CHECK (CHAR_LENGTH(TRIM (LEADING '0' FROM VALUE)) >= 8);
ALTER TABLE products ALTER COLUMN barcode TYPE barcode;

-- we also need to update the remote table definition
DROP FOREIGN TABLE sources_fdw.sources;
IMPORT FOREIGN SCHEMA public FROM SERVER sources_fdw INTO sources_fdw;
```

Now this doesn't really change anything, except that short barcodes cannot be inserted anymore. Let's see ...
```sql
\c sources
INSERT INTO sources VALUES (1008, 'Retailer A', '234', 'Dummy');
```
```
ERROR:  value for domain barcode violates check constraint "barcode_check"
```

The same would happen in `products`. Now let's see how remote queries are doing.

```sql
\c products
SELECT * FROM sources_fdw.sources WHERE barcode = '8718452095551';
```
```
┌──────┬────────────┬───────────────┬─────────────┐
│  id  │   source   │    barcode    │    name     │
├──────┼────────────┼───────────────┼─────────────┤
│ 1004 │ Retailer A │ 8718452095551 │ Cake        │
│ 1005 │ Retailer C │ 8718452095551 │ Farmer cake │
└──────┴────────────┴───────────────┴─────────────┘
```

Same results, nothing changed. But how does the database get this data?

```sql
\c products
EXPLAIN VERBOSE SELECT * FROM sources_fdw.sources WHERE barcode = '8718452095551';
```
```
Foreign Scan on sources_fdw.sources  (cost=100.00..130.25 rows=3 width=100)
  Output: id, source, barcode, name                                        
  Filter: ((sources.barcode)::text = '8718452095551'::text)                
  Remote SQL: SELECT id, source, barcode, name FROM public.sources         
```

As you see, there is now an explicit filtering step. And in _Remote SQL_ you can see
that all data in the `sources` table is requested. With just a couple of records, this
isn't noticable, but on a real-world dataset, this can mean millions of records. And in
the end only a handful of rows remain after the filter. This is very inefficient, and
most queries will timeout before any result is returned.

So even though the `barcode` domain type is really nothing more than a `VARCHAR`,
PostgreSQL doesn't know, and takes the safe approach of doing the filtering locally.


## Possible solutions

The ultimate solution would be to have PostgreSQL recognize that filtering on the remote
domain can well be done. But that would take a while to implement. And perhaps there are
cases that I haven't considered that make it undesirable after all.

One peculiar thing is that when you don't re-`IMPORT FOREIGN SCHEMA` after changing
the data type, PostgreSQL still thinks it's an ordinary `VARCHAR` column, and will
do the right thing. So one solution could be to manually `CREATE FOREIGN TABLE` and
use `VARCHAR` instead of `barcode` for the data type. This requires keeping the
definitions manually in sync.

Another solution would be to create a `VIEW` on the remote database (`sources`) that
exposes the table without the custom domain. That's the approach we're currently using.
Since we need to run a script to update federated connection details now and then anyway,
we can just as well create a remote schema with un-domain-type-ed views of the relevant
tables right away, and use these as remote tables.

Since we want all columns of the `sources` table _except_ `barcodes`, we first run
a query resulting a single row with a SQL-statement, then execute it with `\gexec`
(using the PostgreSQL CLI tool).

```sql
\c sources
CREATE SCHEMA IF NOT EXISTS expose_fdw;
SELECT
  'CREATE OR REPLACE VIEW expose_fdw.sources AS (SELECT '
  || (
       SELECT STRING_AGG(column_name, ',' ORDER BY ordinal_position)
       FROM information_schema.columns
       WHERE table_schema = 'public' AND table_name = 'sources' AND column_name != 'barcode'
     )
  || ', barcode::varchar FROM public.sources)';
\gexec
```

And then in the `products` database, we import from the `expose_fdw` schema instead of `public`.

```sql
\c products
DROP FOREIGN TABLE sources_fdw.sources;
IMPORT FOREIGN SCHEMA expose_fdw FROM SERVER sources_fdw INTO sources_fdw;

EXPLAIN VERBOSE SELECT * FROM sources_fdw.sources WHERE barcode = '8718452095551';
```
```
Foreign Scan on sources_fdw.sources  (cost=100.00..118.31 rows=3 width=100)                                     
  Output: id, source, name, barcode                                                                             
  Remote SQL: SELECT id, source, name, barcode FROM expose_fdw.sources WHERE ((barcode = '8718452095551'::text))
```

Indeed, the barcode filtering happens in the `sources` database, which is where it is done much more efficiently.
