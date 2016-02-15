---
layout: post
title: Reading CSVs from Excel within Ruby
author: wvengen
tags: [ruby, excel, data]
image: https://upload.wikimedia.org/wikipedia/commons/8/86/Microsoft_Excel_2013_logo.svg
---
{% include JB/setup %}

Again and again I hear someone explain about how they manage data and notice that somewhere spreadsheets
play an important role. Very often, that's [Microsoft Excel](https://en.wikipedia.org/wiki/Microsoft_Excel).
From big companies to small organisations like ours. And so it's surprising that it's such a hassle to
reliable export data for use in other tools.

What would be the most logical format to export to?
[Comma separated values](https://en.wikipedia.org/wiki/Comma-separated_values) (CSV),
with [UTF-8](https://en.wikipedia.org/wiki/UTF-8) encoding.
As field-separator preferably a comma (what's in a name), but a semicolon is also acceptable.
And as row-separator a [CRLF](https://en.wikipedia.org/wiki/Newline) (so that Windows users can open it in a text editor).

But, unfortunately, this option is not available in Excel, and hasn't been for all those years.
There is a meagre selection of relevant export options, with either _CSV_ or _Text_ (which means tab-separated),
and for encodings _Windows_, _ASCII_, and _Unicode_. Only the last supports all characters. It
appears to be UTF16-LE with a [BOM](https://en.wikipedia.org/wiki/Byte_order_mark) (phew, at least that).

To be precise: export the sheet as _UTF-16 Unicode Text (*.txt)_ in Excel.

## Reading in Ruby

Importing this file in Ruby, e.g. to populate or update a database, happens like this:

```ruby
require 'csv'

CSV.foreach("sheet.txt", col_sep: "\t", row_sep: "\r\n", encoding: "bom|utf-16le:utf-8") do |row|
  # do something
  puts row.inspect
end
```

Hopefully we now have found a way to handle data from Excel spreadsheets properly.

