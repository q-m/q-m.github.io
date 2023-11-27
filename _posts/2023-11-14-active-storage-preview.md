---
layout: post
title: Direct previews with Active Storage
author: wvengen
tags: [ruby]
image: https://upload.wikimedia.org/wikipedia/commons/6/62/Ruby\_On\_Rails\_Logo.svg
---
{% include JB/setup %}

Nowadays [Ruby on Rails](https://rubyonrails.org) includes [Active Storage](https://guides.rubyonrails.org/active_storage_overview.html)
for handling file uploads, including support for direct uploads from the
browser. Recently, we've worked on an application that uses the [Dropzone file upload component](https://dropzone.dev/)
(with the help of [Stimulus](https://stimulus.hotwired.dev) to wire it up).

Until recently, direct previews of movies and PDFs turned out to be a little more involved.
To understand why, we'll first look at how Active Storage enables direct file uploads:

1. The user loads a web page, containing a form with a file element.
2. Dropzone embellishes the form with a more friendly component.
3. The user selects a file to upload.
4. Dropzone shows a preview of the file (when the file is an image and `createImageThumbnails` is `true`).
5. [`DirectUpload`](https://github.com/rails/rails/blob/main/activestorage/app/javascript/activestorage/direct_upload.js) requests an upload URL from the [`DirectUploadsController`](https://api.rubyonrails.org/classes/ActiveStorage/DirectUploadsController.html)
6. `DirectUpload` uploads the selected file.
7. The returned `signed_id` is stored as a hidden input in the form.
8. The user submits the form.
9. The controller stores the record and associates the already uploaded file.

Often, you would want to show an image thumbnail after the form is submitted.
That is [easy enough](https://edgeguides.rubyonrails.org/active_storage_overview.html#displaying-images-videos-and-pdfs)
e.g. with `url_for(file.representation(resize_to_fill: [102, 120]))`. But here
we would like to show the thumbnail in Dropzone, before the server renders
something new. A thumbnail that is generated server-side, which works for non-image
file formats, like movies and PDFs, too.

One way would to be define a custom controller action that returns the thumbnail URL,
and this would be called after the upload is finished. But it feels a bit strange to
do so, since all of Active Storage is built into Rails, but not this. Do we need to
define an extra route just for this?

A simpler way would be to return a thumbnail URL from the `DirectUploadsController`.
Yes, even when the file has not been uploaded yet, a URL can already be generated. So
we created an override for the `DirectUploadsController`.

In the routes, add:

```ruby
# config/routes.rb
Rails.application.routes.draw do
  post "/rails/active_storage/direct_uploads", to: "direct_uploads#create"
  # ...
end
```

then create the custom controller

```ruby
# app/controllers/direct_uploads_controller.rb
class DirectUploadsController < ActiveStorage::DirectUploadsController

  private

  # add thumb_url to response
  def direct_upload_json(blob)
    json = super(blob)
    json[:thumb_url] = url_for(blob.representation({ resize_to_fill: [120, 120] }))
    json
  end
end
```

Then in the code that integrates Dropzone, the returned `thumb_url` can be used
to set the thumbnail:

```javascript
// ...

class DirectUploadController {

  // ...

  start() {
    // ...
    this.directUpload.create((error, attributes) => {
      if (error) {
        // handle error
      } else {
        this.hiddenInput.value = attributes.signed_id;
        this.file.status = Dropzone.SUCCESS;
        this.source.dropZone.emit("success", this.file);
        // this is the new line that adds the server-generated thumbnail
        this.source.dropZone.emit("thumbnail", this.file, attributes.thumb_url);
        this.source.dropZone.emit("complete", this.file);
      }
    });
  }

  // ...
}
```

And so we have server-generated thumbnails, including for movies and PDFs
(which the browser can't do).


## Later addition: using named variants

Since Rails 7.0, Active Storage allows using named variants. This has the
benefit of a single place where to configure the specific settings for an image
variant, and allows generating these variants in a worker (offloading the web
process).

This works great, except it breaks when we try to use the named variant in
the `DirectUploadsController` above. It seems like named variants work only
work after the file has been uploaded and/or variant has been generated. To
still have the convenience of named variants, we can just get the processing
parameters directly:


```ruby
# app/controllers/direct_uploads_controller.rb
class DirectUploadsController < ActiveStorage::DirectUploadsController

  private

  # add thumb_url to response
  def direct_upload_json(blob)
    json = super(blob)
    variant_tf = MyModel.attachment_reflections["files"].named_variants[:thumb].transformations
    json[:thumb_url] = url_for(blob.representation(variant_tf))
    json
  end
end
```

This code block contains a direct reference to the model (`MyModel`) and the
attribute (`files`), so it is not a generic solution. This can probably be
improved, e.g. by getting the attachment from the blob and, which contains the
model name and attribute. But for us, it works well as it is.
