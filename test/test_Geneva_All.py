# coding=utf-8
# 

import unittest2
from risk_report.asset import byCountryGroup, getAssetType
from risk_report.geneva import readGenevaInvestmentPositionFile
from risk_report.main import loadBlpDataFromFile, byCountryFilter
from risk_report.utility import getCurrentDirectory
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join





class TestGenevaAll(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaAll, self).__init__(*args, **kwargs)



	def testSum(self):
		inputFile = join( getCurrentDirectory()
						, 'samples'
						, 'DIF_20200429_investment_position.xlsx'
						)

		blpDataFile = join( getCurrentDirectory()
						  , 'samples'
						  , 'DIF_20200429_BlpData.xlsx'
						  )
		
		FX = 1/7.7520	# USD FX as of 2020-04-30
		blpData = loadBlpDataFromFile(blpDataFile)
		positions = compose(
			lambda t: list(t[1])
		  , readGenevaInvestmentPositionFile
		)(inputFile)


		getGenevaMarketValue = lambda position: \
			position['AccruedInterest'] + position['MarketValueBook']


		# Now we test by different country groups
		self.assertAlmostEqual( 394165723.69
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 46753980.08
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Hong Kong')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 10019205.48
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Macau')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 15742145.41
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Singapore')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 1419901.34
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'America - others (1)')
							  	)(positions)
							  , 2
							  )