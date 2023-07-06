import os
import uuid
import logging

import ujson
import datetime

import magic # from magic import Magic
from tempfile import NamedTemporaryFile

from flask import request
from flask_restful import Resource, abort

from docsbox import app, rq
from docsbox.docs.tasks import remove_file, process_document

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=app.config["LOGS_PATH"] + 'docsbox.log', level=logging.INFO)

class DocumentView(Resource):

    def get(self, task_id):
        """
        Returns information about task status.
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)

        if task:
            return {
                "id": task.id,
                "status": task._status,
                "result_url": task.result
            }
        else:
            return abort(404, message="Unknown task_id")


class DocumentCreateView(Resource):

    def post(self):
        """
        Recieves file and options, checks file mimetype,
        validates options and creates converting task
        """
        if "file" not in request.files:
            return abort(400, message="file field is required")
        else:
            temp_dir = str(uuid.uuid4().hex) + "/"
            temp_media_dir = app.config["MEDIA_PATH"] + temp_dir
            try:
                os.mkdir(temp_media_dir)
            except FileExistsError:
                pass
            for single_file in request.files.getlist("file"):
                clean_filename = os.path.basename(single_file.filename)
                with NamedTemporaryFile(delete=False, prefix=temp_media_dir) as tmp_file:
                    single_file.save(tmp_file)
                    tmp_file.flush()
                    tmp_file.close()
                    remove_file.schedule(datetime.timedelta(seconds=app.config["ORIGINAL_FILE_TTL"]), temp_media_dir)
                    mimetype = magic.from_file(tmp_file.name, mime=True) # detect mimetype
                    if mimetype not in app.config["SUPPORTED_MIMETYPES"]:
                        return abort(400, message="Not supported mimetype: '{0}'".format(mimetype))
                    options = request.form.get("options", None)
                    if options: # options validation
                        options = ujson.loads(options)
                        formats = options.get("formats", None)
                        if not isinstance(formats, list) or not formats:
                            return abort(400, message="Invalid 'formats' value")
                        else:
                            for fmt in formats:
                                supported = (fmt in app.config["SUPPORTED_MIMETYPES"][mimetype]["formats"])
                                if not supported:
                                    message = "'{0}' mimetype can't be converted to '{1}'"
                                    return abort(400, message=message.format(mimetype, fmt))
                        thumbnails = options.get("thumbnails", None)
                        if thumbnails:
                            if not isinstance(thumbnails, dict):
                                return abort(400, message="Invalid 'thumbnails' value")
                            else:
                                thumbnails_size = thumbnails.get("size", None)
                                if not isinstance(thumbnails_size, str) or not thumbnails_size:
                                    return abort(400, message="Invalid 'size' value")
                                else:
                                    try:
                                        (width, height) = map(int, thumbnails_size.split("x"))
                                    except ValueError:
                                        return abort(400, message="Invalid 'size' value")
                                    else:
                                        options["thumbnails"]["size"] = (width, height)
                    else:
                        if mimetype == "application/pdf":
                            options = {
                                "formats": ["html"]
                            }
                        else:
                            options = app.config["DEFAULT_OPTIONS"]
                    task = process_document.queue(tmp_file.name, options, { "mimetype": mimetype,  }, temp_dir, clean_filename)

        return {
            "id": task.id,
            "status": task._status
        }

