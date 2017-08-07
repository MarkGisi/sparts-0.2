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
import datetime
import json
from flask import render_template, Response, jsonify
from requests.exceptions import ReadTimeout, ConnectionError
from bcdash import app
from bcdash.api import get_blockchain_nodes, get_ledger_api_address, ping_node
from bcdash.exceptions import APIError

def render_page(template, title="", *args, **kwargs):
    return render_template("site_template.html", page_title=title, \
        template=template, *args, **kwargs, page=template)

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
    """display status information about the blockchain. Eventually, this might be its own app.
    """

    uptime_sample = str(datetime.datetime.now() - datetime.datetime(2017, 7, 9, 12, 44))
    uptime_sample = ".".join(uptime_sample.split(".")[:-1])

    # dict supplier.id -> list of part instances by this supplier
    supplier_parts = {}

    # dict supplier.id -> supplier instance

    apps = ["Sparts", "BC Dash"]

    try:

        ledger_ip, ledger_port = get_ledger_api_address()

        categories = [
            {
                "uuid": "b7c0cca2-421d-4bd1-7bb8-da4b33aaebd6",
                "name": "operating-systems",
                "description" : "Operating Systems"
            },
            {
                "uuid": "4d445cd5-b15e-43a5-7cea-fbb627835b77",
                "name": "containers",
                "description" : "Containers"
            },
            {
                "uuid": "940991a2-3f64-417b-7618-8cb810482196",
                "name": "libraries",
                "description" : "Libraries"
            },
            {
                "uuid": "92edccef-0b07-4e87-6928-216483bce4c6",
                "name": "drivers",
                "description" : "Drivers & Firmware"
            }
        ]

        suppliers = [
            {
                "uuid": "1e105fe8-1e1d-408a-4de1-c76e301ba993",
                "short_id": "",
                "name": "wind river",
                "password": "123",
                "url": "wrs.com"
            },
            {
                "uuid": "46bfba18-270a-431e-68fc-2b5385c15e77",
                "short_id": "",
                "name": "intel",
                "password": "123",
                "url": "intel.com"
            }
        ]

        parts = [
            {
                "uuid": "a3ee96e8-2eb9-4c9d-40a4-2c996388c386",
                "name": "Test Part",
                "checksum": "123",
                "version": "1.2",
                "src_uri": "",
                "url": "",
                "licensing": "MIT",
                "label": "test",
                "description": "123",
                "categories": ["4d445cd5-b15e-43a5-7cea-fbb627835b77", "940991a2-3f64-417b-7618-8cb810482196"],
                "suppliers": ["1e105fe8-1e1d-408a-4de1-c76e301ba993"],
                "envelope_uuid": ""
            },
            {
                "uuid": "6b73bf6e-4dd7-4d7f-50d0-154c0c09d0e9",
                "name": "Another part",
                "checksum": "123",
                "version": "1.54",
                "src_uri": "",
                "url": "",
                "licensing": "GPL",
                "label": "test",
                "description": "15341251",
                "categories": ["92edccef-0b07-4e87-6928-216483bce4c6"],
                "suppliers": ["46bfba18-270a-431e-68fc-2b5385c15e77"],
                "envelope_uuid": ""
            }
        ]

        envelopes = []

        supplier_parts = {}

        categories_by_uuid = {}
        for category in categories:
            categories_by_uuid[category["uuid"]] = category

        for supplier in suppliers:
            supplier_parts[supplier["uuid"]] = {"supplier": supplier, "parts": []}

        for part in parts:

            category_uuids = part.pop("categories")
            part["categories"] = []

            #
            # handle invalid category UUID

            for category_uuid in category_uuids:
                if category_uuid in categories_by_uuid:
                    part["categories"].append(categories_by_uuid[category_uuid])


            part["envelope"] = []
            #
            # attach envelope
            #

            found_supplier = False
            for supplier_uuid in part["suppliers"]:
                if supplier_uuid in supplier_parts:
                    found_supplier = True
                    supplier_parts[supplier_uuid]["parts"].append(part)

            if not found_supplier:
                if not "unknown" in supplier_parts:
                    supplier_parts["unknown"] = {"supplier": \
                        {"name": "Unknown supplier. UUID was not found on the blockchain."}, \
                        "parts": []}

                supplier_parts["unknown"]["parts"].append(part)




        return render_page("home", uptime=uptime_sample, \
            suppliers=suppliers, supplier_parts=supplier_parts, apps=apps, \
            nodes=get_blockchain_nodes(), \
            ledger_api_address="http://" + ledger_ip + ":" + str(ledger_port) + "/api/sparts", \
            envelope_count=len(envelopes), \
            supplier_count=len(suppliers), \
            part_count=len(parts))

    except ConnectionError:
        return render_page("error", error_message="The conductor service refused connection." \
            + " Could not query blockchain status at this time. Please try again later.")

    except APIError as error:
        return render_page("error", error_message="Failed to call the conductor API service. " \
            + str(error))


@app.route("/blockchain/nodes/status/<uuid>")
def get_node_status(uuid):
    """json route for pinging a node and returning its status
    """
    selected_node = None
    for node in get_blockchain_nodes():
        if node["uuid"] == uuid:
            selected_node = node
            break

    if selected_node is None:
        return jsonify({"status": "Down. Node UUID was not found on the network."})

    if "api_url" not in node:
        return jsonify({"status": "Invalid conductor response. No api_url."})

    try:
        node_status = ping_node(node["api_url"], timeout=5)
    except ReadTimeout:
        node_status = "Down. Timed out."
    except ConnectionError:
        node_status = "Down. Connection refused."

    return jsonify({"status": node_status})
