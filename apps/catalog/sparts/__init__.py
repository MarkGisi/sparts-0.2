"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

sparts catalog package
"""

import sys
import os

from flask import Flask, jsonify
from requests.exceptions import ReadTimeout, ConnectionError
# from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__)

# application_cache = SimpleCache(threshold=64, default_timeout=3600)

app.config.from_object("config")

def get_resource_as_string(name, charset='utf-8'):
    """for writing css or javascript files directly in the html document.
    """
    with app.open_resource(name) as file:
        return file.read().decode(charset)

app.jinja_env.globals['get_resource_as_string'] = get_resource_as_string

# import controllers

from sparts.database import db_session
import sparts.views
from sparts.views import render_page, stacktrace
import sparts.catalog
import sparts.envelope
import sparts.sampledata
import sparts.api
from sparts.api import register_app_with_blockchain


try:
    register_app_with_blockchain()
except sparts.exceptions.APIError as error:
    print("Failed to register app with blockchain. " + str(error))
except ReadTimeout:
    print("Failed to register app with blockchain. Conductor service timed out")
except ConnectionError:
    print("Failed to register app with blockchain. " \
        + "The conductor service refused connection or is not running.")
except Exception as error:
    print(str(error))

try:
    sparts.catalog.populate_categories()
except sparts.exceptions.APIError as error:
    print("Failed to get part categories from the ledger. " + str(error))
except ReadTimeout:
    print("Failed to get part categories from the ledger. Conductor service timed out")
except ConnectionError:
    print("Failed to get part categories from the ledger. " \
        + "The conductor service refused connection or is not running.")
except Exception as error:
    print(str(error))

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
