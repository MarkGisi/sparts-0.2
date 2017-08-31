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


class PartTransactionHandler:
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'part'

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
        pt_id,pt_name,checksum,version,src_uri,licensing,label,description,action,envelope_id,category_id,supplier_id,signer = extract_transaction(transaction)

      
        if  pt_id  == "":
            raise InvalidTransaction("part Data is required")

        if action == "":
            raise InvalidTransaction("Action is required")

        # Checks to see if the action is valid or not
        if action not in ("create","list-part","show-part","AddEnvelope","AddCategory","AddSupplier"):
            raise InvalidTransaction("Invalid Action '{}'".format(action))

        data_address = self._namespace_prefix \
            + hashlib.sha512(pt_id.encode("utf-8")).hexdigest()

        # Retrieve data from address
        state_entries = state_store.get([data_address])
        
        # Checks to see if the list is not empty
        if len(state_entries) != 0:
            try:
                   
                    stored_pt_id, stored_pt_str = \
                    state_entries[0].data.decode().split(",",1)          
                    stored_pt = json.loads(stored_pt_str)
            except ValueError:
                raise InternalError("Failed to deserialize data.")
            
        else:
            stored_pt_id = stored_pt = None
            
        
        if action == "create" and stored_pt_id is not None:
            raise InvalidTransaction("Invalid Action-part already exists.")
               
           
        if action == "create":
            pt = create_part(pt_id,pt_name,checksum,version,src_uri,licensing,label,description)
            stored_pt_id = pt_id
            stored_pt = pt
            _display("Created a part.")
            
        if action == "AddEnvelope":
            if envelope_id not in stored_pt_str:
                pt_env = add_envelope(envelope_id,stored_pt)
                stored_pt = pt_env
            
        if action == "AddSupplier":
            if supplier_id not in stored_pt_str:
                pt_supp = add_supplier(supplier_id,stored_pt)
                stored_pt = pt_supp
        
        if action == "AddCategory":
            if category_id not in stored_pt_str:
                pt_cat = add_category(category_id,stored_pt)
                stored_pt = pt_cat
   
        stored_pt_str = json.dumps(stored_pt)
        addresses = state_store.set([
            StateEntry(
                address=data_address,
                data=",".join([stored_pt_id, stored_pt_str]).encode()
            )
        ])
        
        if len(addresses) < 1:
            raise InternalError("State Error")
        


def add_envelope(uuid,parent_pt):
    
    pt_envelope_list = parent_pt['envelopes']
    pt_envelope_dic = {'envelope_id': uuid}
    pt_envelope_list.append(pt_envelope_dic)
    parent_pt['envelopes'] = pt_envelope_list
    return parent_pt  


def add_supplier(uuid,parent_pt):
    
    pt_supplier_list = parent_pt['suppliers']
    pt_supplier_dic = {'supplier_id': uuid}
    pt_supplier_list.append(pt_supplier_dic)
    parent_pt['suppliers'] = pt_supplier_list
    return parent_pt     

def add_category(uuid,parent_pt):
    
    pt_cat_list = parent_pt['categories']
    pt_cat_dic = {'category_id': uuid}
    pt_cat_list.append(pt_cat_dic)
    parent_pt['categories'] = pt_cat_list
    return parent_pt        


def create_part(pt_id,pt_name,checksum,version,src_uri,licensing,label,description):
    pt = {'pt_id': pt_id,'pt_name': pt_name,'checksum': checksum,'version': version,'src_uri':src_uri,'licensing':licensing,'label':label,'description':description,'envelopes':[],'suppliers':[],'categories':[]}
    return pt
        

def extract_transaction(transaction):
    
    header = TransactionHeader()
    header.ParseFromString(transaction.header)
    # The transaction signer is the player
    signer = header.signer_pubkey

    try:
        pt_id,pt_name,checksum,version,src_uri,licensing,label,description,action,envelope_id,category_id,supplier_id = transaction.payload.decode().split(",")
    except ValueError:
        raise InvalidTransaction("Invalid payload serialization")
    
    return pt_id,pt_name,checksum,version,src_uri,licensing,label,description,action,envelope_id,category_id,supplier_id, signer

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
        
