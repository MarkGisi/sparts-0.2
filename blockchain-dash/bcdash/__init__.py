"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

bcdash catalog package
"""

import sys
import os

from flask import Flask, jsonify
# from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__)

# application_cache = SimpleCache(threshold=64, default_timeout=3600)

app.config.from_object("config")

import bcdash.views
import bcdash.api
from bcdash.api import register_app_with_blockchain

# register this app with the conductor service

try:
    register_app_with_blockchain()
except Exception as error:
    print(str(error))
