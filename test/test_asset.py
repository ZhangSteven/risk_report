# coding=utf-8
# 

import unittest2
from risk_report.utility import getCurrentDirectory
from risk_report.asset import getAssetType
from risk_report.geneva import readGenevaInvestmentPositionFile
from risk_report.main import loadBlpDataFromFile
from utils.iter import firstOf
from toolz.functoolz import compose
from os.path import join



class TestAsset(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestAsset, self).__init__(*args, **kwargs)


	def testDIFAssetType(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'DIF_20200429_investment_position.xlsx')
		date, positions = compose(\
			lambda t: (t[0], list(t[1]))
		  , readGenevaInvestmentPositionFile
		)(inputFile)

		blpDataFile = join(getCurrentDirectory(), 'samples', 'DIF_20200429_BlpData.xlsx')
		blpData = loadBlpDataFromFile(blpDataFile)

		# USD cash on hand position
		isUSDCash = lambda x: \
			x['InvestID'] == 'USD' and int(x['Quantity']) == 8183675
		self.assertEqual( ('Cash', )
						, getAssetType(blpData, firstOf(isUSDCash, positions)))

		# Cash payable position
		isHKDCashPayable = lambda x: \
			x['InvestID'] == 'HKD' and int(x['Quantity']) == -1804761
		self.assertEqual( ('Cash', )
						, getAssetType(blpData, firstOf(isHKDCashPayable, positions)))

		# Equity position
		isEquityPosition = lambda x: x['InvestID'] == '1299 HK'
		self.assertEqual( ('Equity', 'Listed Equities')
						, getAssetType(blpData, firstOf(isEquityPosition, positions)))

		# The bond: T V2.875 PERP B
		isBondPosition = lambda x: x['InvestID'] == 'XS2114413565'
		self.assertEqual( ('Fixed Income', 'Corporate')
						, getAssetType(blpData, firstOf(isBondPosition, positions)))

		# The callable bond: BCHINA V3.6 PERP
		isCallableBondPosition = lambda x: x['InvestID'] == 'XS2125922349'
		self.assertEqual( ('Fixed Income', 'Additional Tier 1, Contingent Convertibles')
						, getAssetType(blpData, firstOf(isCallableBondPosition, positions)))

		# The iShares A50 China ETF
		isA50Fund = lambda x: x['InvestID'] == '2823 HK'
		self.assertEqual( ('Fund', 'Exchange Traded Funds')
						, getAssetType(blpData, firstOf(isA50Fund, positions)))

		# The LINK REIT
		isREITFund = lambda x: x['InvestID'] == '823 HK'
		self.assertEqual( ('Fund', 'Real Estate Investment Trusts')
						, getAssetType(blpData, firstOf(isREITFund, positions)))
