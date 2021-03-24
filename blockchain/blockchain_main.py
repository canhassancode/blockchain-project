import binascii
from time import time
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from _collections import OrderedDict
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from uuid import uuid4
import json
import hashlib
import requests
from urllib.parse import urlparse

#############################################
# Creating the Blockchain with all its
# characteristics
#############################################

MINING_SENDER = "The Overseer"      # The blockchain
MINING_REWARD = 1                  # Adds 1 to the reputation of the individual
# Difficulty for the miner in relation to the nonce
MINING_DIFFICULTY = 2


class Blockchain:

    def __init__(self):
        self.chain_data = []  # empty list to populate the data uploaded to blockchain TODO
        self.chain = []  # containing the list of blocks on the blockchain TODO
        self.nodes = set()  # Add a list of nodes to each node TODO
        # id of node. replaces the - with empty TODO
        self.node_id = str(uuid4()).replace('-', '')
        # Creating Genesis Block
        self.create_block(0, '00')  # nonce and previous hash

    def create_block(self, nonce, previous_hash):
        # Adds a block of data to the blockchain

        block = {
            # with each block, add 1 to length of blockchain
            'block_number': len(self.chain) + 1,
            'timestamp': time(),
            'data': self.chain_data,
            'nonce': nonce,
            'previous_hash': previous_hash
        }

        # reset current data once the block has been added to the chain
        self.chain_data = []
        self.chain.append(block)
        return block

    def register_node(self, node_url):
        # breaks down the parsed url to paramaters used(netloc and path)
        parsed_url = urlparse(node_url)
        if parsed_url.netloc:  # network location
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    # method verifies the signature
    @staticmethod  # self not used
    def verify_transaction_signature(public_key, signature, data):
        public_key = RSA.importKey(binascii.unhexlify(public_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(data).encode('utf8'))  # hash
        try:
            # library does not explicitly return
            verifier.verify(h, binascii.unhexlify(signature))
            return True
        except ValueError:
            return False

    # refers to the mining process of guessing the nonce
    @staticmethod
    def valid_proof(chain_data, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(chain_data) + str(last_hash) + str(nonce)).encode('utf8')
        h = hashlib.new('sha256')
        h.update(guess)
        guess_hash = h.hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    # TODO: Necessary for DeepFake?
    # proof of work for blockchain mining
    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0
        while self.valid_proof(self.chain_data, last_hash, nonce) is False:
            nonce += 1
        return nonce

    # generates a hash on request. Generates current and previous hash
    @staticmethod
    def hash(block):
        # Important to sort keys so that the dictionary retains its ordered format
        block_string = json.dumps(block, sort_keys=True).encode('utf8')
        h = hashlib.new('sha256')
        h.update(block_string)
        return h.hexdigest()

    # determines validity of the chain. I.e. Chain length x is greater than y. Remove or overwrite
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            # passed in variable of block with 'previous_hash'
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False

            chain_data = block['data'][:-1]
            # TODO: Add more here when looking into
            data_elements = ['public_key', 'data_hash']
            chain_data = [OrderedDict((x, data[x]) for x in data_elements)
                          for information in chain_data]

            if not self.valid_proof(chain_data, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    # resolve conflicts for length of chain, if length is greater than overwrite dependent
    # on verfified data transactions
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        # compare with length of other chains in network
        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get('http://' + node + '/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

            if new_chain:
                self.chain = new_chain
                return True

            return False

    # submit data to the blockchain after verfying the signature of the data
    # TODO: append more to this method if required
    def submit_data(self, public_key, signature, data_hash, reputation):
        # Validate the Signature
        # Reward the Verfier for proving authenticity

        data = OrderedDict({
            'public_key': public_key,
            'data_hash': data_hash,
            'reputation': reputation
        })

        # Rewarding the Verifier from the Blockchain itself " THE OVERSEER"
        if public_key == MINING_SENDER:
            self.chain_data.append(data)
            return len(self.chain) + 1
        else:
            # data uploaded to block verification
            signature_verification = self.verify_transaction_signature(
                public_key, signature, data)
            if signature_verification:
                # append to node. adding each block
                self.chain_data.append(data)
                return len(self.chain) + 1
            else:
                return False


#############################################
# Instantiate the Blockchain, flask and
# CORS. Index and configure build
#############################################

blockchain = Blockchain()
app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    # render template looks at template folder by default. Flask module.
    return render_template('index.html')


@app.route('/configure')
def configure():
    # render template looks at template folder by default. Flask module.
    return render_template('configure.html')

#############################################
# Retrieve data and chain information
#############################################


@app.route('/data-get', methods=['GET'])
def get_data():
    chain_data = blockchain.chain_data
    response = {'chain_data': chain_data}  # !CHECK IF THIS IS RIGHT!
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

#############################################
# Verifying (Mining) the data on the chain
#############################################


@app.route('/verify', methods=['GET'])
def verify():
    # Running the PROOF OF WORK algorithm from earlier
    nonce = blockchain.proof_of_work()

    blockchain.submit_data(
        public_key=MINING_SENDER,
        signature='',
        data_hash='',
        reputation=MINING_REWARD
    )

    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)

    response = {
        'message': 'New block created',
        'block_number': block['block_number'],
        'data': block['data'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200

#############################################
# New data recieved
#############################################


@app.route('/data-new', methods=['POST'])
def new_data():
    values = request.form

    # TODO: Append if required for more inputs

    required = ['confirm_public_key', 'signature', 'data_hash']

    if not all(x in values for x in required):
        return 'Missing values', 400

    data_result = blockchain.submit_data(
        values['confirm_public_key'],
        values['signature'],
        values['data_hash'],
        'test feature for reputation'
    )

    if data_result == False:
        response = {'message': 'Invalid Data/Signature'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction Successful. Added to block ' +
                    str(data_result)}  # number of next
        return jsonify(response), 201


@app.route('/verify-hash', methods=['GET'])
def verify_hash():
    
    response = {'chain': blockchain.chain,
    'chain_data': blockchain.chain_data}

    return jsonify(response), 200

#############################################
# Nodes get and register to blockchain
# Additionally, it resolves the nodes
#############################################


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.form
    nodes = values.get('nodes').replace(' ', '').split(',')

    if nodes is None:
        return 'Error: Please supply a valid list of nodes', 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nodes have been added',
        'total_nodes': [node for node in blockchain.nodes]
    }

    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['POST'])
def resolve_nodes():
    return 200

#############################################
# Localhost for Blockchain
#############################################


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()  # calls a function to parse arguments/parameters
    parser.add_argument('-p', '--port', default=5001, type=int,
                        help="port to listen to")  # sets args by adding to
    # parse. this relates to port
    args = parser.parse_args()  # sets the values of the added parse to args
    port = args.port  # generates the port variable from args

    # runs flask code with these parameters set, debug is true so
    app.run(host='127.0.0.1', port=port, debug=True)
    # server does not constantly restart
