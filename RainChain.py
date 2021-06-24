from datetime import datetime
from datetime import timezone
import hashlib
import json

class Block():

	def __init__(self, data, previoushash):
		self.__previoushash = previoushash
		self.__data = data
		self.__timestamp = str(int((datetime.now(timezone.utc) - datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc)).total_seconds() * 1000))
		self.__nonce = 0
		self.__hash = self.calculateHash()

	def calculateHash(self):
		hash = Cryptography().applySha256(Cryptography().encodeUnicode(self.__previoushash + self.__timestamp + str(self.__nonce) + self.__data))
		return hash

	def getHash(self):
		return self.__hash

	def getPreviousHash(self):
		return self.__previoushash

	def mineBlock(self, difficulty):
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

	def encodeUnicode(self, string):
		return string.encode('utf-8')
	
	def decodeUnicode(self, string):
		return string.decode('utf-8')

class RainChain():

	def __init__(self, initialData):
		self.__difficulty = 5
		self.__firstblock = Block(initialData, "0")
		self.__blockchain = [self.__firstblock]
		print("Trying to mine first block:")
		self.__firstblock.mineBlock(self.__difficulty)
		self.__length = 1

	def getBlock(self, index):
		try:
			return self.__blockchain[index-1]
		except IndexOutOfBounds:
			print("Index out of bounds")

	def insertBlock(self, data):
		newblock = Block(data, self.__blockchain[self.__length - 1].getHash())
		self.__blockchain.append(newblock)
		self.__length += 1
		print("Trying to mine block " + str(self.__length) + ":")
		newblock.mineBlock(self.__difficulty)

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