# coding=utf-8
# 

import unittest2
from risk_report.utility import getCurrentDirectory
from risk_report.asset import getAssetType, getAverageRatingScore, isInvestmentGrade \
							, getIdnType
from risk_report.geneva import readGenevaInvestmentPositionFile
from risk_report.main import loadBlpDataFromFile, ratingsApplicable
from itertools import filterfalse
from functools import partial
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


		# The bond: POSABK V4.5 PERP, the special case, treated as equity in 19437
		isBondPosition2 = lambda x: x['InvestID'] == 'XS1684793018 Perfshs'
		self.assertEqual( ('Equity', 'Listed equities')
						, getAssetType(blpData, firstOf(isBondPosition2, positions)))


		# The callable bond: BCHINA V3.6 PERP
		isCallableBondPosition = lambda x: x['InvestID'] == 'XS2125922349'
		self.assertEqual( ('Fixed Income', 'Additional Tier 1, Contingent Convertibles')
						, getAssetType(blpData, firstOf(isCallableBondPosition, positions)))

		# The iShares A50 China ETF
		isA50Fund = lambda x: x['InvestID'] == '2823 HK'
		self.assertEqual( ('Fund', 'Exchange Traded Funds')
						, getAssetType(blpData, firstOf(isA50Fund, positions)))

		# The LINK REIT (823 HK is treated as special case)
		isREITFund = lambda x: x['InvestID'] == '823 HK'
		self.assertEqual( ('Equity', 'Listed equities')
						, getAssetType(blpData, firstOf(isREITFund, positions)))



	def testAverageRating(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'DIF_20200429_investment_position.xlsx')
		date, positions = compose(\
			lambda t: (t[0], list(t[1]))
		  , readGenevaInvestmentPositionFile
		)(inputFile)

		blpDataFile = join(getCurrentDirectory(), 'samples', 'DIF_20200429_BlpData.xlsx')
		blpData = loadBlpDataFromFile(blpDataFile)

		securitiesWithRatings = compose(
			list
		  , partial(map, lambda p: (getAverageRatingScore(blpData, p), p))
		  , partial(map, lambda t: t[1])
		  , partial(filter, lambda t: ratingsApplicable(t[0]))
		  , lambda blpData, positions: \
		  		map(lambda p: (getAssetType(blpData, p), p), positions)
		)(blpData, positions)

		# There are 154 bonds (155 bonds, but one with special case override)
		self.assertEqual(154, len(securitiesWithRatings))

		# Has 3 credit ratings
		self.assertEqual(11, firstOf( lambda t: t[1]['InvestID'] == 'XS2114413565'
									, securitiesWithRatings)[0])

		# Has 2 credit ratings
		self.assertEqual(11, firstOf( lambda t: t[1]['InvestID'] == 'USY70902AB04'
									, securitiesWithRatings)[0])

		# Has 1 credit ratings
		self.assertEqual(13, firstOf( lambda t: t[1]['InvestID'] == 'XS2127809528'
									, securitiesWithRatings)[0])

		# Has no credit ratings
		self.assertEqual(0, firstOf( lambda t: t[1]['InvestID'] == 'XS2021226985'
									, securitiesWithRatings)[0])
