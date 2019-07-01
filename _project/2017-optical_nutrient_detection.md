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

Covering all cases is likely to be very complicated. Let's start with the basics
first, as long as there is a substantial portion of real-world pictures that can be
recognized.

### Finding the spot

Many photos contain a product held by someone, and we're only interested in the nutrient
table. First step will be to find where the nutrient table is in the image. This might
be done by object detection techniques, keeping in mind that there are several forms of
the nutrient table.

Alternatively, one could just identify all text in the image, and find nutrients in there.
Alignment is important here, as there may be multiple columns with different values for
e.g. 100g and portion.

### Technology

We prefer to use open source software, because it is better maintainable, but quality
and performance is at least as important.

### Training data

There are pictures available of at least 10k products, including structured nutrient tables
(which may or may not be literally what's being displayed, but should be close). This could
be a training set for machine learning. There is currently no labeling of which images are
showing what part of the product, or points/areas of interest. This could, of course, be
done for a subset.

## Existing work

* [Nutriscanner](https://youtu.be/WgNRjYHQs0g?t=32) is an old iOS app doing nutrient table OCR. Pretty basic.
* NutriSnap mobile app ([old](https://vimeo.com/159855857) and [new](https://vimeo.com/233983078) video;
  [initial funding](https://www.sbir.gov/sbirsearch/detail/1008737);
  [trademark](https://trademarks.justia.com/876/81/nutrisnap-87681393.html)).
* OpenFoodFacts has [plans for OCR](https://en.wiki.openfoodfacts.org/OCR/Roadmap).
  - they already have [nutrient table detection](https://github.com/tensorflow/models/tree/master/research/object_detection)
  - based on TensorFlow's [object detection model](https://github.com/tensorflow/models/tree/master/research/object_detection)
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

### Commercial

Some commercial solutions and companies who've done similar things before:
- [Microblink](https://www.microblink.com/) - real-time text recognition for mobile apps. _Nutritional information scanning_ mentioned.
- [Anyline](https://www.anyline.com/) - mobile OCR SDK.
- [OCR at Cloudfactory](https://www.cloudfactory.com/machine-learning/optical-character-recognition-ocr) - provides service combining OCR with human checks if needed.
- [ABBYY FlexiCapture](https://www.abbyy.com/flexicapture/) - enterprise-level image capture and processing.
- [Virtronic](https://www.vitronic.com/industrial-and-logistics-automation/applications/optical-character-recognition-ocr.html) - industrial machine vision company.
- [ExperVision](http://www.expervision.com/find-ocr-software-by-document-types/ocr-software-for-label-processing-1) - OCR company, has done food label recognition before.
- [SRI](https://www.sri.com/research-development/computer-vision)
- [Focal Systems](https://focal.systems/solutions) also does computer vision consulting.
- [Abto Computer Vision](https://www.abtosoftware.com/computer-vision-and-image-processing-solutions)
- [Kitware Computer Vision](https://www.kitware.com/computer-vision/) (though focus seems to be on video)
- [Vision++](http://visionplusplus.com/)

### Higher education (NL)

- [Advanced School for Computing and Imaging](http://www.asci.tudelft.nl/pages/about-asci.php), graduate school by multiple universities.
- [TUDelft Computer Vision Lab](https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/intelligent-systems/pattern-recognition-bioinformatics/computer-vision-lab/)
- [University of Amsterdam Computer Vision](https://ivi.fnwi.uva.nl/cv/) (plus [prof. dr. Gavrila](http://www.gavrila.net/))
- [CWI Computation Imaging](https://www.cwi.nl/research/groups/computational-imaging), focused on 3D (but might still be relevant).
- [TNO](http://www.tno.nl/) should do related things, but the website is not very informative.
- [NL eScience Center Computer Vision](https://www.esciencecenter.nl/technology/expertise/computer-vision) (though not much deep learning yet).
- [Gamera](http://gamera.informatik.hsnr.de/) developers (though probably too archive-centered instead of mobile camera pictures).

It is also interesting to look at partners of vision-companies that do something tangential, like [VicarVision](http://www.vicarvision.nl/about/partners/), [EagleVision](https://www.eaglevision.nl/index.php/projects-and-partners.html).

### Other links

- [Awesome OCR](https://github.com/kba/awesome-ocr) - links to awesome OCR projects.
- [Computer Vision companies](http://www.lengrand.fr/computer-vision-companies/) in Europe.

