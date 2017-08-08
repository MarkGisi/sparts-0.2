"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

routes for reading sample data from CSV files and importing them in the database
"""
import os
import json
import csv
import shutil
import hashlib
import codecs
import glob
import datetime
from sparts import app, db_session, jsonify, stacktrace
from sparts.database import init_db, engine
from sparts.models import Part, Supplier, Category, Artifact, Envelope, BOM, BOMItem
from sparts.exceptions import EnvelopeError, APIError
from sparts.envelope import extract_and_parse_envelope
from sparts.api import get_blockchain_categories, save_part_supplier_relation, \
    save_part_category_relation, save_part_envelope_relation

@app.route("/api/sparts/reset")
def reset_handler():
    """respond to conductor call RESET by purging the database and repopulating with sample data
    """
    response_data = {}

    try:

        # clear all the tables

        for part in db_session.query(Part).all():
            part.categories = []
            part.envelope = None
            part.supplier = None
            db_session.delete(part)

        db_session.flush()

        db_session.query(Category).delete()
        db_session.query(Supplier).delete()

        for envelope in db_session.query(Envelope).all():
            envelope.boms = []
            envelope.artifacts = []
            db_session.delete(envelope)

        db_session.flush()

        for bom in db_session.query(BOM).all():
            bom.items = []
            bom.artifact = None
            db_session.delete(bom)

        db_session.flush()

        db_session.query(Artifact).delete()
        db_session.query(BOMItem).delete()

        db_session.flush()
        db_session.commit()

        # delete all envelope and artifact files

        empty_directory(app.config["UPLOAD_FOLDER"])
        empty_directory(app.config["ARTIFACT_FOLDER"])

        # insert suppliers

        for supplier_dict in read_csv_file("suppliers.csv"):

            supplier = Supplier()
            supplier.name = supplier_dict["name"]
            supplier.uuid = supplier_dict["uuid"]
            supplier.password = hashlib.md5(codecs.encode(supplier_dict["password"], "utf-8"))\
                .hexdigest()
            supplier.blockchain = (supplier_dict["blockchain"] == "true")

            if supplier.blockchain:
                supplier.save_to_blockchain()

            db_session.add(supplier)

        db_session.flush()


        # insert categories

        categories_by_uuid = {}

        for category_dict in read_csv_file("categories.csv"):
            category = Category()
            category.name = category_dict["name"]
            category.uuid = category_dict["uuid"]
            category.description = category_dict["description"]
            db_session.add(category)

            category.save_to_blockchain()

            categories_by_uuid[category.uuid] = category

        db_session.flush()


        # read part category association table

        part_category_instances = {}

        for part_category_relation in read_csv_file("part-categories.csv"):
            if part_category_relation["part_uuid"] not in part_category_instances:
                part_category_instances[part_category_relation["part_uuid"]] = []

            part_category_instances[part_category_relation["part_uuid"]].append( \
                categories_by_uuid[part_category_relation["category_uuid"]])


        # insert parts

        categories = db_session.query(Category).all()

        for part_dict in read_csv_file("parts.csv"):

            part = Part()

            part_supplier_query = db_session.query(Supplier)\
                .filter(Supplier.uuid == part_dict["supplier_uuid"])

            assert part_supplier_query.count() == 1, \
                "Invalid supplier UUID in the following sample part. \n" \
                + json.dumps(part_dict) + " Could not find a supplier with UUID '" \
                + part_dict["supplier_uuid"] + "'"

            part.supplier = part_supplier_query.one()

            part.blockchain = (part_dict["blockchain"] == "true")

            for field in ["uuid", "usku", "supplier_part_id", "name", "version", \
                "licensing", "url", "status", "description", "checksum", "src_uri"]:

                setattr(part, field, part_dict[field])

            if part.uuid in part_category_instances:
                for category in part_category_instances[part.uuid]:
                    part.categories.append(category)

            db_session.add(part)

            if part.blockchain:

                part.save_to_blockchain()

                for category in part.categories:
                    save_part_category_relation(part, category)

                save_part_supplier_relation(part, part.supplier)

        db_session.flush()


        # read envelope part association table

        envelope_parts = {}

        for envelope_parts_dict in read_csv_file("part-envelopes.csv"):
            envelope_parts[envelope_parts_dict["envelope_uuid"]] = envelope_parts_dict["part_uuid"]

        # unpack and parse envelopes

        for envelope_path in glob.glob(\
                os.path.join(app.config["SAMPLE_DATA_FOLDER"], "envelopes/*")):

            envelope = create_envelope(envelope_path)

            part_query = db_session.query(Part).filter(Part.uuid == envelope_parts[envelope.uuid])

            assert part_query.count() == 1, \
                "Invalid sample data. No part was found with UUID " + envelope_parts[envelope.uuid]

            part = part_query.one()
            part.envelope = envelope
            envelope.blockchain = part.blockchain

            if envelope.blockchain:
                envelope.save_to_blockchain()
                save_part_envelope_relation(part, envelope)

            db_session.flush()

        db_session.commit()

        response_data["status"] = "success"

    except AssertionError as error:
        response_data["status"] = "failed"
        response_data["error_message"] = str(error)

    except APIError as error:
        response_data["status"] = "failed"
        response_data["error_message"] = "Encountered an error while calling blockchain API. " \
            + str(error)

    except (OSError, IOError):
        response_data["status"] = "failed"
        response_data["error_message"] = stacktrace()

    except:
        response_data["status"] = "failed"
        response_data["error_message"] = "Unhandled Exception \n\n" + stacktrace()

    return jsonify(response_data)


def create_envelope(envelope_path):
    """create a directory, extract the envelope zip file at envelope_path there, parse it,
    add it along with all its artifacts to the database, and return the envelope instance
    """

    base_dirname = hashlib.sha1(codecs.encode(str(datetime.datetime.now()), "utf-8")).hexdigest()
    base_path = os.path.join(app.config["UPLOAD_FOLDER"], base_dirname)
    filename = os.path.basename(envelope_path)
    extract_path = os.path.join(base_path, "envelope")
    envelope_upload_path = os.path.join(base_path, filename)

    assert not os.path.exists(base_path), \
        "Could not create unique directory to extract envelope files." + \
        " Please try again later."

    try:
        os.makedirs(extract_path)
    except:
        raise EnvelopeError("Failed to create directory to extract envelope")

    try:
        shutil.copyfile(envelope_path, envelope_upload_path)
    except:
        raise EnvelopeError("Failed to copy sample envelope file.")

    return extract_and_parse_envelope(envelope_upload_path, extract_path)


def read_csv_file(filename):
    """read a CSV file and return a key, value dict of contents
    """
    file_path = os.path.join(app.config["SAMPLE_DATA_FOLDER"], filename)

    assert os.path.exists(file_path), "File was not found: '" + str(filename) + "'"

    with open(file_path) as csvfile:
        return [row for row in csv.DictReader(csvfile, delimiter=",")]


def empty_directory(dir_path):
    """delete all the contents inside the given path
    """
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            os.remove(os.path.join(root, file))
        for directory in dirs:
            shutil.rmtree(os.path.join(root, directory))
