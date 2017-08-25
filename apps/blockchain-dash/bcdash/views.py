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
from bcdash.api import get_blockchain_nodes, get_ledger_api_address, ping_node, \
    get_bc_suppliers, get_bc_parts, get_bc_categories, get_bc_envelopes
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

@app.route("/ledger/components")
def query_ledger_components():
    """get parts, suppliers, envelopes, and categories from the blockchain ledger service
    """
    try:

        categories = get_bc_categories()
        suppliers = get_bc_suppliers()
        parts = get_bc_parts()
        envelopes = get_bc_envelopes()

        supplier_parts = {}

        categories_by_uuid = {}
        for category in categories:
            categories_by_uuid[category["uuid"]] = category

        envelopes_by_uuid = {}
        for envelope in envelopes:
            envelopes_by_uuid[envelope["uuid"]] = envelope


        for supplier in suppliers:
            supplier_parts[supplier["uuid"]] = {"supplier": supplier, "parts": []}

        for part in parts:

            category_uuids = [category["category_id"] for category in part.pop("categories")]
            part["categories"] = []

            envelope_uuids = [envelope["envelope_id"] for envelope in part.pop("envelopes")]
            part["envelopes"] = []

            #
            # handle invalid category UUID

            for category_uuid in category_uuids:
                if category_uuid in categories_by_uuid:
                    part["categories"].append(categories_by_uuid[category_uuid])

            for envelope_uuid in envelope_uuids:
                if envelope_uuid in envelopes_by_uuid:
                    part["envelopes"].append(envelopes_by_uuid[envelope_uuid])

            #
            # attach envelope
            #

            found_supplier = False
            for supplier in part["suppliers"]:
                supplier_uuid = supplier["supplier_id"]
                if supplier_uuid in supplier_parts:
                    found_supplier = True
                    supplier_parts[supplier_uuid]["parts"].append(part)

            if not found_supplier:
                if not "unknown" in supplier_parts:
                    supplier_parts["unknown"] = {"supplier": \
                        {"name": "[Unknown] Supplier UUID was not found."}, \
                        "parts": []}

                supplier_parts["unknown"]["parts"].append(part)

        return render_template("components.html", suppliers=suppliers,
            supplier_parts=supplier_parts,
            parts_count=len(parts),
            suppliers_count=len(suppliers),
            envelopes_count=len([envelope for envelope in envelopes \
                if envelope["content_type"] == "this"]))

    except ConnectionError:
        return render_page("error", error_message="The conductor service refused connection." \
            + " Could not query blockchain status at this time. Please try again later.")

    except APIError as error:
        return render_page("error", error_message="Failed to call the conductor API service" \
            + " to query the blockchain. " + str(error))
























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


        # envelope_count=len(envelopes), \
        # supplier_count=len(suppliers), \
        # part_count=len(parts))

        return render_page("home", uptime=uptime_sample, \
            apps=apps, \
            nodes=get_blockchain_nodes(), \
            ledger_api_address="http://" + ledger_ip + ":" + str(ledger_port) + "/api/sparts", \
            envelope_count=0, \
            supplier_count=0, \
            part_count=0)

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
