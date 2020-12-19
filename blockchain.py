import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Genesis Block - Creation
        self.new_block(previous_hash=1, proof=100)


    def new_block(self, proof, previous_hash=None):
        '''
        Creates a new Block and adds it to the chain
        :param proof: <int> Proof from Proof of work Algorithm
        :param previous_hash: (optional) <str> Hash of previous block
        :return: <dict> New block
        '''
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []
        
        # Adding the block to the chain
        self.chain.append(block)
        return block


    def new_transactions(self, sender, recipient, amount):
        '''
        Creates a new transaction to go into the next mined block
        :param sender: <str> Address of the sender
        :param recipient: <str> Address of rhe recipient 
        :param amount: <int> Amount of transaction
        :return: <int> Index of the block that will keep this transaction
        '''
        self.current_transactions.append({
            'sender':   sender,
            'recipient':    recipient,
            'amount':   amount,
        })

        return self.last_block['index'] + 1
    

    def proof_of_work(self, last_proof):
        '''
        Algo : Finding a number p' such that hash(pp') contains 4 leading zeroes (can be adjusted with time)
        p : is previous proof
        p': new proof
        :param last_proof: <int>
        :return: <int> 
        '''

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof+=1
        return proof
     

    @staticmethod
    def valid_proof(last_proof, proof):
        # Validates the proof for 4 leading zeores
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    @staticmethod
    def hash(block):
        '''
        Hashes a block, using SHA-256 (hash of the block)
        :param block: <dict> Block
        :return: <str>
        '''
        # Make sure not to have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    
    @property
    def last_block(self):
        # Return last block in the chain
        return self.chain[-1]

# Class Blockchain is complete , Now working on API for the Blockchain to create endpoints using flask

# Instantiate the app
app = Flask(__name__)

# Generating Global unique address for this node
node_identifier = str(uuid4()).replace('-','')

# Instantitate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    #Running the POW algorithm to get next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #Granting reward for finding the proof
    blockchain.new_transactions(
        sender = "0", # To signify that this node has mined new coin
        recipient = node_identifier,
        amount = 1,
    )

    #Forging the block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200
    #return "Mining a new block"
    

@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json(force=True)
    #Checking the required field
    required =  ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    #Create the new transaction once verified
    index = blockchain.new_transactions(values['sender'], values['recipient'], values['amount'])

    response = {'message':f'Transaction will be added to Block {index}'}
    return jsonify(response), 201
    #return "Adding a new Transaction"


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)

