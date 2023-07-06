import os
import shutil
import logging
import datetime

from pylokit import Office
from wand.image import Image
from tempfile import NamedTemporaryFile, TemporaryDirectory

from rq import get_current_job

from docsbox import app, rq
from docsbox.docs.utils import make_zip_archive, make_thumbnails

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=app.config["LOGS_PATH"] + 'docsbox.log', level=logging.INFO)

@rq.job(timeout=app.config["REDIS_JOB_TIMEOUT"])
def remove_file(path):
    """
    Just removes a file.
    Used for deleting original files (uploaded by user) and result files (result of converting) 
    """
    if os.path.isfile(path):
        return os.remove(path)
    else:
        if (os.path.exists(path) and os.path.isdir(path)):
            return shutil.rmtree(path)


@rq.job(timeout=app.config["REDIS_JOB_TIMEOUT"])
def process_document(path, options, meta, temporary_path, original_name):
    current_task = get_current_job()
    with Office(app.config["LIBREOFFICE_PATH"]) as office: # acquire libreoffice lock
        with office.documentLoad(path) as original_document: # open original document
            tmp_dir = "/tmp/" + temporary_path #' as tmp_dir: # create temp dir where output'll be stored
            for fmt in options["formats"]: # iterate over requested formats
                current_format = app.config["SUPPORTED_FORMATS"][fmt]
                output_path = os.path.join(tmp_dir, original_name + ".pdf")
                original_document.saveAs(output_path, fmt=current_format["fmt"])
            if options.get("thumbnails", None):
                is_created = False
                if meta["mimetype"] == "application/pdf":
#                        pdf_path = path
                    pdf_path = os.path.join(tmp_dir, original_name + ".pdf")
                elif "pdf" in options["formats"]:
#                        pdf_path = os.path.join(tmp_dir, "current_task_pdf")
                    pdf_path = os.path.join(tmp_dir, original_name + ".pdf")
                else:
                    pdf_tmp_file = NamedTemporaryFile()
                    pdf_path = pdf_tmp_file.name
                    original_document.saveAs(pdf_tmp_file.name, fmt="pdf")
                    is_created = True
                image = Image(filename=pdf_path,
                              resolution=app.config["THUMBNAILS_DPI"])
                if is_created:
                    pdf_tmp_file.close()
                thumbnails = make_thumbnails(image, tmp_dir, options["thumbnails"]["size"])
            result_path, result_url = make_zip_archive(current_task.id, tmp_dir)
        remove_file.schedule(datetime.timedelta(seconds=app.config["RESULT_FILE_TTL"]), result_path)
        remove_file.schedule(datetime.timedelta(seconds=app.config["ORIGINAL_FILE_TTL"]), tmp_dir)

    return result_url
