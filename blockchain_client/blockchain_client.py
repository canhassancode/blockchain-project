from flask import Flask, render_template, jsonify, request
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii
from _collections import OrderedDict


class Transaction:

    """
    User can Interface with this class
    """

    def __init__(self, sender_public_key, sender_private_key, recipient_public_key, amount):  # constructor
        self.sender_public_key = sender_public_key
        self.sender_private_key = sender_private_key
        self.recipient_public_key = recipient_public_key
        self.amount = amount

    def to_dict(self):
        return OrderedDict({
            'sender_public_key': self.sender_public_key,
            'recipient_public_key': self.recipient_public_key,
            'amount': self.amount
        })

    def sign_transaction(self):
        private_key = RSA.import_key(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        hash = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(hash)).decode('ascii')


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate/transaction', methods=['POST'])
def generate_transaction():
    sender_public_key = request.form['sender_public_key']
    sender_private_key = request.form['sender_private_key']
    recipient_public_key = request.form['recipient_public_key']
    amount = request.form['amount']

    transaction = Transaction(sender_public_key, sender_private_key, recipient_public_key, amount)

    response = {'transaction': transaction.to_dict(),
                'signature': transaction.sign_transaction()}

    return jsonify(response), 200


@app.route('/make/transaction')
def make_transaction():
    return render_template('make_transaction.html')


@app.route('/view/transactions')
def view_transaction():
    return render_template('view_transactions.html')


@app.route('/wallet/new')
def new_wallet():
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


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()  # calls a function to parse arguments/parameters
    parser.add_argument('-p', '--port', default=8081, type=int, help="port to listen to")  # sets args by adding to
    # parse. this relates to port
    args = parser.parse_args()  # sets the values of the added parse to args
    port = args.port  # generates the port variable from args

    app.run(host='127.0.0.1', port=port, debug=True)  # runs flask code with these parameters set, debug is true so
    # server does not constantly restart
