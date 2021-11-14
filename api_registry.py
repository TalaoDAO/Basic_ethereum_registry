from web3.middleware import geth_poa_middleware
from web3 import Web3
import json
import logging
logging.basicConfig(level=logging.INFO)
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# use case data to setup the trusted issuer registry 
issuer_data_1 = open("trustmydata/talao_data.json", "r").read()
did_1 = "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250"  
issuer_data_2 = open("trustmydata/cci_data.json", "r").read()
did_2 = "did:ethr:0x8A837ACCd6Dc24dbBd408dcf4EB98A6C8413631A"  
issuer_data_3 = open("trustmydata/myguichet_data.json", "r").read()
did_3 = "did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7"  
issuer_data_4 = open("trustmydata/bank_data.json", "r").read()
did_4 = "did:ethr:0x59dc708328b2c0031786B2F13911c35764De4A49"

# data to setup the schema registry
schema_data_1= open("trustmydata/schema_1.json", "r").read()
id_1 = "123"

# For Talao POA network this is a signer address and private key with some eth to pay transaction fees
# use local msg sender private key with some eth
address = "0x461B99bCBdaD9697d299FDFe0879eC04De256DA1"
private_key = "4203a13f5b04d83bf35d00982c8d7ed3af7c99ee446300da7a35705b135a4164"

# smart contract address and abi, this comes from remix
registries_abi = open("trustmydata/registry.abi", "r").read()
registries_contract = "0xe14C84119B20f1E5732d9ADF8869546E6d564dC2"

# use an IPCProvider if this program runs on the Geth IPC node, if not you need a rpc node
# ex : w3 = Web3(Web3.IPCProvider("/home/admin/Talaonet/node1/geth.ipc", timeout=20))
w3 = Web3(Web3.HTTPProvider("https://talao.co/rpc"))

# for POA compatibility
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(registries_contract,abi=registries_abi)


# API to get Issuer data
# example https://talao.co/registry/api/v1/issuer?did=did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7
@app.route('/registry/api/v1/issuer', methods=['GET'])
def get_issuer() :
    try :
        did = request.args['did']
        issuer_data = contract.functions.get_issuer_data(did).call()
        if not issuer_data :
            logging.error("DID not found")
            return jsonify("DID not found"), 400
        return jsonify(json.loads(issuer_data))
    except :
        logging.error("Request mal formed")
        return jsonify ("request malformed"), 400


# API to get Schema data
@app.route('/registry/api/v1/schema', methods=['GET'])
def get_schema() :
    try :
        id = request.args['id']
        schema_data = contract.functions.get_schema_data(id).call()
        if not schema_data :
            logging.error("Schema not found")
            return jsonify("Schema not found"), 400
        return jsonify(json.loads(schema_data))
    except :
        logging.error("Request mal formed")
        return jsonify ("request malformed"), 400


# Call this API to init smart contract data. Use once it is enough
@app.route('/registry/api/v1/init', methods=['GET'])
def api_set_issuer() :
    try : 
        set_issuer(did_1, issuer_data_1)
        set_issuer(did_2, issuer_data_2)
        set_issuer(did_3, issuer_data_3)
        set_issuer(did_4, issuer_data_4)
        set_schema(id_1, schema_data_1)
        logging.info("all registries updated")
        return jsonify("all registries updated")
    except :
        logging.error("registries update failed")
        return jsonify("registry update failed"), 500


# this is needed within the schema.json
# https://talao.co/schemas/residentcard/2020/v1
@app.route('/schemas/residentcard/2020/v1', methods=['GET'])
def residentcard() :
    return jsonify(json.load(open("trustmydata/residentcard_schema.jsonld", "r")))


# send transaction to POA for issuer registry init
def set_issuer(did, json_string) :
    nonce = w3.eth.get_transaction_count(address)
    txn = contract.functions.set_issuer_data(did, json_string).buildTransaction({'chainId': 50000,'gas': 1000000,'gasPrice': w3.toWei("10", 'gwei'),'nonce': nonce,})
    signed_txn = w3.eth.account.sign_transaction(txn,private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    receipt = w3.eth.wait_for_transaction_receipt(hash, timeout=2000, poll_latency=1)
    return receipt['status']


# send transaction to POA for schema registry init
def set_schema(did, json_string) :
    nonce = w3.eth.get_transaction_count(address)
    txn = contract.functions.set_schema_data(did, json_string).buildTransaction({'chainId': 50000,'gas': 1000000,'gasPrice': w3.toWei("10", 'gwei'),'nonce': nonce,})
    signed_txn = w3.eth.account.sign_transaction(txn,private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    receipt = w3.eth.wait_for_transaction_receipt(hash, timeout=2000, poll_latency=1)
    return receipt['status']


# pytest api_registry.py
def test_call():
    did = 'did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7'
    dict_data = {
        "did": [
            "did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7"
        ], 
        "eidasCertificatePem": [
            {}
        ], 
        "organizationInfo": {
            "currentAddress": "11, Rue Notre-Dame L-2240 Luxembourg", 
            "id": "", 
            "issuerDomain": [
            "compell.io"
            ], 
            "legalName": "My Guichet", 
            "vatNumber": "", 
            "website": "https://guichet.public.lu/en/myguichet.html"
        }, 
        "preferredName": "My Guichet", 
        "serviceEndpoints": [
            {}, 
            {}
        ]
    }
    assert json.loads(contract.functions.get_issuer_data(did).call()) == dict_data
    id = str(uuid.uuid4())
    text = id + '_test'
    set_issuer(id, text)
    assert contract.functions.get_issuer_data(id).call() == text

# MAIN entry point for local running, use NGINX + gunicorn, ... for remote and production,
if __name__ == '__main__':
    logging.info('flask serveur init')
    app.run(host = "0.0.0.0", port= 9000, debug = True)
