---
layout: post
title: Finding a Ruby memory leak using time analysis
author: wvengen
tags: [ruby, debugging, data]
image: https://cloud.githubusercontent.com/assets/503804/11392637/56f47762-935b-11e5-8122-a7bfd16cbec8.png
teaser: 'When developing a program in Ruby, you may sometimes encounter a memory leak. For a while now, Ruby has a facility to gather information about what objects are laying around: ObjectSpace.'
---
{% include JB/setup %}

{% gist f1097651c238b2f7f11d README.md %}

See the code in [this gist](https://gist.github.com/wvengen/f1097651c238b2f7f11d).
