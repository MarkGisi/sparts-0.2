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
    suppliers = {}

    apps = ["Sparts", "BC Dash"]

    try:

        ledger_ip, ledger_port = get_ledger_api_address()

        # for supplier in db_session.query(Supplier).filter(Supplier.blockchain == True).all():
        #     suppliers[supplier.id] = supplier

        # for part in db_session.query(Part).filter(Part.blockchain == True).all():
        #     if part.supplier_id not in suppliers:
        #         continue

        #     if part.supplier.id not in supplier_parts:
        #         supplier_parts[part.supplier.id] = []
        #     supplier_parts[part.supplier.id].append(part)


        return render_page("home", uptime=uptime_sample, \
            suppliers=suppliers, supplier_parts=supplier_parts, apps=apps, \
            nodes=get_blockchain_nodes(), \
            ledger_api_address="http://" + ledger_ip + ":" + str(ledger_port) + "/api/bcdash", \
            part_count=sum([len(supplier_parts[supplier_id]) for supplier_id in supplier_parts]), \
            supplier_count=len(suppliers.items()), \
            envelope_count=sum([sum([1 for part in supplier_parts[supplier_id] if part.envelope]) \
            for supplier_id in supplier_parts]))

    except ConnectionError:
        return render_page("error", error_message="The conductor service refused connection." \
            + " Could not query blockchain status at this time. Please try again later.")

    except APIError as error:
        return render_page("error", error_message="Failed to call the conductor API service: " \
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
