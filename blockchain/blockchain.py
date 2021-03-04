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

MINING_SENDER = "The Blockchain"
MINING_REWARD = 1
MINING_DIFFICULTY = 2


class Blockchain:

    def __init__(self):
        self.transactions = []  # transaction data empty at first
        self.chain = []  # will contain list of blocks
        self.nodes = set()  # TODO: Add a list of nodes to each node
        self.node_id = str(uuid4()).replace('-', '') # id of node
        # create the genesis block
        self.create_block(0, '00')  # nonce and previous hash

    def create_block(self, nonce, previous_hash):
        """
        Add a block of transactions to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,  # every new block is added, +1 to chain length
                 'timestamp': time(),
                 'transactions': self.transactions,
                 'nonce': nonce,
                 'previous_hash': previous_hash}

        # reset current list of transactions once added to block
        self.transactions = []
        self.chain.append(block)
        return block

    def register_node(self, node_url):
        parsed_url = urlparse(node_url)
        if parsed_url.netloc:  # network location
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    @staticmethod  # self not used
    def verify_transaction_signature(sender_public_key, signature, transaction):
        public_key = RSA.importKey(binascii.unhexlify(sender_public_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(transaction).encode('utf8'))  # hash
        try:
            verifier.verify(h, binascii.unhexlify(signature))  # library does not explicitly return
            return True
        except ValueError:
            return False

    @staticmethod
    def valid_proof(transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(transactions) + str(last_hash) + str(nonce)).encode('utf8')
        h = hashlib.new('sha256')
        h.update(guess)
        guess_hash = h.hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty

    # TODO: Research if proof-of-work is necessary for DEEPFAKE
    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0
        while self.valid_proof(self.transactions, last_hash, nonce) is False:
            nonce += 1

        return nonce

    @staticmethod
    def hash(block):
        # Important to sort keys so that the dictionary retains its ordered format
        block_string = json.dumps(block, sort_keys=True).encode('utf8')
        h = hashlib.new('sha256')
        h.update(block_string)
        return h.hexdigest()

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)  # compare with length of other chains in network

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

    def valid_chain(self, chain):
        # Whether chain is valid or not. I.e. one chain with 5 blocks and another with 6..
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False

            transactions = block['transactions'][:-1]
            transaction_elements = ['sender_public_key', 'recipient_public_key', 'amount']
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements) for transaction in
                            transactions]
            if not self.valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    def submit_transaction(self, sender_public_key, recipient_public_key, signature, amount):
        # TODO: Reward the miner
        # TODO: Validate Signature !IMPORTANT!

        transaction = OrderedDict({
            'sender_public_key': sender_public_key,
            'recipient_public_key': recipient_public_key,
            'amount': amount
        })

        # TODO: Reward for uploading verified video
        # Reward for mining a block
        if sender_public_key == MINING_SENDER:
            self.transactions.append(transaction)  # append to node. adding each block
            return len(self.chain) + 1
        else:
            # Transaction from wallet to another wallet
            signature_verification = self.verify_transaction_signature(sender_public_key, signature, transaction)
            if signature_verification:
                self.transactions.append(transaction)  # append to node. adding each block
                return len(self.chain) + 1
            else:
                return False


# Instantiate the Blockchain
blockchain = Blockchain()

# Instantiate the Node using Flask for HTML Javascript communication
app = Flask(__name__)  # Minimal Flask installation for this simulation
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')  # render template looks at template folder by default. Flask module.


@app.route('/configure')
def configure():
    return render_template('configure.html')  # render template looks at template folder by default. Flask module.


@app.route('/transactions/get', methods=['GET'])
def get_transaction():
    transactions = blockchain.transactions
    response = {'transactions': transactions}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm
    nonce = blockchain.proof_of_work()

    blockchain.submit_transaction(sender_public_key=MINING_SENDER,
                                  recipient_public_key=blockchain.node_id,
                                  signature='',
                                  amount=MINING_REWARD)

    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)

    response = {
        'message': 'New block created',
        'block_number': block['block_number'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.form

    # TODO: check the required fields, four fields. Change this when changing to deepfake

    required = ['confirmation_sender_public_key', 'confirmation_recipient_public_key', 'transaction_signature',
                'confirmation_amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    transaction_result = blockchain.submit_transaction(values['confirmation_sender_public_key'],
                                                       values['confirmation_recipient_public_key'],
                                                       values['transaction_signature'],
                                                       values['confirmation_amount'])
    if transaction_result == False:
        response = {'message': 'Invalid Transaction/Signature'}
        return jsonify(response), 406
    else:
        response = {'message': 'Transaction Successful. Added to Block ' + str(transaction_result)}  # number of next
        # block that contains the transaction
        return jsonify(response), 201


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_node():
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


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()  # calls a function to parse arguments/parameters
    parser.add_argument('-p', '--port', default=5001, type=int, help="port to listen to")  # sets args by adding to
    # parse. this relates to port
    args = parser.parse_args()  # sets the values of the added parse to args
    port = args.port  # generates the port variable from args

    app.run(host='127.0.0.1', port=port, debug=True)  # runs flask code with these parameters set, debug is true so
    # server does not constantly restart

