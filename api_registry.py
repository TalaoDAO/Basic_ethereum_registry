from web3.middleware import geth_poa_middleware
from web3 import Web3
import json
import logging
logging.basicConfig(level=logging.INFO)
from flask import Flask, request, jsonify

app = Flask(__name__)

# data to setup issuer data
issuer_data_1 = open("trustmydata/talao_data.json", "r").read()
did_1 = "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250"  
# data to setup schema data
schema_data_1= open("trustmydata/schema_1.json", "r").read()
id_1 = "123"

# signer address and private key
address = "0x461B99bCBdaD9697d299FDFe0879eC04De256DA1"
private_key = "4203a13f5b04d83bf35d00982c8d7ed3........6300da7a35705b135a4164" #fake ,key

# smart contract address and abi
registries_abi = open("trustmydata/registry.abi", "r").read()
registries_contract = "0xe14C84119B20f1E5732d9ADF8869546E6d564dC2"

""" 
use an IPCProvider for a server local instance
ex : w3 = Web3(Web3.IPCProvider("/home/admin/Talaonet/node1/geth.ipc", timeout=20))
"""
w3 = Web3(Web3.HTTPProvider("https://talao.co/rpc"))

# for POA compatibility
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(registries_contract,abi=registries_abi)


# API to get Issuer data
@app.route('/registry/api/v1/issuer', methods=['GET'])
def get_issuer() :
    try :
        did = request.args['did']
        issuer_data = contract.functions.get_issuer_data(did).call()
        if not issuer_data :
            return jsonify("did not found")
        return jsonify(json.loads(issuer_data))
    except :
        return jsonify ("request malformed")


# API to get Schema data
@app.route('/registry/api/v1/schema', methods=['GET'])
def get_schema() :
    try :
        id = request.args['id']
        schema_data = contract.functions.get_schema_data(id).call()
        if not schema_data :
            return jsonify("did not found")
        return jsonify(json.loads(schema_data))
    except :
        return jsonify ("request malformed")


# API to init smart contract data. Use once it is enough !
@app.route('/registry/api/v1/init', methods=['GET'])
def api_set_issuer() :
    if not set_issuer(did_1, issuer_data_1) :
        return jsonify("issuer registry updated failed")
    if not set_schema(id_1, schema_data_1) :
        return jsonify("schema registry update failed")
    return jsonify("registries updated !")


# https://talao.co/schemas/residentcard/2020/v1
@app.route('/schemas/residentcard/2020/v1', methods=['GET'])
def residentcard() :
    return jsonify(json.load(open("trustmydata/residentcard_schema.jsonld", "r")))


def set_issuer(did, json_string) :
    nonce = w3.eth.get_transaction_count(address)
    txn = contract.functions.set_issuer_data(did, json_string).buildTransaction({'chainId': 50000,'gas': 1000000,'gasPrice': w3.toWei("10", 'gwei'),'nonce': nonce,})
    signed_txn = w3.eth.account.sign_transaction(txn,private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    receipt = w3.eth.wait_for_transaction_receipt(hash, timeout=2000, poll_latency=1)
    if not receipt['status'] :
        logging.error("transaction set issuer error")
        return False
    else :
        return True


def set_schema(did, json_string) :
    nonce = w3.eth.get_transaction_count(address)
    txn = contract.functions.set_schema_data(did, json_string).buildTransaction({'chainId': 50000,'gas': 1000000,'gasPrice': w3.toWei("10", 'gwei'),'nonce': nonce,})
    signed_txn = w3.eth.account.sign_transaction(txn,private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    receipt = w3.eth.wait_for_transaction_receipt(hash, timeout=2000, poll_latency=1)
    if not receipt['status'] :
        logging.error("transaction set schema error")
        return False
    else :
        return True


# MAIN entry point for local running, use NGINX + gunicorn, ... for remote and production,
if __name__ == '__main__':
    logging.info('flask serveur init')
    app.run(host = "0.0.0.0", port= 9000, debug = True)
