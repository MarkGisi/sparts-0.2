"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

catalog views
"""
import json
from flask import render_template, request, abort
from sqlalchemy import desc, asc, and_
from sqlalchemy.sql import exists
from sparts import app, db_session, render_page, jsonify, stacktrace
from sparts.models import Category, Supplier, Part, Envelope
from sparts.api import APIError, get_blockchain_categories
from sparts.envelope import delete_envelope


def populate_categories():
    """ask blockchain for categories and update the database
    """
    if app.config["BYPASS_API_CALLS"]: return

    print("Retrieving blockchain categories ...")
    categories = get_blockchain_categories()

    # delete old categories if their UUID's no longer exists

    new_uuids = [category_dict["uuid"] for category_dict in categories]
    parts = db_session.query(Part).all()

    for category in db_session.query(Category).all():
        if category.uuid not in new_uuids:
            db_session.delete(category)

            # delete all the parts relations that had this category

            for part in parts:
                for part_category in part.categories:
                    if part_category.uuid == category.uuid:
                        part.categories.remove(part_category)

    db_session.flush()

    # update existing or insert new categories

    for category_dict in categories:
        category_query = db_session.query(Category).filter(Category.uuid == category_dict["uuid"])

        if category_query.count() == 1:
            # update
            category = category_query.one()
            category.name = category_dict["name"]
            category.description = category_dict["description"]
        else:
            # insert
            category = Category()
            category.uuid = category_dict["uuid"]
            category.name = category_dict["name"]
            category.description = category_dict["description"]
            db_session.add(category)

    db_session.flush()
    db_session.commit()

@app.route("/catalog/supplier/<supplier_id>")
def catalog_by_supplier(supplier_id):
    """catalog page filtered by supplier id
    """
    return render_page("catalog", parts=db_session.query(Part, Supplier) \
        .join(Supplier).filter(Supplier.id == supplier_id) \
        .order_by(asc(Part.id)).all(), \
        suppliers=db_session.query(Supplier), selected_supplier=supplier_id)


@app.route("/catalog/category/<category>")
def catalog_by_category(category):
    """catalog page filtered by category name
    """
    part_query = db_session.query(Part, Supplier).join(Supplier)

    if category == "other":
        part_query = part_query.filter(~Part.categories.any())
    else:
        part_query = part_query.filter(Part.categories.any(Category.name == category))

    part_query = part_query.order_by(asc(Part.id))

    return render_page("catalog", parts=part_query.all(), suppliers=db_session.query(Supplier))


@app.route("/catalog")
def catalog():
    """catalog page
    """
    parts = db_session.query(Part, Supplier).join(Supplier) \
        .order_by(asc(Part.id))

    # filter by search term if it exists

    if "q" in request.args:
        parts = parts.filter(Part.name.ilike("%" + request.args["q"] + "%"))

    return render_page("catalog", parts=parts.all(), suppliers=db_session.query(Supplier))


@app.route("/supplier/new", methods=["POST"])
def create_supplier():
    """json route for creating a new supplier. expects a simple object containing the fields in the
    Supplier data model.
    """
    response_data = {"failed": False}
    try:
        data = request.json

        assert "supplier_name" in data, "Bad call, missing required 'supplier_name'."
        assert "password" in data, "Bad call, missing required 'password'."

        supplier_name = data["supplier_name"]
        pwd = data["password"]

        assert not db_session.query(exists().where(Supplier.name == supplier_name)).scalar(), \
            "Another supplier with this name already exists."

        supplier = Supplier()
        supplier.name = supplier_name
        supplier.password = pwd
        supplier.blockchain = data["blockchain"]

        # call the ledger service to add this supplier to the blockchain

        if supplier.blockchain:
            supplier.save_to_blockchain()

        db_session.add(supplier)
        db_session.flush()
        db_session.commit()

        response_data["supplier_table_html"] = render_template("supplier_table.html", \
            suppliers=db_session.query(Supplier))

    except (APIError, AssertionError) as error:
        response_data["failed"] = True
        response_data["error_message"] = str(error)

    except:
        response_data["failed"] = True
        response_data["error_message"] = stacktrace()

    return jsonify(response_data)


@app.route("/supplier/new", methods=["GET"])
def create_supplier_page():
    """new supplier page
    """
    return render_page("new_supplier", suppliers=db_session.query(Supplier))


def supplier_password_is_correct(supplier_id, password):
    """check if the given password is correct
    """
    return db_session.query(exists().where( \
        and_(Supplier.id == supplier_id, Supplier.password == password))).scalar()


@app.route("/part/create", methods=["POST"])
def create_part():
    """json route for creating a new part, expects a simple object containing the fields in the
    Part data model.
    """
    data = request.json

    response_data = {}

    response_data["incorrect_password"] = not \
        supplier_password_is_correct(data["supplier_id"], data["password"])

    if response_data["incorrect_password"]:
        return jsonify(response_data)

    try:
        part = Part()

        # read off the fields from the posted data and set the new part's attributes

        for col in Part.__table__.columns:
            if col.key != "id":
                if col.key in data:
                    setattr(part, col.key, data[col.key])

        part.categories = [category for category in db_session.query(Category) \
            if str(category.id) in data["categories"] ]

        supplier = db_session.query(Supplier).filter(Supplier.id == data["supplier_id"]).one()

        assert not part.blockchain or supplier.blockchain, "The supplier '" + supplier.name \
             +  "' is not registered with the blockchain network. None of its" \
             + " software parts can be registered with the network."

        # call the ledger service to add this part to the blockchain

        if part.blockchain:
            part.save_to_blockchain()

        db_session.add(part)
        db_session.flush()
        db_session.commit()

        response_data["failed"] = False
        response_data["part_id"] = part.id

    except (APIError, AssertionError) as error:
        response_data["failed"] = True
        response_data["error_message"] = str(error)

    except:
        response_data["failed"] = True
        response_data["error_message"] = stacktrace()

    return jsonify(response_data)


@app.route("/part/new")
def new_part():
    """new part page"""
    return render_page("new_part", suppliers=db_session.query(Supplier))


@app.route("/part/view/<int:part_id>")
def view_part(part_id):
    """part profile page
    """
    if not db_session.query(exists().where(Part.id == part_id)).scalar():
        abort(404)

    part, supplier = db_session.query(Part, Supplier) \
        .join(Supplier).filter(Part.id == part_id).one()

    category_list = [{"text": cat.description, "value": cat.id} \
        for cat in db_session.query(Category).all()]

    selected_categories = [category.id for category in part.categories]

    return render_page("part", part=part, supplier=supplier, \
        category_list=category_list, envelope=part.envelope, \
        selected_categories=selected_categories)


@app.route("/part/edit", methods=["POST"])
def edit_part():
    """json route for editing a part
    """
    data = request.json
    response_data = {}

    # validate supplier password

    response_data["incorrect_password"] = \
        not supplier_password_is_correct(data["supplier_id"], data["password"])
    if response_data["incorrect_password"]:
        return jsonify(response_data)

    # make sure that the part exists

    part_query = db_session.query(Part).filter(Part.id == data["part_id"])
    response_data["part_exists"] = (part_query.count() == 1)

    if not response_data["part_exists"]:
        return jsonify(response_data)

    # update the part

    try:
        part = part_query.one()

        for col in Part.__table__.columns:
            if col.key != "id":
                if col.key in data:
                    setattr(part, col.key, data[col.key])

        # update the categories

        if "categories" in data:
            part.categories = [category for category in db_session.query(Category).all() \
            if category.id in data["categories"] ]

        db_session.flush()
        db_session.commit()

        response_data["failed"] = False
    except:
        response_data["failed"] = True
        response_data["error_message"] = stacktrace()

    return jsonify(response_data)


@app.route("/part/delete", methods=["POST"])
def delete_part():
    """json route for deleting a part. expects part_id.
    """
    response_data = {}
    data = request.json

    # validate supplier password

    response_data["incorrect_password"] = \
        not supplier_password_is_correct(data["supplier_id"], data["password"])
    if response_data["incorrect_password"]:
        return jsonify(response_data)

    # make sure that the part exists

    part_query = db_session.query(Part).filter(Part.id == data["part_id"])
    response_data["part_exists"] = (part_query.count() == 1)

    if not response_data["part_exists"]:
        return jsonify(response_data)

    try:
        part = part_query.one()

        db_session.delete(part)
        db_session.flush()

        if part.envelope:
            delete_envelope(part.envelope)

        db_session.commit()
        response_data["failed"] = False
    except:
        response_data["failed"] = True
        response_data["error_message"] = stacktrace()

    return jsonify(response_data)

