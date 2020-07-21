from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import base64
import dbus
import hashlib
import os
import sys

if len(sys.argv) != 4:
    raise Exception(
        "Usage: %s <secret-type> <secret-group> <secret-name>" % sys.argv[0])
secret_type, secret_group, secret_name = sys.argv[1:4]
secret = sys.stdin.buffer.read()[:-1]

print("Setting secret %s-%s-%s to %s" %
      (secret_type, secret_group, secret_name, secret))

bus = dbus.SystemBus()
ctrl_proxy = bus.get_object(
    "com.github.puiterwijk.dbus_parsec",
    "/com/github/puiterwijk/DBusPARSEC/Control")
ctrl = dbus.Interface(
    ctrl_proxy, "com.github.puiterwijk.DBusPARSEC.Control")

wrapkey = AESGCM.generate_key(256)
print("Wrapper key sha256: %s" % hashlib.sha256(wrapkey).hexdigest())
encryptor = AESGCM(wrapkey)
nonce = os.urandom(12)
aad = '%s;%s;%s' % (secret_type, secret_group, secret_name)
ct = encryptor.encrypt(nonce, secret, aad.encode("utf-8"))

pubkey = ctrl.GetPublicKey(secret_type, secret_group, byte_arrays=True)
print("Public key sha256: %s" % hashlib.sha256(pubkey).hexdigest())
pubkey = load_der_public_key(pubkey, default_backend())

wrapped = pubkey.encrypt(
    nonce + wrapkey, OAEP(mgf=MGF1(SHA256()), algorithm=SHA256(), label=None))

ctrl.StoreSecret(secret_type, secret_group, secret_name, wrapped, ct)

print("Secret stored")
