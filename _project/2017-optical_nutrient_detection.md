---
layout: project
title: Reading nutritional tables from food product photos
priority: 5
status: open
contact: wvengen
---
{% include JB/setup %}

To be able to rate a product on health and on sustainability, knowing basic information
present on a food product's package is a first step. Some of this information we can find
online, but not all. Users of the [Questionmark app](://www.thequestionmark.org/download)
submit photos of products they want to see included, and there are other products for which
our only source of information is the product itself, or a photo of it.

Some manual work on verification, and entering hard-to-read packages will probably always
be needed, but the bulk of the work should be possible to automate. With the use of
[OCR](https://en.wikipedia.org/wiki/Optical_character_recognition), a list of nutrients
and their values may be extracted from a bare photo. With a clear picture containing only
a nutrients table, this is relatively easy (something we're
[already doing](https://github.com/q-m/rabbiteye-exp/tree/master/nutrient-ocr-tesseract)),
but with all photos taken in many different lighting conditions, of many different product
shapes, having different nutrient tables appearances, taken by a variety of mobile camera's,
this is a much more difficult task.

## Goal

_Extract structured nutritional tables from photos of food products._

* Photos may be taken by a variety of (mobile phone) camera's under varying conditions.
* The photo contains the product, but possibly also a hand, a table, a kitchen,
  or the inside of a supermarket.
* The nutrient tables come in different, but probably a limited set of forms and shapes
  (sometimes with a border around it, sometimes just free-flowing text, sometimes a table without borders, etc.).
* The language is primarily Dutch (though additional languages may be present).

## Considerations

### Offline vs. interactive

Preferably detection can be done offline, including on photos previously taken. But
sometimes photos aren't clear enough, or could be clearer for better accuracy. Having
detection integrated into the mobile app that takes pictures, would allow the detection
algorithm to tell when the photo is good enough, or when a new photo should be taken.
Both options would be acceptable.

### Presence detection

Generally, we don't know for sure if a photo contains a nutrient table or not. Ideally
OCR would tell whether the photo contains it or not. It is possible to provide a hint
on which of a series of photos contains a full nutrient table, but even if we ask users,
the hint will not be 100% perfect.

### Varying conditions

Many photos are products of products held in the hand, or lying on a table. There may
be a background of a supermarket, a kitchen, or a smiling person. Maybe there are
other, more vaguely visible, products in the background.

The packaging may be curved (a bottle, a can) or wrinkled (cookies, a bag of crisps).
Lighting conditions can vary a lot, including uneven lighting.

Covering all cases is most probably very complicated. Let's start with the basics
first, as long as there is a substantial portion of real-word pictures that can be
recognized.

### Finding the spot

Many photos contain a product held by someone, and we're only interested in the nutrient
table. First step will be to find where the nutrient table is in the image. This might
be done by object detection techniques, keeping in mind that there are several forms of
the nutrient table.

Alternatively, one could just identify all text in the image, and find nutrients in there.
Alignment is important here, as there may be multiple columns with different values for
e.g. 100g and portion.


## Existing work

* [Nutriscanner](https://youtu.be/WgNRjYHQs0g?t=32) is an old iOS app doing nutrient table OCR. Pretty basic.
* NutriSnap mobile app ([old](https://vimeo.com/159855857) and [new](https://vimeo.com/233983078) video;
  [initial funding](https://www.sbir.gov/sbirsearch/detail/1008737);
  [trademark](https://trademarks.justia.com/876/81/nutrisnap-87681393.html)).
* OpenFoodFacts has [plans for OCR](https://en.wiki.openfoodfacts.org/OCR/Roadmap).
* Some other people [who built similar apps](https://dsp.stackexchange.com/questions/2433/nutrition-facts-label-ocr).
  Takeaways:
  - can use Tesseract, or something like [ABBYY](http://www.wisetrend.com/abbyy_flexicapture.shtml)
  - user training and guidance important for clear images: garbage in, garbage out
* [_Automatic Nutritional Information Extraction from Photographic Images of Labels_](https://repositorio-aberto.up.pt/bitstream/10216/83493/2/35406.pdf), technical Master's thesis.
  - example pictures of some nutritional tables (Appendix A), and how to process them
  - algorithms for all relevant steps
  - final accuracy 55% (cf. 20% for just Tesseract)
* [_Recognition of Nutrition Facts Labels from Mobile Images_](https://stacks.stanford.edu/file/druid:bf950qp8995/Grubert_Gao.pdf), technical article. Final accuracy 64%.
* [_Vision Based Extraction of Nutrition Information from Skewed Nutrition Labels_](https://digitalcommons.usu.edu/cgi/viewcontent.cgi?referer=&httpsredir=1&article=5916&context=etd), technical thesis (related to barcode-based [NutriGlass](https://play.google.com/store/apps/details?id=org.vkedco.mobappdev.nutriglass) mobile app).
* [_Image processing for the extraction of nutritional information from food labels_](https://scholarcommons.scu.edu/cseng_senior/42/), bachelor's thesis, with [code](https://github.com/Rsullivan00/labelRecognizer). Accuracy of each step 60-80%.
* [_Potential OCR Software for Nutrition Facts Labels_](http://swhig.web.unc.edu/files/2012/06/Potential-OCRs-for-Nutrition-Facts-Labels.pptx) short presentation evaluating different OCR software options for nutrient recognition.

## Who may be able to provide this?

- https://www.microblink.com/
- https://www.vitronic.com/industrial-and-logistics-automation/applications/optical-character-recognition-ocr.html
- https://www.cloudfactory.com/machine-learning/optical-character-recognition-ocr
- http://www.wisetrend.com/abbyy_flexicapture.shtml
- https://www.anyline.io/
- http://www.expervision.com/find-ocr-software-by-document-types/ocr-software-for-label-processing-1
- ...

