import random
import hashlib
from uuid import uuid4
import zipfile
from random import randint
from os import environ
from flask import Flask, jsonify, send_file
from pathlib import Path
from flask_restx import Api, Resource


app = Flask(__name__)

api = Api(app, version="1.0", title="Mock API", description="API for handling tasks and files")
ns = api.namespace("api", description="API Endpoints")

@ns.route("/tasks", methods=['GET'])
def tasks(Resource):
    """
    Endpoint for receiving mocked tasks.
    :return: Task's data in JSON format.
    """
    randomized_task: dict[str, str | list[str]] = {
        "student_id": str(randint(1, 10)),
        "task_id": str(uuid4()),
        "file_ids": [str(uuid4())]
    }

    return jsonify(randomized_task), 200


@ns.route("/files/<file_id>", methods=['GET'])
def files(Resource, file_id: str):
    """
    Return mock taks file
    :param file_id: Id of the file.
    :return: Invokes send_file function of flask library.
    """
    file_path = Path('main0.cpp')
    file_extension = file_path.suffix

    response = send_file(file_path, as_attachment=True, mimetype="text/plain")
    response.headers["X-File-Extension"] = file_extension
    return response, 200


@ns.route("/tasks/<task_id>", methods=['POST'])
def task(Resource, task_id: str):
    """
    Mock endpoint for submitting task result.
    :param task_id: Id of the task.
    :return: Result message in JSON format.
    """
    return jsonify({"result": "uploaded " + str(task_id)}), 200

@ns.route("/sync_problem", methods=['GET'])
def dbFiles(Resource):
    """
    Returns files.db zipped file
    """
    zip_filename = "files_db.zip"

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        zipf.write('files.db')

    return send_file(zip_filename, as_attachment=True, mimetype='nslication/zip')

@ns.route("/sync", methods=['GET'])
def dbTag(Resource):
    """
    Returns hash of files.db
    """
    hash_md5 = hashlib.md5()
    with open('files.db', 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    file_hash = hash_md5.hexdigest()
    return jsonify({"remote_tag": file_hash}), 200




PORT = int(environ.get("STOS_PORT", '2137'))
HOST = environ.get("STOS_HOST", '0.0.0.0')

if __name__ == '__main__':
    app.run(host=HOST, port=PORT,   debug=True)
