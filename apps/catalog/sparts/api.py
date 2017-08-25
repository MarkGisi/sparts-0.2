"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

Ledger API service calls
"""

import json
import requests
from requests.exceptions import ReadTimeout, ConnectionError
from sparts import app, jsonify
from sparts.exceptions import APIError


API_SERVER = app.config["BLOCKCHAIN_API"]


@app.route("/api/sparts/ping")
def ping_handler():
    """respond to a simple "ping" request, indicating whether this app (sparts catalog) is running
    """
    return jsonify({"status": "success"})

def get_uuid():
    """call the conductor service to a unique UUID
    """
    try:
        response = requests.get(API_SERVER + "/uuid", timeout=app.config["DEFAULT_API_TIMEOUT"])
    except ReadTimeout:
        raise APIError("Failed to get new UUID. Conductor service timed out")
    except ConnectionError:
        raise APIError("Failed to get new UUID. " \
            + "The conductor service refused connection or is not running.")

    if response.status_code != 200:
        raise APIError("Failed to call the blockchain API to get a UUID. Conductor server " \
            + "responded with status " + response.status_code)

    try:
        data = response.json()
    except:
        raise APIError("Failed to parse the JSON in the call to the conductor service " \
            + "to retrieve a new UUID.")

    return data["uuid"]

def ping_node(node_api_url, timeout=app.config["DEFAULT_API_TIMEOUT"]):
    """ping a blockchain node and return its status
    """
    if not node_api_url:
        return "Node did not provide a ledger service API URL"

    try:
        response = requests.get(node_api_url + "/api/sparts/ping", timeout=timeout)
    except ReadTimeout:
        raise APIError("Failed to ping node. Conductor service timed out")
    except ConnectionError:
        raise APIError("Failed to ping node. " \
            + "The conductor service refused connection or is not running.")

    if response.status_code != 200:
        return "Down (HTTP " + str(response.status_code) + ")"

    try:
        data = response.json()
    except:
        return "Down' Returns invalid JSON."

    if "status" not in data:
        return "Down. Returns invalid JSON: missing 'status'"

    print(data)

    if data["status"] != "success":
        return "Down. Status: '" + str(data["status"]) + "'"

    return "Running"

def get_blockchain_nodes():
    """get a list of nodes running the ledger and their status from the conductor API
    """
    try:
        response = requests.get(API_SERVER + "/ledger_nodes", timeout=app.config["DEFAULT_API_TIMEOUT"])
    except ReadTimeout:
        raise APIError("Failed to get blockchain nodes. Conductor service timed out")
    except ConnectionError:
        raise APIError("Failed to get blockchain nodes. " \
            + "The conductor service refused connection or is not running.")

    print(API_SERVER + "/ledger/nodes")

    if response.status_code != 200:
        raise APIError("Failed to call the conductor service to get list of blockchain nodes. " \
            + "Server responded with status " + response.status_code)

    try:
        nodes = response.json()
    except:
        raise APIError("Failed to parse the JSON in the call to the conductor service " \
            + "to retrieve list of running blockchain nodes.")

    if "status" in nodes and nodes["status"] != "success":
        raise APIError("Failed to call the conductor service to get list of blockchain nodes. " \
            + "Server returned status '" + nodes["status"] + "'." )

    return nodes


def get_ledger_api_address():
    """get the address of the ledger service from the conductor

    Returns:
        (tuple) ip, port
    """
    try:
        response = requests.get(API_SERVER + "/ledger/address", \
            timeout=app.config["DEFAULT_API_TIMEOUT"])
    except ReadTimeout:
        raise APIError("Failed to get ledger API address. Conductor service timed out")
    except ConnectionError:
        raise APIError("Failed to get ledger API address. " \
            + "The conductor service refused connection or is not running.")

    if response.status_code != 200:
        raise APIError("Failed to retrieve the blockchain API server address.")

    try:
        ledger_address = response.json()
    except:
        raise APIError("Failed to parse the JSON response of the blockchain API server. Got:" \
            + " <br><br><pre>" + str(response.content) + "</pre>")

    if "ip_address" not in ledger_address or ledger_address["ip_address"] == "0.0.0.0":
        raise APIError("Failed to retrieve the blockchain API server address. " \
            + "Could not read a valid IP address. Got '" + str(ledger_address) + "'.")

    return ledger_address["ip_address"], ledger_address["port"]



def register_app_with_blockchain():
    """call the  conductor service to register this app (sparts catalog) on the supply chain network
    """
    data = {
        "uuid": "9fb84fa0-1716-4367-7012-61370e23028f",
        "api_url": "http://open.windriver.com:5000",
        "type": "website",
        "label": "Sparts Catalog"
    }

    if app.config["BYPASS_API_CALLS"]:
        return

    try:
        response = requests.post(API_SERVER + "/app/register", data=json.dumps(data), \
            headers={'Content-type': 'application/json'}, timeout=app.config["DEFAULT_API_TIMEOUT"])
    except ReadTimeout:
        raise APIError("Failed to register app with blockchain. Conductor service timed out")
    except ConnectionError:
        raise APIError("Failed to register app with blockchain. " \
            + "The conductor service refused connection or is not running.")

    if response.status_code != 200:
        raise APIError("Failed to register app with blockchain. Server responded with " \
            + "HTTP " + str(response.status_code))

    try:
        result = response.json()
    except:
        raise APIError("Failed to register app with blockchain. Invalid JSON return data " \
            + "'" + str(response.content)) + "'"

    if "status" not in result:
        raise APIError("Failed to register app with blockchain. Invalid JSON return data " \
            + ": Missing required field 'status'.")

    if result["status"] != "success":
        raise APIError("Failed to register app with blockchain. Server returned status '" \
            + str(result["status"]) + "'.")


def save_part_supplier_relation(part, supplier):
    call_blockchain_api("post", "/ledger/mapping/PartSupplier", {
        "part_uuid": part.uuid,
        "supplier_uuid": supplier.uuid
    })


def save_part_category_relation(part, category):
    call_blockchain_api("post", "/ledger/parts/AddCategory", {
        "part_uuid": part.uuid,
        "category_uuid": category.uuid
    })

def save_part_envelope_relation(part, envelope):
    call_blockchain_api("post", "/ledger/parts/AddEnvelope", {
        "part_uuid": part.uuid,
        "envelope_uuid": envelope.uuid
    })


def get_blockchain_categories():
    """get list of part categories
    """
    return call_blockchain_api("get", "/ledger/categories")

def save_category_to_blockchain(category):
    call_blockchain_api("post", "/ledger/categories", {
        "uuid": category.uuid,
        "name": category.name,
        "description": category.description
    })

def save_supplier_to_blockchain(supplier):
    """save the given supplier on the blockchain by calling the ledger service
    """
    call_blockchain_api("post", "/ledger/suppliers", {
        "uuid": supplier.uuid,
        "short_id": "",
        "name": supplier.name,
        "passwd": supplier.password,
        "url": ""
    })

def save_part_to_blockchain(part):
    """save the given part on the blockchain by calling the ledger service
    """
    call_blockchain_api("post", "/ledger/parts", {
        "uuid": part.uuid,
        "name": part.name,
        "checksum": "",
        "version": part.version,
        "src_uri": part.url,
        "licensing": part.licensing,
        "label": "",
        "description": part.description
    })

def save_envelope_to_blockchain(envelope):
    """save the given envelope on the blockchain by calling the ledger service
    """
    call_blockchain_api("post", "/ledger/envelopes", json.loads(envelope.toc))


def call_blockchain_api(method, url, data={}):
    """ call the blockchain ledger service with the given method (post or get), url, and data.
    """
    if app.config["BYPASS_API_CALLS"]:
        return {}

    bc_server_ip, bc_server_port = get_ledger_api_address()

    request_url = "http://" + bc_server_ip + ":" + str(bc_server_port) + "/api/sparts" + url

    print("[" + method + "] " + request_url)

    result = None

    try:

        if method == "get":
            result = requests.get(request_url, params=data, timeout=app.config["DEFAULT_API_TIMEOUT"])

        elif method == "post":
            result = requests.post(request_url, data=json.dumps(data), \
                headers={'Content-type': 'application/json'}, timeout=app.config["DEFAULT_API_TIMEOUT"])

        else:
            raise APIError("Bad method passed to function 'call_blockchain_api")

    except ReadTimeout:
        raise APIError("Blockchain ledger service timed out.")

    except ConnectionError:
        raise APIError("Blockchain ledger service refused connection.")


    if result.status_code != 200:
        raise APIError("The blockchain API server responeded with HTTP " + \
            str(result.status_code) + ".")

    # hack to bypass invalid JSON value when blockchain is empty
    if result.content == "[{[]}]":
        return []

    json_result = None
    try:
        json_result = result.json()
    except:
        raise APIError("Failed to parse the following JSON data in the response of the blockchain" \
            +" API server.<br><br><pre>" + str(result.content) + "</pre>")

    if "status" in json_result:
        # raise APIError("Invalid JSON in the response of the ledger service at " + url \
        #     + "Missing required field 'status'")

        if json_result["status"] == "failed":
            if "error_message" in json_result:
                raise APIError("Leger service call to '" + url + "' failed. " \
                    + "The API server provided the following reason: '" \
                    + json_result["error_message"] + "'.")

            else:
                raise APIError("Leger service call to '" + url + "' failed." + \
                    "No error_message was provided by the server.")

        if json_result["status"] != "success":
            raise APIError("Leger service call to '" + url + "' returned 'status' = '" \
                + json_result["status"] + "'.")

    return json_result
