"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.
"""
import traceback
from flask import render_template, Response
from sqlalchemy import desc, asc
from sparts import app, db_session
from sparts.models import Category

def render_page(template, title="", *args, **kwargs):
    return render_template("site_template.html", page_title=title, \
        template=template, *args, **kwargs, page=template, \
        production_server=app.config["PRODUCTION"], \
        categories=db_session.query(Category).order_by(asc(Category.id)).all())

def stacktrace():
    return "<pre>" + str(traceback.format_exc()) + "</pre>"

@app.route("/about")
def about():
    return render_page("about")

@app.errorhandler(404)
def page_not_found(e):
    return render_page("404"), 404

@app.route("/")
def home():
    return render_page("home")
