---
layout: project
title: Troublesome barcodes
priority: 28
status: open
contact: wvengen
---
{% include JB/setup %}


With the [Questionmark app](://www.thequestionmark.org/download) you can scan a barcode of food
a food product, and see sustainability and health information. Scanning a barcode works fine in
many cases, but sometimes it doesn't work reliably.

We currently don't have a focus on improving this, but it would still be nice to have.
Not only would this help users of our app, but it may also improve barcode reading in general,
e.g. by submitting a patch to an open source project.

Note that Google ML Kit has an (offline) [barcode scanner](https://firebase.google.com/docs/ml-kit/read-barcodes)
that may suffice already. Or at the very least, it would be something to start from.


# Issues

We started off using the widely used [ZXing](https://github.com/zxing/zxing) barcode scanner library.
This worked mostly fine, but it appeared that [Scandit](http://www.scandit.com/) performed a bit better.
Nevertheless, problems remain. When are barcodes troublesome to scan?

- Unsharp images (e.g. because of bad phone cameras, or focussing issues)
- Curved surfaces (bottles and cans, or a sticker with a bend)
- Low lighting conditions (in the fridge or at night)
- Lighting gradient (lamp on one side of the room)

These are the most important reasons. Others may be low depth of field, or stickers with wrinkles, and
probably many more.

While some of them may be hard to tackle, I think that sensitivity can be improved. How?


## Curved surfaces

Some ideas:
- Detect lines using a [Hough transform](https://en.wikipedia.org/wiki/Hough_transform) of curves, and transform barcode to a rectangle.
- Locate corners using feature detection on the image, find curvature parameter and straighten lines.

There's also a lot of existing research, for example at [semanticscholar.org](https://www.semanticscholar.org/search?facets%5BfieldOfStudy%5D%5B%5D=Computer%20Science&q=ean%20barcode&sort=relevance&ae=false). I wonder if this is actually applied in the scanner libraries we used.


## Lighting gradient

It is possible to detect gradients and compensate for them.


## Low lighting conditions

This often results in low contrast and unsharp images. Low contrast might be improved by increasing
exposure time, or digitally, by combining multiple images.

I'd consider this the least important, because one can usually turn on a light easily. As a user of
the app, other issues are probably a lot harder to tackle.


# Links

- [Reconstruct argorithm of 2D barcode for reading the QR code on cylindrical surface](https://doi.org/10.1109/ICASID.2013.6825309)
- "Scanning barcode on a curved surface" [thread](http://git.net/ml/zxing/2014-08/threads.html) on ZXing mailing list
- [Grouping Curved Lines](https://www.semanticscholar.org/paper/Grouping-Curved-Lines-Rosin/0972a19f23cff9873409ae7fbf2492624f4f0ded)
- [Barcode Readers using the Camera Device in Mobile Phones](https://www.semanticscholar.org/paper/Barcode-Readers-using-the-Camera-Device-in-Mobile-Ohbuchi-Hanaizumi/9a0353a97717dbde7d832702c9e038af0e406480)
- [Real-Time Barcode Detection in the Wild](https://www.semanticscholar.org/paper/Real-Time-Barcode-Detection-in-the-Wild-Creusot-Munawar/cacd53e60a9b713cf71df842c18a8c14859e1c36)
