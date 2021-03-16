from flask import Flask, render_template, jsonify, request
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii
from _collections import OrderedDict
from werkzeug.utils import secure_filename

