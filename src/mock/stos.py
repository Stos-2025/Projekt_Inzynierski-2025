import random
import hashlib
from uuid import uuid4
import zipfile
from random import randint
from os import environ
from flask import Flask, jsonify, send_file
from pathlib import Path


app = Flask(__name__)


@app.route("/tasks", methods=['GET'])
def tasks():
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


@app.route("/files/<file_id>", methods=['GET'])
def files(file_id: str):
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


@app.route("/tasks/<task_id>", methods=['POST'])
def task(task_id: str):
    """
    Mock endpoint for submitting task result.
    :param task_id: Id of the task.
    :return: Result message in JSON format.
    """
    return jsonify({"result": "uploaded " + str(task_id)}), 200

@app.route("/sync_problem", methods=['GET'])
def dbFiles():
    """
    Returns files.db zipped file
    """
    zip_filename = "files_db.zip"

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        zipf.write('files.db')

    return send_file(zip_filename, as_attachment=True, mimetype='application/zip')

@app.route("/sync", methods=['GET'])
def dbTag():
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
HOST = environ.get("STOS_HOST", '127.0.0.1')
app.run(host=HOST, port=PORT)
