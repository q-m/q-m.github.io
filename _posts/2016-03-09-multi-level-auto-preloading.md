---
layout: post
title: Multi-level auto eager loading
author: wvengen
tags: [ruby]
image: /assets/ruby_on_rails_a.png
---
{% include JB/setup %}

Active Record is great. Being able to split up large SQL queries into meaningful bits,
and traversing relations with ease is invaluable. Yet some discipline remains needed.
Using [eager loading](http://guides.rubyonrails.org/active_record_querying.html#eager-loading-associations)
to avoid N+1 queries, to name something well-known to any Rails developer who
has some real-world experience.

For smaller projects, this is usually fine: the controller does the preloading, all set.
But when it grows, and more and more functionality is moved to concerns and other places,
it's not so straightforward anymore which associations are required. Now the controller
needs to know _all_ tables that are referenced from all methods called down the line.


## ActiveRecord's over-eagerness

Adding an [includes](http://api.rubyonrails.org/classes/ActiveRecord/QueryMethods.html#method-i-includes)
to a [relation](http://api.rubyonrails.org/classes/ActiveRecord/Relation.html) always
does a database call, you know.

To show this, consider a product model with nutritional info:

```ruby
class Product < ActiveRecord::Base
  has_many :product_nutrients, dependent: :destroy, inverse_of: :product
  has_many :nutrients, through: :product_nutrients
end

class ProductNutrient < ActiveRecord::Base
  belongs_to :product
  belongs_to :nutrient
  belongs_to :nutrient_unit
  validates :product, presence: true
  validates :nutrient, presence: true
  validates :nutrient_unit, presence: true
  validates :value, presence: true, numericality: { greater_than_or_equal_to: 0 }
end

class Nutrient < ActiveRecord::Base
  has_many :product_nutrients, dependent: :restrict_with_error
  has_many :products, through: :product_nutrients
  validates :name, presence: true, uniqueness: { case_sensitive: false }
end

class NutrientUnit < ActiveRecord::Base
  has_many :product_nutrients, dependent: :restrict_with_error
  validates :name, presence: true, uniqueness: { case_sensitive: false }
end
```

ActiveRecord understands that referencing the `Product.product_nutrients` association twice
yields the same result, and does just one database call. But if we add `includes(:nutrient)`,
it's different.

```ruby
p = Product.find(...);
# Product Load (1.4ms)  SELECT  "products".* FROM "products" WHERE "products"."id" = $1 LIMIT 1

p.product_nutrients.to_a; p.product_nutrients.to_a;
# ProductNutrient Load (1.0ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" = $1

p.product_nutrients.includes(:nutrient).to_a; p.product_nutrients.includes(:nutrient).to_a;
# ProductNutrient Load (0.5ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" = $1
# Nutrient Load (0.4ms)  SELECT "nutrients".* FROM "nutrients" WHERE "nutrients"."id" IN (...)
# ProductNutrient Load (0.3ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" = $1
# Nutrient Load (0.3ms)  SELECT "nutrients".* FROM "nutrients" WHERE "nutrients"."id" IN (...)
```

There's probably some good reason for this behaviour, but it's pretty annoying.


## A workaround

In the product model, we have a method to check if all basic ingredients are there. If not,
the data we have is most probably incorrect - in all but some corner-cases manufacturers need
to specify saturated fat, energy and salt or natrium. And on some places this has consequences
for our data pipeline.

```ruby
class Product
  def has_basic_nutrients?
    codes = product_nutrients.map {|pn| pn.nutrient.code }.compact.uniq
    codes.include?('energy') &&
      codes.include?('fat_saturated') &&
      (codes.include?('salt') || codes.include?('natrium'))
  end
end
```

Sounds easy enough, right? But for one thing: all methods that call this method, need to know
to eager load both `product_nutrients` and `nutrients`. That's inconvenient, since in many
cases this is only called for a single product, and `#has_basic_nutrients?` could just eager
load it by itself when needed.


### Single-level

This works by default. For querying multiple products, you can preload explicitely, while
for a single product, ActiveRecord already loads the whole array at once. Great!

But that's not enough for our case: we don't only look at `product_nutrients`, but also its
association `nutrient`.


### Dual-level

That's where ActiveRecord breaks down, unfortunately. So make it somewhat managable in our
codebase (to avoid needing eager loading in all code-paths to `Product#has_basic_nutrients?`),
we check whether the association is loaded, as well as all nutrients are loaded.

```ruby
class Product
  def has_basic_nutrients?
    # hack to avoid all callers needing to know about preloading
    scope = product_nutrients
    if !scope.loaded? || scope.any? {|pn| !pn.association(:nutrient).loaded? }
      scope = scope.includes(:nutrient)
    end

    codes = scope.map {|pn| pn.nutrient.code }.uniq
    codes.include?('energy') &&
      codes.include?('fat_saturated') &&
      (codes.include?('salt') || codes.include?('natrium'))
  end
end
```

If `product_nutrients` aren't loaded at all, we need to load them anyway - and we just
as well include the nutrients too. If `product_nutrients` are loaded, we need to check
if nutrients are loaded. This is needed for _each_ `product_nutrient`, and I'm afraid
we need to iterate them all (assuming database calls are more expensive then this).

While ActiveRecord [relations](http://api.rubyonrails.org/classes/ActiveRecord/Relation.html)
have a `#loaded?` method, this is not the case for a `belongs_to` or `has_one` relation,
and so we use the [association](http://api.rubyonrails.org/classes/ActiveRecord/Associations/ClassMethods.html#module-ActiveRecord::Associations::ClassMethods-label-Association+extensions) method instead.

And does it work?

```ruby
p = Product.includes(:product_nutrients => :nutrient).find(...)
# Product Load (0.7ms)  SELECT  "products".* FROM "products" WHERE "products"."id" = $1 LIMIT 1
# ProductNutrient Load (0.6ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" IN (.)
# Nutrient Load (0.3ms)  SELECT "nutrients".* FROM "nutrients" WHERE "nutrients"."id" IN (...)
p.has_basic_nutrients?
=> false

p = Product.find(...)
# Product Load (1.4ms)  SELECT  "products".* FROM "products" WHERE "products"."id" = $1 LIMIT 1
p.has_basic_nutrients?
# ProductNutrient Load (0.8ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" = $1
# Nutrient Load (0.4ms)  SELECT "nutrients".* FROM "nutrients" WHERE "nutrients"."id" IN (...)
=> false
``` 

Yes, it eager loads correctly, both when specified explicitely at product-load and when
that is omitted.

Unfortunately, calling the method twice without eager loading does not keep the data :(

```ruby
p.has_basic_nutrients?
# ProductNutrient Load (0.8ms)  SELECT "product_nutrients".* FROM "product_nutrients" WHERE "product_nutrients"."product_id" = $1
# Nutrient Load (0.4ms)  SELECT "nutrients".* FROM "nutrients" WHERE "nutrients"."id" IN (...)
=> false
```

But for now, we're reasonably happy.

