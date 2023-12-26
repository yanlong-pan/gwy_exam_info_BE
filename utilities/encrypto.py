import hashlib

def hash_gen(data):
    return hashlib.sha256(data.encode()).hexdigest()

def verify_hash(data, received_hash):
    return hash_gen(data) == received_hash
