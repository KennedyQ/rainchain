from RainChain import RainChain, Cryptography, Block
from secp256k1 import secp256k1
import secrets

class Transaction():

	def __init__(self, sender, reciever, value, inputs, number):
		self.__from = sender
		self.__fromencoded = Cryptography().encodePublicKey(self.__from)
		self.__to = reciever
		self.__toencoded = Cryptography().encodePublicKey(self.__to)
		self.__value = value
		self.__inputs = inputs
		self.__outputs = []
		self.__UTXOs = []
		self.__number = number
		self.__calculateHash()

	def __calculateHash(self):
		self.__hash = Cryptography().applySha256(Cryptography().encodeUnicode(self.__fromencoded + self.__toencoded + str(self.__value) + str(self.__number)))

	def generateSignature(self, key):
		data = self.__fromencoded + self.__toencoded
		self.__signature = Cryptography().ECDSASign(key, data)

	def genesisTransaction(self):
		self.__hash = "0"
		self.__outputs.append(TransactionOutput(self.__to, self.__value, self.__hash))
		return self.__outputs[0]

	def getHash(self):
		return self.__hash

	def getInputsValue(self):
		total = 0
		for i in self.__UTXOs:
			if i == None:
				continue
			total += i.getValue()
		return total

	def getOutputsValue(self):
		total = 0
		for i in self.__outputs:
			total += i.getValue()
		return total

	def processTransaction(self, chain):
		if not self.verifySignature():
			print("Transaction Signature Failed to Verify")
			return false
		for i in self.__inputs:
			self.__UTXOs.append(chain.getUTXO(i.getId()))
		if self.getInputsValue() < chain.getMinimumTransaction():
			print("Transaction Inputs too Small: " + str(self.getInputsValue()))
			return false
		leftover = self.getInputsValue() - self.__value
		self.__outputs = [TransactionOutput(self.__to, self.__value, self.__hash), \
			TransactionOutput(self.__from, leftover, self.__hash)]
		for i in self.__outputs:
			chain.addUTXO(i.getId(), i)
		for i in self.__UTXOs:
			if i == None:
				continue
			chain.removeUTXO(i.getId())
		return True

	def verifySignature(self):
		data = self.__fromencoded + self.__toencoded
		return Cryptography().ECDSAVerify(self.__from, data, self.__signature)

class TransactionInput():
	
	def __init__(self, id):
		self.__id = id

	def getId(self):
		return self.__id

class TransactionOutput():

	def __init__(self, recipient, value, parent):
		self.__recipient = recipient
		self.__value = value
		self.__parent = parent
		self.__id = Cryptography().applySha256(Cryptography().encodeUnicode(Cryptography().encodePublicKey(recipient) + str(value) + parent))
	
	def getId(self):
		return self.__id

	def getValue(self):
		return self.__value

	def hasOwnership(self, key):
		return self.__recipient == key

class TransactionManager():

	def __init__(self):
		self.__count = 0

	def createTransaction(self, sender, reciever, value, inputs):
		newtransaction = Transaction(sender, reciever, value, inputs, self.__count)
		self.__count += 1
		return newtransaction

class Wallet():

	def __init__(self):
		self.__generateKeyPair()
		self.__UTXOs = {}

	def __generateKeyPair(self):
		curve = secp256k1().getCurve()
		self.__privatekey = secrets.randbelow(curve.field.n)
		self.__publickey = curve.g * self.__privatekey
		self.__compressedpublickey = '0' + str(2 + self.__publickey.y % 2) + str(hex(self.__publickey.x)[2:])

	def getBalance(self, chain):
		total = 0
		UTXOs = chain.getAllUTXOs()
		for i in UTXOs.keys():
			currentOutput = UTXOs[i]
			if currentOutput.hasOwnership(self.__publickey):
				self.__UTXOs[i] = UTXOs[i]
				total += currentOutput.getValue()
		return total
			

	def getPublicKey(self):
		return self.__publickey

	def getPrivateKey(self):
		return self.__privatekey

	def sendFunds(self, recipient, value, chain, manager):
		if self.getBalance(chain) < value:
			print("Not enough funds to send transaction. Transaction cancelled.")
			return None
		inputs = []
		total = 0
		for i in self.__UTXOs.keys():
			currentOutput = self.__UTXOs[i]
			total += currentOutput.getValue()
			inputs.append(currentOutput)
			if total > value:
				break
		newtransaction = manager.createTransaction(self.__publickey, recipient, value, inputs)
		newtransaction.generateSignature(self.__privatekey)
		for i in inputs:
			del self.__UTXOs[i.getId()]
		return newtransaction

if (__name__ == "__main__"):
	testWallet1 = Wallet()
	testWallet2 = Wallet()
	coinbase = Wallet()
	transactionmanager = TransactionManager()	

	genesis = transactionmanager.createTransaction(coinbase.getPublicKey(), testWallet1.getPublicKey(), 100, None)
	genesis.generateSignature(coinbase.getPrivateKey())
	output = genesis.genesisTransaction()

	print("Creating and Mining Genesis Block")
	genesisblock = Block("0")
	genesisblock.addTransaction(genesis)
	testchain = RainChain(genesisblock, output)

	testBlock1 = Block(genesisblock.getHash())
	print("Wallet 1's Balance is: " + str(testWallet1.getBalance(testchain)))
	print("Wallet 1 is Attempting to Send Funds (40) to Wallet 2")
	testBlock1.addTransaction(testWallet1.sendFunds(testWallet2.getPublicKey(), 40, testchain, transactionmanager), testchain)
	testchain.insertBlock(testBlock1)
	print("Wallet 1's Balance is: " + str(testWallet1.getBalance(testchain)))
	print("Wallet 2's Balance is: " + str(testWallet2.getBalance(testchain)))

	testBlock2 = Block(testBlock1.getHash())
	print("Wallet 1 is Attempting to Send More Funds (1000) than it has")
	testBlock2.addTransaction(testWallet1.sendFunds(testWallet2.getPublicKey(), 1000, testchain, transactionmanager), testchain)
	testchain.insertBlock(testBlock2)
	print("Wallet 1's Balance is: " + str(testWallet1.getBalance(testchain)))
	print("Wallet 2's Balance is: " + str(testWallet2.getBalance(testchain)))

	testBlock3 = Block(testBlock2.getHash())
	print("Wallet 2 is Attempting to Send Funds (20) to Wallet 1")
	testBlock3.addTransaction(testWallet2.sendFunds(testWallet1.getPublicKey(), 20, testchain, transactionmanager), testchain)
	testchain.insertBlock(testBlock3)
	print("Wallet 1's Balance is: " + str(testWallet1.getBalance(testchain)))
	print("Wallet 2's Balance is: " + str(testWallet2.getBalance(testchain)))

	testchain.isChainValid()