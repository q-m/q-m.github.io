---
layout: post
title: Free-form select2 with existing values
author: wvengen
tags: [javascript, select2]
image: https://gist.github.com/wvengen/be89a2f8bfec7c038084/raw/2f458f9d423307fa63912f4d8cd51896c07d5fdf/select2-freeform.png
---
{% include JB/setup %}

In our backend, we're heavily relying on [select2](http://select2.github.io/select2/)
for choosing values from a list in forms. Sometimes we want to show a list of
existing values, but still allow the user to add his own. This can easily
be done like this:

{% include JB/gist gist_id="be89a2f8bfec7c038084" gist_file="select2_freeform.js" %}

In our ingredient edit form it looks like this:

<img src="https://gist.github.com/wvengen/be89a2f8bfec7c038084/raw/2f458f9d423307fa63912f4d8cd51896c07d5fdf/select2-freeform.png" style="width: 100%" alt="screenshot" />
