from datetime import datetime, timezone
import hashlib
import json
from secp256k1 import secp256k1
import secrets

class Block():

	def __init__(self, previoushash):
		self.__previoushash = previoushash
		self.__timestamp = str(int((datetime.now(timezone.utc) - datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc)).total_seconds() * 1000))
		self.__nonce = 0
		self.__merkleroot = ""
		self.__hash = self.calculateHash()
		self.__transactions = []

	def addTransaction(self, transaction, chain = None):
		if transaction is None:
			return False
		if not self.__previoushash == "0":
			if not transaction.processTransaction(chain):
				print("The Transaction Failed to Process and was Discarded.")
				return False
		self.__transactions.append(transaction)
		print("Transaction Successfully Added to the Block")
		return True

	def calculateHash(self):
		hash = Cryptography().applySha256(Cryptography().encodeUnicode(self.__previoushash + self.__timestamp + str(self.__nonce) + self.__merkleroot))
		return hash

	def getHash(self):
		return self.__hash

	def getPreviousHash(self):
		return self.__previoushash

	def mineBlock(self, difficulty):
		merkleroot = Cryptography().getPseudoMerkleRoot(self.__transactions)
		target = ""
		for i in range(0, difficulty):
			target += "0"
		while not self.__hash[0:difficulty] == target:
			self.__nonce += 1
			self.__hash = self.calculateHash()
		print("Block Mined! : " + str(self.__hash))

	def toJson(self):
		return json.dumps(self, indent = 4, default = lambda o: o.__dict__)

class Cryptography():
	
	def applySha256(self, string):
		return hashlib.sha256(string).hexdigest()

	def ECDSASign(self, key, data):
		nvalue = secp256k1().getCurve().field.n
		messagehash = self.applySha256(self.encodeUnicode(data))
		kvalue = secrets.randbelow(nvalue-1) + 1
		rvalue = (kvalue * secp256k1().getCurve().g).x
		kinverse = self.modularInverse(kvalue, nvalue)
		svalue = kinverse * (int(messagehash, 16) + rvalue * key) % nvalue
		return [rvalue, svalue]

	def ECDSAVerify(self, key, data, signature):
		nvalue = secp256k1().getCurve().field.n
		messagehash = self.applySha256(self.encodeUnicode(data))
		svalue = self.modularInverse(signature[1], nvalue)
		r1 = (int(messagehash, 16) * svalue % nvalue) * secp256k1().getCurve().g
		r2 = (signature[0] * svalue % nvalue) * key
		rvalue = (r1 + r2).x % nvalue
		if rvalue == signature[0]:
			return True
		else:
			return False

	def decodeUnicode(self, string):
		return string.decode('utf-8')

	def encodePublicKey(self, key):
		return '0' + str(2 + key.y % 2) + str(hex(key.x)[2:])		

	def encodeUnicode(self, string):
		return string.encode('utf-8')
	
	def getPseudoMerkleRoot(self, transactions):
		count = len(transactions)
		previoustreelayer = []
		treelayer = []
		for i in transactions:
			previoustreelayer.append(i.getHash())
		while count > 1:
			for i in range(1,len(previoustreelayer)):
				treelayer.append(self.applySha256(previousTreeLayer[i-1] + previousTreeLayer[i]))
			count = len(treelayer)
			previoustreelayer = [i for i in treelayer]
		if len(treelayer) == 1:
			merkleroot = treelayer[0]
		else:
			merkleroot = ""
		return merkleroot

	def modularInverse(self, base, modulo):
		if base < 0 or modulo <= base:
			base = base % modulo
		currentbase = base
		currentmodulo = modulo
		baseconstantu, baseconstantv, moduloconstantu, moduloconstantv = 1, 0, 0, 1
		while currentbase != 0:
			quotient, currentbase, currentmodulo = divmod(currentmodulo, currentbase) + (currentbase,)
			baseconstantu, baseconstantv, moduloconstantu, moduloconstantv = moduloconstantu - quotient*baseconstantu, moduloconstantv - quotient*baseconstantv, baseconstantu, baseconstantv
		if not currentmodulo == 1:
			return None
		if moduloconstantu > 0:
			return moduloconstantu
		else:
			return moduloconstantu + modulo

class RainChain():

	def __init__(self, genesisblock, initialutxo):
		self.__difficulty = 5
		self.__firstblock = genesisblock
		self.__blockchain = [self.__firstblock]
		print("Trying to mine first block:")
		self.__firstblock.mineBlock(self.__difficulty)
		self.__length = 1
		self.__UTXOs = {initialutxo.getId(): initialutxo}

	def addUTXO(self, id, output):
		self.__UTXOs[id] = output

	def getAllUTXOs(self):
		return self.__UTXOs

	def getBlock(self, index):
		try:
			return self.__blockchain[index-1]
		except IndexOutOfBounds:
			print("Index out of bounds")

	def getMinimumTransaction(self):
		return 1

	def getUTXO(self, id):
		return self.__UTXOs[id]

	def insertBlock(self, block):
		print("Trying to mine block " + str(self.__length) + ":")
		block.mineBlock(self.__difficulty)
		self.__blockchain.append(block)
		self.__length += 1

	def isChainValid(self):
		minetarget = ""
		for i in range(0, self.__difficulty):
			minetarget += "0"
		if not self.__blockchain[0].getHash()[0:self.__difficulty] == minetarget:
			return False
		for i in range(1, self.__length):
			currentBlock = self.__blockchain[i]
			previousBlock = self.__blockchain[i-1]
			if not currentBlock.getHash() == currentBlock.calculateHash():
				print("Current hashes not equal")
				return False
			if not previousBlock.getHash() == currentBlock.getPreviousHash():
				print("Previous hashes not equal")
				return False
			if not currentBlock.getHash()[0:self.__difficulty] == minetarget:
				print("Block not mined")
				return False
		return True

	def removeUTXO(self, id):
		del self.__UTXOs[id]

	def __str__(self):
		blockchainjson = "{\n"
		for i in self.__blockchain:
			blockchainjson += i.toJson() + ",\n"
		blockchainjson += "}"
		return blockchainjson
		

if (__name__ == "__main__"):
	testchain = RainChain("Hi I'm the first block")
	testchain.insertBlock("Yo I'm the second block")
	testchain.insertBlock("Whaddup I'm the third block")
	print("The chain is valid: " + str(testchain.isChainValid()))
	print(testchain)
