from flask import Flask, render_template, jsonify, request, redirect
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii
from _collections import OrderedDict
from werkzeug.utils import secure_filename

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
        self.data_hash = imageHash

    def to_dict(self):
        return OrderedDict({
            'public_key': self.public_key,
            'private_key': self.private_key,
            'data_hash': self.data_hash
        })

    def sign_transaction(self):
        private_key = RSA.import_key(
            binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
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

dirname = os.path.dirname(__file__)


# Implementation of difference hashing
def image_dhash(image, hashSize=8):
    # resize the input image to satisfy a 8*8 dimensional
    # image
    resized = cv2.resize(image, (hashSize + 1, hashSize))

    diff = resized[:, 1:] > resized[:, :-1]

    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])


@app.route("/upload-data", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":

        if request.files:
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
            print("THE HASH IS ", imageHash)

            # remove local file and clean up
            os.remove(os.path.join(dirname, 'static/img/' + image.filename))

    # transaction = Transaction()

    return render_template('upload_data.html'), 200

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
