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
from bcdash import app, jsonify
from bcdash.exceptions import APIError

API_SERVER = app.config["BLOCKCHAIN_API"]

@app.route("/api/sparts/ping")
def ping_handler():
    """respond to a simple "ping" request, indicating whether this app (bcdash catalog) is running
    """
    return jsonify({"status": "success"})

def get_uuid():
    """call the conductor service to a unique UUID
    """
    response = requests.get(API_SERVER + "/uuid", timeout=app.config["DEFAULT_API_TIMEOUT"])

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

    response = requests.get(node_api_url + "/api/sparts/ping", timeout=timeout)

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
    response = requests.get(API_SERVER + "/ledger_nodes", timeout=app.config["DEFAULT_API_TIMEOUT"])

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
    response = requests.get(API_SERVER + "/ledger/address", \
        timeout=app.config["DEFAULT_API_TIMEOUT"])

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
    """call the  conductor service to register this app (bcdash catalog) on the supply chain network
    """
    data = {
        "uuid": "9fb84fa0-1716-4367-7012-61370e23028f",
        "api_url": "http://open.windriver.com:5000",
        "type": "website",
        "label": "Sparts Catalog"
    }

    if app.config["BYPASS_API_CALLS"]:
        return

    response = requests.post(API_SERVER + "/app/register", data=json.dumps(data), \
        headers={'Content-type': 'application/json'}, timeout=app.config["DEFAULT_API_TIMEOUT"])

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
