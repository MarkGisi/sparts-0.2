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
import sys
import argparse

from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.client.config import get_log_dir
from sawtooth_sdk.client.config import get_log_config
from sawtooth_sdk.client.log import init_console_logging
from sawtooth_sdk.client.log import log_configuration
from sawtooth_supplier.processor.handler import SupplierTransactionHandler



def parse_args(args):
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument('endpoint',
                        nargs='?',
                        default='tcp://localhost:4004',
                        help='Endpoint for the validator connection')
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase output sent to stderr')
    return parser.parse_args(args)

def main(args=sys.argv[1:]):
    opts = parse_args(args)
    processor = None
    try:
        processor = TransactionProcessor(url=opts.endpoint)
        log_config = get_log_config(filename="supplier_log_config.toml")
        if log_config is not None:
            log_configuration(log_config=log_config)
        else:
            log_dir = get_log_dir()
            # use the transaction processor zmq identity for filename
            log_configuration(
                log_dir=log_dir,
                name="supplier-" + str(processor.zmq_id)[2:-1])

        init_console_logging(verbose_level=opts.verbose)

      
        supplier_prefix = hashlib.sha512('supplier'.encode("utf-8")).hexdigest()[0:6]
        handler = SupplierTransactionHandler(namespace_prefix=supplier_prefix)

        processor.add_handler(handler)

        processor.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Error: {}".format(e))
    finally:
        if processor is not None:
            processor.stop()