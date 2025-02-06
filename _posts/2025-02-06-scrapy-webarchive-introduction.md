---
layout: post
title: Extending Scrapy with WACZ to preserve and leverage archived data
author: leewesleyv
tags: [python, spiders]
image: /assets/scrapy.png
---

Web scraping is a powerful tool for collecting data from websites, but what happens to that data after it’s been scraped? Without a reliable way to preserve the exact state of the pages you collect, important details can be lost over time. Imagine being able to not only scrape data but also store it in a way that lets you revisit a website exactly as it appeared in the past, or share a complete, self-contained snapshot of your scraped data with others. This is where Scrapy, a Python-based web scraping framework, and WACZ, a format for archiving web data, come together.

In this article, we’ll explore how you can extend Scrapy with the `scrapy-webarchive` extension to preserve and leverage WACZ files. But why should you care? The ability to preserve and leverage archived web data opens up a range of practical applications. For instance, you can use WACZ to archive entire websites, supporting long-term research projects. Historical snapshots of websites can be invaluable for analyzing changes over time. Additionally, WACZ files provide a standardized way to package and share scraped data, making collaboration and data reuse more efficient. By leveraging existing WACZ archives, you can also reduce redundant scraping efforts, saving both time and resources.

While the benefits of WACZ are clear, this article also dives deep into the technical underpinnings of how WACZ works and how it integrates with Scrapy. You’ll learn about the structure of WACZ files, how they build on the WARC format, and how `scrapy-webarchive` transforms Scrapy’s scraping workflow to support both creating and reading WACZ archives. Additionally, we’ll explore how to overcome one of the key technical hurdles: efficiently accessing and extracting data from remote ZIP files stored in cloud services like S3 or Google Cloud Storage.

(Shortcut to the [spider example](#Spider example))

## What is WACZ?
WACZ stands for Web Archive Collection Zipped, a format designed to store, share, and access web archives efficiently. If you are already familiar with tools such as the [Wayback Machine](https://web.archive.org/), you probably know that it's convenient to explore archives, view changes over time, or retrieve historical web pages that are no longer available.

WACZ builds upon the WARC (Web ARChive) format, which is a standardized file format used for storing web crawls. WARC files capture HTTP requests and responses, enabling complete archival snapshots of web pages, including their structure and content. While WARC serves as the raw data format for web archives, WACZ enhances it by providing a structured package with additional features, such as metadata, integrity checks, and indexing support.

A WACZ object consists of the following:
1. A `datapackage.json` file for recording technical and descriptive metadata.
2. An extensible directory and naming convention for web archive data.
3. A method for bundling the directory layout in a ZIP file.

For more information, see the [WACZ specification](https://specs.webrecorder.net/wacz/latest/) or [WARC specification](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1-annotated/).

## Current Limitations of Archiving in Scrapy
Scrapy includes a built-in mechanism for caching scraped data through the `http-cache` middleware. While this feature is valuable for avoiding duplicate requests and speeding up development, it has notable limitations regarding archiving. The primary drawback is that the cached data is stored in a proprietary format, making it challenging to share or access outside the specific Scrapy project. Additionally, it relies on a custom caching mechanism and does not support standardized archive formats, limiting its compatibility and utility for broader use cases.

## Overview of `scrapy-webarchive`
`scrapy-webarchive` addresses these limitations by extending Scrapy’s functionality to handle WACZ files. It does this by automatically creating WACZ archives from scraped data and reading existing WACZ files by turning them into Scrapy-compatible requests and responses during scraping.

### Creating WACZ Files
During scraping, requests and responses are saved to a WARC file. First, the `warcinfo` record is generated with metadata regarding the crawl.

**Example of a `warcinfo` record (WARC file header)**
```
WARC/1.1
WARC-Type: warcinfo
WARC-Date: 2025-01-01T03:20:00Z
WARC-Record-ID: <urn:uuid:d7ae5c10-e6b3-4d27-967d-34780c58ba39>
Content-Type: application/warc-fields
Content-Length: 381

software: Scrapy/2.9.0 (+https://scrapy.org)
isPartOf: example
format: WARC file version 1.1
conformsTo:
 http://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/
```

Each request/response object passing through the `WarcExporter` extension is transformed into a `request` or `response` record and saved to the WARC file. 

**Example of a `request` record**
```
WARC/1.1
WARC-Type: request
WARC-Target-URI: http://www.example.com/
WARC-Warcinfo-ID: <urn:uuid:d7ae5c10-e6b3-4d27-967d-34780c58ba39>
WARC-Date: 2025-01-01T03:24:30Z
Content-Length: 236
WARC-Record-ID: <urn:uuid:4885803b-eebd-4b27-a090-144450c11594>
Content-Type: application/http;msgtype=request
WARC-Concurrent-To: <urn:uuid:92283950-ef2f-4d72-b224-f54c6ec90bb0>

GET / HTTP/1.0
User-Agent: ExampleBot/0.1.0 (https://www.example.com/bot)
Accept-Encoding: gzip, deflate, br
```

**Example of a `response` record**
```
WARC/1.1
WARC-Type: response
WARC-Target-URI: http://www.example.com/
WARC-Date: 2025-01-01T03:24:35Z
WARC-Block-Digest: sha1:UZY6ND6CCHXETFVJD2MSS7ZENMWF7KQ2
WARC-Payload-Digest: sha1:CCHXETFVJD2MUZY6ND6SS7ZENMWF7KQ2
WARC-Record-ID: <urn:uuid:92283950-ef2f-4d72-b224-f54c6ec90bb0>
Content-Type: application/http;msgtype=response
Content-Length: 52

HTTP/1.1 200 OK
Date: Wed, 1 Jan 2025 03:24:35 GMT
Content-Type: application/json

<html><body><title>Hello WARC!</title></body></html>
```

When the scraping finishes, the WARC file is indexed, metadata files are generated, and all files are packaged together into a WACZ file (`.wacz`). Based on the application configuration the WACZ file will be saved on the local file system or stored in a cloud storage (S3, GCS).

**Example of a `.cdxj` file with 2 entries**
```python
com,example)/ 20250101032435 {"url": "http://example.com/", "mime": "text/html", "status": "200", "digest": "A6DESOVDZ3WLYF57CS5E4RIC4ARPWRK7", "length": "1207", "offset": "834", "filename": "example.warc.gz", "req.http:method": "GET", "http:date": "Wed, 01 Jan 2025 03:24:35 GMT", "referrer": "http://example.com/"}
com,example)/example 20250101032437 {"url": "http://example.com/example", "mime": "text/html", "status": "302", "digest": "RP3Y66FDBYBZKSFYQ4VJ4RMDA5BPDJX2", "length": "675", "offset": "2652", "filename": "example.warc.gz", "req.http:method": "GET", "http:date": "Wed, 01 Jan 2025 03:25:02 GMT", "referrer": "http://example.com/"}
```

### Reading WACZ Files
The WACZ specification defines a [processing model](https://specs.webrecorder.net/wacz/1.1.1/#processing-model) that among others describes how to do a lookup. This comes down to the following steps:
1. Read the full index, can be CDX (Capture/Crawl inDeX) or CDXJ (CDX with JSON-style extension), from ZIP file
2. Binary search index looking for the URL
3. If a match found, get offset/length/location in WARC
4. Read compressed WARC chunk in ZIP file

Applying this to Scrapy's lifecycle:
1. Read the full index (CDX or CDXJ) from ZIP file when the spider is opened
2. For each request that goes through the downloader middleware search the index based on URL
3. If a match found, get offset/length/location in WARC
4. Read (compressed - optional) WARC chunk in ZIP file
5. Transform WARC chunk to a Scrapy-compatible `response` object.

#### Complications
When scraping WACZ files on the local filesystem, this process is fairly straightforward. This is because we can utilize Python's built-in `zipfile` module. It implements all sorts of methods that make it possible to fetch the index files, extract WARC records, and more. However, this is not the case when the archive is stored in the cloud, for example, on AWS Simple Storage Service (S3) or Google Cloud Storage (GCS). The `zipfile` module can only open files on a local filesystem.

Simple, right? We just download the archive so we can utilize this module. While this is possible, this is not preferable. WACZ files can grow to several gigabytes or more, making them costly in terms of bandwidth and time-consuming to download for crawling. Even when dealing with smaller archives, you want to avoid transferring unnecessary data.

Luckily for us, there is a solution that helps us avoid the unnecessary transfer of data. The ZIP file format provides random access that allows for efficient retrieval of an archived web page from large archives without the need to access the entire WACZ. To achieve this, we can read parts of the ZIP file using HTTP Range requests.

#### Partial requests
An HTTP Range request asks the server to send parts of a resource back to the client. If we can identify the byte range of our index file and our WARC records, we can send a range request to our server to only retrieve what we are looking for. The only problem is: how do we identify these byte ranges without being able to utilize Python's `zipfile` module?

#### ZIP Exploration
So, how does the `zipfile` module work, and how does it determine which files are contained within a ZIP file? To answer this, we need to understand the structure of ZIP files. Initially, I tried to dive straight into the `zipfile` module, but without a clear understanding of the underlying structure, my efforts weren’t very effective. My exploration began by reading the [ZIP specification](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT) and an insightful [blog article](https://blog.yaakov.online/zip64-go-big-or-go-home/) on Yaakov’s blog, which delves into the ZIP64 format, a topic I hadn’t even known existed. From these resources, I learned that ZIP files consist of several key components, each playing a critical role in how data is stored and accessed.

##### **Central Directory**
The Central Directory (CD) is like a table of contents for the ZIP file. It lists all the files within the archive, along with their metadata (e.g., names, sizes, compression methods, and offsets to their data within the file). This allows for quick location and extraction of individual files without scanning the entire archive.

##### **End of Central Directory**
The End of Central Directory (EOCD) marks the end of the CD and contains a summary of the archive. It includes the total number of files, the size of the CD, and its offset from the start of the file. This structure enables quick access to the CD.

##### **ZIP64**
ZIP64 extends the traditional ZIP format to support larger files and archives. It overcomes the 4 GB file size and 65,535 file count limitations of the original format. ZIP64 introduces additional fields to the CD and EOCD structures, allowing for expanded sizes and counts.

#### **Applying the knowledge**
In order to extract the list of files in the ZIP file, we need to locate and extract the CD. The first step in obtaining the CD is to locate the EOCD. For a standard ZIP file, the EOCD is located at the very end of the ZIP file. We simply extract the last chunk of bytes (65 KB) and locate the EOCD using its signature (`0x06054b50`).

```python
search_offset = max(0, file_size - 65536)
range_bytes = f"bytes={search_offset}-{file_size - 1}"
end_of_file = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
eocd_offset = file_part.rfind(b"\x50\x4B\x05\x06") + search_offset
```

Once we know the offset of the EOCD, we can extract the entire EOCD using another range request. The EOCD has a size of 22 bytes.

```python
range_bytes = f"bytes={eocd_offset}-{eocd_offset + 22 - 1}"
eocd = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
```

This, however, only works for standard ZIP files and not for ZIP64. For ZIP64, we instead find an EOCD locator near the end of the file. Using this EOCD locator, we can find the ZIP64 EOCD from which we can extract the start and size of the CD. The ZIP EOCD signature (`0x06064b50`) is slightly different from the standard EOCD signature. For ZIP64, we need to first extract the locator. The locator is 20 bytes long and is present before the standard EOCD.

```python
locator_offset = eocd_offset - 20
range_bytes = f"bytes={locator_offset}-{eocd_offset - 1}"
locator = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
```

The locator contains information on the location of the ZIP64 EOCD. Once again, we make a range request—this time to retrieve the ZIP64 EOCD. The ZIP64 EOCD size is 56 bytes.

```python
zip64_eocd_offset = struct.unpack("<Q", locator[8:16])[0] + locator_offset
range_bytes = f"bytes={zip64_eocd_offset}-{zip64_eocd_offset + 56 - 1}"
zip64_eocd = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
```

Now that we have the EOCD or ZIP64 EOCD, we can extract the CD offset and size, and finally get the CD.

```python
if eocd:
	cd_size = struct.unpack("<I", eocd[12:16])[0]
	cd_start = struct.unpack("<I", eocd[16:20])[0]
elif zip64_eocd:
	cd_size = struct.unpack("<Q", zip64_eocd[40:48])[0]
	cd_start = struct.unpack("<Q", zip64_eocd[48:56])[0]

range_bytes = f"bytes={cd_start}-{cd_start + cd_size - 1}"
cd = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
```

From here on, we can parse the CD to retrieve the files along with their offsets, allowing us to begin looking up specific WARC records.

```python
entries = {}
offset = 0

while offset < len(cd):
	file_name_length = struct.unpack("<H", cd[offset + 28:offset + 30])[0]
	extra_field_length = struct.unpack("<H", cd[offset + 30:offset + 32])[0]
	compressed_size = struct.unpack("<I", cd[offset + 20:offset + 24])[0]
	header_offset = struct.unpack("<I", cd[offset + 42:offset + 46])[0]

	# Check for ZIP64 extra fields for large files
	if compressed_size == 0xFFFFFFFF:
		compressed_size = read_zip64_extra_field(cd, offset)

	file_name = cd[offset + 46:offset + 46 + file_name_length].decode("utf-8")

	entries[file_name] = {
		"header_offset": header_offset,
		"file_header_length": get_file_header_length(header_offset),
		"compressed_size": compressed_size,
	}
	offset += 46 + file_name_length + extra_field_length

return entries
```

With the entries in the ZIP file known, we can start by extracting and parsing the index file. Through a lookup in our entries, we can find the metadata for a specific file. From this we can derive the start and end bytes that we need to request from the server. The offset (or start) is calculated by taking the header offset, where the file header begins, and adding the file header length. The section we are skipping is the file header, which is not relevant at this point. The end of the range is calculated by adding the file size.

```python
index_path = "indexes/index.cdxj"
index_metadata = entries[index_path]

start = index_metadata["header_offset"] + index_metadata["file_header_length"]
end = start + metadata["compressed_size"] - 1
range_bytes = f"bytes={start}-{end}"

index_raw = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
index = BytesIO(index_raw)
```

To make it easier to look up data when making requests, we can parse the index file into a dictionary. However, this approach is not entirely safe because archives can include data from multiple recordings, which means there might be duplicate URLs. Also, index files can get quite large, which can use up a lot of memory. For example, a WACZ file I created was 1.7 GB in size, with an index containing 14,255 entries that added up to 5.3 MB.

```python
cdxj_records = defaultdict(list)

for line in index_file:
	cdxj_record = CdxjRecord.from_cdxline(line.decode())
	cdxj_records[cdxj_record.data["url"]].append(cdxj_record)
```

Now we can finally start looking into how this hooks into the Scrapy workflow. With the `scrapy_webarchive.downloadermiddlewares.WaczMiddleware` downloader middleware configured, any incoming request is resolved by doing a lookup into our index. In this case, the request that comes in is on the URL `http://example.com`. We do a lookup in our CDXJ records (or index) to get the metadata related to it. We are mainly interested in the location of this record in the WARC and the actual WARC file that contains this response, so we can extract the response from it. 

```python
from scrapy_webarchive.warc import WARCReader

# Lookup URL is the index and extract metadata
cdxj_record = cdxj_records["http://example.com"]
offset = int(cdxj_record["offset"])
size = int(cdxj_record["length"])
warc_metadata = entries[f"archives/{cdxj_record['filename']}"]

# Determine the range
start = warc_metadata["header_offset"] + warc_metadata["file_header_length"] + offset
end = start + size - 1
range_bytes = f"bytes={start}-{end}"

# Fetch the WARC record
warc_record_raw = s3_client.get_object(Bucket="bucket-name", Key="archive.wacz", Range=range_bytes)["Body"].read()
warc_record = BytesIO(warc_record_raw)
parsed_warc_record = WARCReader(warc_record).read_record()
```

## Spider example
Below is an example of how to add WACZ crawling functionality to your spiders. This example uses a simple spider that scrapes `https://quotes.toscrape.com/`. In the spider, we define `custom_settings` to provide settings specific to the spider.

We set `SW_WACZ_SOURCE_URI` to the location of the WACZ file as a URI and update `DOWNLOADER_MIDDLEWARES` to include the middleware that manages the request/response flow with WACZ. In your spider, point `SW_WACZ_SOURCE_URI` to where your WACZ file is stored. In this example, the WACZ file is on S3, so you’ll need to configure AWS-specific settings.

To let Scrapy access your WACZ file on S3, you need to configure your AWS credentials. The required settings are `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, where you replace these with your own keys. Make sure to also check settings like `AWS_REGION_NAME` to ensure everything is configured properly. You can refer to the [Scrapy documentation](https://docs.scrapy.org/en/latest/topics/settings.html) for a full list of settings.

The requirements for this example are:
- Python 3.7, 3.8, 3.9, 3.10, 3.11, or 3.12
- `scrapy-webarchive` (0.4.0)
- `boto3`

```python
import scrapy


class QuotesSpider(scrapy.Spider):
	name = "quotes"
	start_urls = ["https://quotes.toscrape.com/"]

	# Enable settings to crawl from an existing WACZ archive.
	custom_settings = {
		"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
		"AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"SW_WACZ_SOURCE_URI": "s3://bucket-name/path/to/archive.wacz",
		"DOWNLOADER_MIDDLEWARES": {
			"scrapy_webarchive.downloadermiddlewares.WaczMiddleware": 500,
		}
	}

	def start_requests(self):
		for url in self.start_urls:
			yield scrapy.Request(url, dont_filter=True)

	def parse(self, response):
		for quote in response.css("div.quote"):
			yield {
				"text": quote.css("span.text::text").extract_first(),
				"author": quote.css("small.author::text").extract_first(),
				"tags": quote.css("div.tags > a.tag::text").extract()
			}

		next_page_url = response.css("li.next > a::attr(href)").extract_first()
		if next_page_url is not None:
			yield scrapy.Request(response.urljoin(next_page_url))
```

The full documentation on how to implement `scrapy-webarchive` is available [here](https://developers.thequestionmark.org/scrapy-webarchive/).

## Conclusion
The idea of integrating WACZ with Scrapy has been successfully realized and turned into an open-source Python package. The `scrapy-webarchive` extension allows developers to create and access WACZ archives effortlessly, bridging the gap between scraping and preserving data.

Along the way, I’ve learned much more about ZIP files than I ever expected, exploring their structure and behavior in depth. It was a bit unfortunate to find that support for handling remote ZIP files is somewhat limited within the Python landscape, but it turned out to be an interesting challenge to work with them on a lower level.

In addition to that, I’ve gained a solid understanding of the WACZ and WARC formats and their practical applications. Working with web archives in the past, I now have much better insight into how these archives are stored and accessed so efficiently.

## Links

- **PyPI**: https://pypi.org/project/scrapy-webarchive/
- **GitHub**: https://github.com/q-m/scrapy-webarchive
- **Documentation**: https://developers.thequestionmark.org/scrapy-webarchive/

## A Word of Thanks

Thank you to [wvengen](https://github.com/wvengen) for originating the idea of integrating WACZ with the Scrapy framework and for their input and discussions on the implementation details.

