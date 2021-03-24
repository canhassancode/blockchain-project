from flask import Flask, render_template, jsonify, request, redirect
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii
from _collections import OrderedDict
from werkzeug.utils import secure_filename
import requests

import time
import cv2
import os


#############################################
# Constructor. User interface with this
# class.
#############################################

class Data:

    def __init__(self, public_key, private_key, data_hash):
        self.public_key = public_key
        self.private_key = private_key
        self.data_hash = data_hash

    def to_dict(self):
        return OrderedDict({
            'public_key': self.public_key,
            'private_key': self.private_key,
            'data_hash': self.data_hash
        })

    def sign_transaction(self):
        new_private_key = RSA.import_key(
            binascii.unhexlify(self.private_key))
        signer = PKCS1_v1_5.new(new_private_key)
        hash = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(hash)).decode('ascii')


#############################################
# Index, Upload Data and View Data pages with
# flask initialisaiton
#############################################

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload/data')
def upload_data():
    return render_template('upload_data.html')


@app.route('/authenticate/data')
def authenticate_data():
    return render_template('authenticate_data.html')


@app.route('/view/data')
def view_data():
    return render_template('view_data.html')


#############################################
# User Account/Wallet Creation.
# Public/Private key pair
#############################################


@app.route('/new/account')
def new_account():
    # this exists through ajax function for generate wallet. Returns this function
    random_gen = Crypto.Random.new().read  # generate random number for RSA
    # RSA of 1024 bits
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.public_key()

    """
    response is a dictionary as it is a json
    format is DER as that is format of the key to decode to ascii
    ascii then passed through json to response with code 200 to confirm it works
    """

    response = {
        'private_key': binascii.hexlify(private_key.export_key(format('DER'))).decode('ascii'),
        'public_key': binascii.hexlify(public_key.export_key(format('DER'))).decode('ascii')
    }
    return jsonify(response), 200


#############################################
# Uploading data, Hashing image uploads and
# parsing data
#############################################

# Machine Learning Deepfake detection
def deeepfake_detection():
    return ''


dirname = os.path.dirname(__file__)


# Implementation of difference hashing
def image_dhash(image, hashSize=8):
    # resize the input image to satisfy a 8*8 dimensional
    # image
    resized = cv2.resize(image, (hashSize + 1, hashSize))

    diff = resized[:, 1:] > resized[:, :-1]

    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
    # code referenced in README

@app.route("/upload/new", methods=["GET"])
def test_function():
    test_string = "IT WORKS"
    response = {"hello": "key 1",
    "bye bye": "key 2"}
    return jsonify(response), 200

@app.route("/upload-data", methods=["POST"])
def upload_files():
    # recieve uploaded image and
    # save locally
    image = request.files["image"]
    filename = secure_filename(image.filename)
    image.save(os.path.join(dirname, 'static/img/' + filename))

    # opencv to read image and convert
    # to grayscale
    recieved_image = cv2.imread(os.path.join(
        dirname, 'static/img/' + image.filename))
    recieved_image = cv2.cvtColor(recieved_image, cv2.COLOR_BGR2GRAY)
    imageHash = image_dhash(recieved_image)
    print("THE HASH IS", imageHash)

    # CHECK HASH AGAIST BLOCKCHAIN 
    blockchain_hashes = requests.get('http://127.0.0.1:5001/verify-hash')
    blockchain_hash_list = blockchain_hashes.json()
    blockchain_hash_check = []
    
    # Blockchain verified hashes
    for i in range(len(blockchain_hash_list['chain']) + 1):
        try:
            for j in range(len(blockchain_hash_list['chain'][i]['data'])):
                if blockchain_hash_list['chain'][i]['data'][j]['data_hash'][j] != '':
                    blockchain_hash_check.append(blockchain_hash_list['chain'][i]['data'][j]['data_hash'])
        except Exception:
            pass
    
    # Hashes on block before being hashed
    for i in range(len(blockchain_hash_list['chain_data'])):
        try: 
            if blockchain_hash_list['chain_data'][i]['data_hash'] != '':
                blockchain_hash_check.append(blockchain_hash_list['chain_data'][i]['data_hash'])
        except Exception:
            pass
    
    # Check if Hash exists
    for i in blockchain_hash_check:
        if str(i) == str(imageHash):
            os.remove(os.path.join(dirname, 'static/img/' + image.filename))
            return "file exists on blockchain", 422

    # remove local file and clean up
    os.remove(os.path.join(dirname, 'static/img/' + image.filename))

    public_key = request.form['sender_public_key']
    private_key = request.form['sender_private_key']

    data = Data(public_key, private_key, str(imageHash))

    response = {'data': data.to_dict(),
                'signature': data.sign_transaction()}

    return jsonify(response), 200

#############################################
# Localhost for Blockchain
#############################################


# This section hosts the flask html site
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()  # calls a function to parse arguments/parameters
    parser.add_argument('-p', '--port', default=8081, type=int,
                        help="port to listen to")  # sets args by adding to
    # parse. this relates to port
    args = parser.parse_args()  # sets the values of the added parse to args
    port = args.port  # generates the port variable from args

    # runs flask code with these parameters set, debug is true so
    app.run(host='127.0.0.1', port=port, debug=True)
    # server does not constantly restart
