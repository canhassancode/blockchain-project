from flask import Flask, render_template, jsonify, request
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii
from _collections import OrderedDict
from werkzeug.utils import secure_filename

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

@app.route('/view/data')
def view_data():
    return render_template('view_data.html')


#############################################
# User Account/Wallet and generate data 
# transaction to blockchain
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
