# Copyright 2016 Intel Corporation
# Copyright 2017 Wind River Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import hashlib
import logging
import json
from collections import OrderedDict

from sawtooth_sdk.processor.state import StateEntry
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader

LOGGER = logging.getLogger(__name__)


class SupplierTransactionHandler:
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'supplier'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def encodings(self):
        return ['csv-utf8']

    @property
    def namespaces(self):
        return [self._namespace_prefix]
    
 
    def apply(self, transaction, state_store):

        # Deserialize the transaction and verify it is valid
        supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id,signer = extract_transaction(transaction)

      
        if  supplier_id  == "":
            raise InvalidTransaction("supplier Data is required")

        if action == "":
            raise InvalidTransaction("Action is required")

        # Checks to see if the action is valid or not
        if action not in ("create","list-supplier","show-supplier","AddPart"):
            raise InvalidTransaction("Invalid Action '{}'".format(action))

        data_address = self._namespace_prefix \
            + hashlib.sha512(supplier_id.encode("utf-8")).hexdigest()

        # Retrieve data from address
        state_entries = state_store.get([data_address])
        
        # Checks to see if the list is not empty
        if len(state_entries) != 0:
            try:
                   
                    stored_supplier_id, stored_supplier_str = \
                    state_entries[0].data.decode().split(",",1)
                             
                    stored_supplier = json.loads(stored_supplier_str)
            except ValueError:
                raise InternalError("Failed to deserialize data.")
            
        else:
            stored_supplier_id = stored_supplier = None
            
        # Validate the envelope data
        if action == "create" and stored_supplier_id is not None:
            raise InvalidTransaction("Invalid Action-supplier already exists.")
               
           
        if action == "create":
            supplier = create_supplier(supplier_id,short_id,supplier_name,passwd,supplier_url)
            stored_supplier_id = supplier_id
            stored_supplier = supplier
            _display("Created a supplier.")
            
        if action == "AddPart":
            if part_id not in stored_supplier_str:
                supplier = add_part(part_id,stored_supplier)
                stored_supplier = supplier
   
        stored_cat_str = json.dumps(stored_supplier)
        addresses = state_store.set([
            StateEntry(
                address=data_address,
                data=",".join([stored_supplier_id, stored_cat_str]).encode()
            )
        ])
        
        if len(addresses) < 1:
            raise InternalError("State Error")
        


def add_part(uuid,parent_supplier):
    
    sub_part_list = parent_supplier['parts']
    sub_part_dic = {'part_id': uuid}
    sub_part_list.append(sub_part_dic)
    parent_supplier['parts'] = sub_part_list
    return parent_supplier     

# Create an envelope payload record
def create_supplier(supplier_id,short_id,supplier_name,passwd,supplier_url):
    supplierD = OrderedDict()
    supplierD = {'supplier_id': supplier_id,'short_id':short_id,'supplier_name': supplier_name,'passwd': passwd,'supplier_url': supplier_url,'parts':[]}
    return supplierD 


def extract_transaction(transaction):
    
    header = TransactionHeader()
    header.ParseFromString(transaction.header)
    # The transaction signer is the player
    signer = header.signer_pubkey

    try:
        supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id = transaction.payload.decode().split(",")
    except ValueError:
        raise InvalidTransaction("Invalid payload serialization")
    
    return supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id, signer

def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")
        
