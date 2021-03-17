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
MINING_REWARD = +1                  # Adds 1 to the reputation of the individual
MINING_DIFFICULTY = 2               # Difficulty for the miner in relation to the nonce

class Blockchain:

    def __init__(self):
        self.chain_data = []  # empty list to populate the data uploaded to blockchain TODO
        self.chain      = []  # containing the list of blocks on the blockchain TODO
        self.nodes      = set()  # Add a list of nodes to each node TODO
        self.node_id    = str(uuid4()).replace('-', '')  # id of node. replaces the - with empty TODO
        # Creating Genesis Block
        self.create_block(0, '00')  # nonce and previous hash

    def create_block(self, nonce, previous_hash):
        # Adds a block of data to the blockchain

        block = {
            'block_number': len(self.chain) + 1,  # with each block, add 1 to length of blockchain
            'timestamp' : time(),
            'data': self.chain_data,
            'nonce': nonce,
            'previous_hash': previous_hash
        }

        # reset current data once the block has been added to the chain
        self.chain_data = []
        # self.chain.appened(block)
        return block

    def register_node(self, node_url):
        parsed_url = urlparse(node_url)  # breaks down the parsed url to paramaters used(netloc and path)
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
            verifier.verify(h, binascii.unhexlify(signature))  # library does not explicitly return
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
            block = chain[current_index]  # passed in variable of block with 'previous_hash' 
            if block['previous_hash'] != self.hash(last_block):
                return False

            chain_data      = block['data'][:-1]
            data_elements   = ['public_key', 'data_hash']  # TODO: Add more here when looking into 
            chain_data      = [OrderedDict((x, data[x]) for x in data_elements) for information in chain_data]

            if not self.valid_proof(chain_data, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    # resolve conflicts for length of chain, if length is greater than overwrite dependent 
    # on verfified data transactions
    def resolve_conflicts(self):
        neighbours  = self.nodes 
        new_chain   = None
        max_length  = len(self.chain)  # compare with length of other chains in network

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
    def submit_data(self, public_key, signature, data_hash):
        # Validate the Signature
        # Reward the Verfier for proving authenticity
        
        data = OrderedDict({
            'public_key': public_key,
            'data_hash': data_hash
        })

        # Rewarding the Verifier from the Blockchain itself " THE OVERSEER"
        if public_key == MINING_SENDER:
            self.chain_data.append(data)
            return len(self.chain) + 1
        else:
            # data uploaded to block verification
            signature_verification = self.verify_transaction_signature(public_key, signature, data)
            if signature_verification:
                self.chain_data.append(data)  # append to node. adding each block
                return len(self.chain) + 1
            else:
                return False
          

#############################################
# Instantiate the Blockchain, flask and 
# CORS
#############################################

blockchain = Blockchain()
app = Flask(__name__)
CORS(app)

