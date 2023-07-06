# docsbox

`docsbox` is a standalone service that allows you convert office documents, like .docx and .pptx, into more useful filetypes like PDF, for viewing it in browser with PDF.js, or HTML for organizing full-text search of document content.
`docsbox` uses **LibreOffice** (via **LibreOfficeKit**) for document converting.

```bash
$ curl -F "file=@kittens.docx" -F "file=@/home/user/Documents/filesample.docx" http://docconverter.technikum-wien.at/api/v1/

{
    "id": "9b643d78-d0c8-4552-a0c5-111a89896176",
    "status": "queued"
}

$ curl http://docconverter.technikum-wien.at/api/v1/9b643d78-d0c8-4552-a0c5-111a89896176

{
    "id": "9b643d78-d0c8-4552-a0c5-111a89896176",
    "result_url": "/media/9b643d78-d0c8-4552-a0c5-111a89896176.zip",
    "status": "finished"
}

$ curl -O http://docconverter.technikum-wien.at/media/9b643d78-d0c8-4552-a0c5-111a89896176.zip

$ unzip -l 9b643d78-d0c8-4552-a0c5-111a89896176.zip

Archive:  9b643d78-d0c8-4552-a0c5-111a89896176.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
    11135  2016-07-08 05:31   txt
   373984  2016-07-08 05:31   pdf
   147050  2016-07-08 05:31   html
---------                     -------
   532169                     3 files
```

```bash
$ cat options.json
{
  "formats": ["pdf"],
  "thumbnails": {
    "size": "640x480",
  }
}

$ curl -i -F "file=@kittens.ppt" -F "options=<options.json" http://docconverter.technikum-wien.at/api/v1/

{
  "id": "afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1",
  "status": "queued"
}

$ curl http://docconverter.technikum-wien.at/api/v1/afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1

{
  "id": "afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1",
  "status": "finished",
  "result_url": "/media/afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1.zip"
}

$ curl -O http://docconverter.technikum-wien.at/media/afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1.zip

$ unzip -l afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1.zip
Archive:  afb58e2b-78fa-4dd7-b7f9-a64f75f50cb1.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
   779820  2016-07-10 02:02   pdf
   177357  2016-07-10 02:02   thumbnails/0.png
                              ...
   130923  2016-07-10 02:02   thumbnails/30.png
---------                     -------
 13723770                     32 files

```

# API

```
POST (multipart/form-data) /api/v1/
file=@kittens.docx
options={ # json, optional
    "formats": ["pdf"] # desired formats to be converted in, optional
    "thumbnails": { # optional
        "size": "320x240",
    }
}

GET /api/v1/{task_id}
```

# Install
Installation and configuration are done by ansible


# Settings (env)

```
REDIS_URL - redis-server url (default: redis://[::1]:6379/0)
REDIS_JOB_TIMEOUT - job timeout (default: 10 minutes)
ORIGINAL_FILE_TTL - TTL for uploaded file in seconds (default: 10 minutes)
RESULT_FILE_TTL - TTL for result file in seconds (default: 1 hour)
THUMBNAILS_DPI - thumbnails dpi, for bigger thumbnails choice bigger values (default: 90)
LIBREOFFICE_PATH - path to libreoffice (default: /usr/lib/libreoffice/program/)
```

# Supported filetypes

| Input                              | Output              | Thumbnails |
| ---------------------------------- | ------------------- | ---------- |
| Document `doc` `docx` `odt` `rtf`  | `pdf` `txt` `html`  | `yes`      |
| Presentation `ppt` `pptx` `odp`    | `pdf` `html`        | `yes`      |
| Spreadsheet `xls` `xlsx` `ods`     | `pdf` `csv` `html`  | `yes`      |
