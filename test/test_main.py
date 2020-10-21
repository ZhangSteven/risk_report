# coding=utf-8
# 
# Production data test comes here

import unittest2
from risk_report.main import marketValueWithFX, getLiquidityCategory \
							, getTotalMarketValueFromCountrynAssetType
from risk_report.data import getFX, getPortfolioPositions, getBlpData, getLqaData
from toolz.functoolz import compose
from functools import partial
from os.path import join



getLiquidityData = lambda portfolio, date, mode: \
compose(
	list
  , partial( map
  		   , lambda p: ( getLiquidityCategory( date
  		   			   						 , mode
  		   			   						 , getBlpData(date, mode)
  		   			   						 , getLqaData(date, mode)
  		   			   						 , p)
  		   			   , marketValueWithFX(getFX(date, 'USD'), p)
  		   			   ))
  , getPortfolioPositions
)(portfolio, date, mode)



getMarketValueWithLiquidity = lambda liquidityTag, positions: \
compose(
	sum
  , partial(map, lambda t: t[1])
  , partial(filter, lambda t: t[0] == liquidityTag)
)(positions)




class TestMain(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestMain, self).__init__(*args, **kwargs)



	def testDIF20200630Liquidity(self):
		"""
		on 2020-06-30, DIF liquidity involves:

		1. special case
		2. liqudity override
		"""
		liquidityData = getLiquidityData('19437', '20200630', 'production')

		self.assertAlmostEqual( 512967110.78
							  , getMarketValueWithLiquidity('L0', liquidityData)
							  , 2)
		self.assertAlmostEqual( 72815789.05
							  , getMarketValueWithLiquidity('L1', liquidityData)
							  , 2)
		self.assertAlmostEqual( 29030087.72 
							  , getMarketValueWithLiquidity('L2', liquidityData)
							  , 2)
		self.assertAlmostEqual( 967654.17
							  , getMarketValueWithLiquidity('L3', liquidityData)
							  , 2)



	def testDIF20200930Liquidity(self):
		"""
		on 2020-09-30, DIF liquidity involves no special case and no override.
		"""
		liquidityData = getLiquidityData('19437', '20200930', 'production')

		self.assertAlmostEqual( 524102815.92
							  , getMarketValueWithLiquidity('L0', liquidityData)
							  , 2)
		self.assertAlmostEqual( 77442485.31
							  , getMarketValueWithLiquidity('L1', liquidityData)
							  , 2)
		self.assertAlmostEqual( 14232749.36
							  , getMarketValueWithLiquidity('L2', liquidityData)
							  , 2)
		self.assertAlmostEqual( 10084539.17
							  , getMarketValueWithLiquidity('L3', liquidityData)
							  , 2)



	def testDIF20200630AssetAllocation(self):
		"""
		on 2020-06-30, we have manual overrides for:

		XS1684793018 (POSABK V4.5 PERP) is treated as China listed equity for DIF

		XS2166383799 (APICORP) has a country SNAT (supernational), but treated
		as SA (Saudi Arabia)
		"""
		date = '20200630'
		mode = 'production'
		currency = 'USD'
		positions = list(getPortfolioPositions('19437', date, mode))
		blpData = getBlpData(date, mode)
		marketValueInCountryAsset = partial( getTotalMarketValueFromCountrynAssetType
										   , date, positions, blpData, currency)

		# XS1684793018 (POSABK V4.5 PERP) override
		self.assertAlmostEqual( 5567210.01
							  , marketValueInCountryAsset(
							  		'China - Mainland'
							  	  , 'Equity'
							  	  , 'Listed equities'
							  	  , 'Financial Institution'
							  	)
							  , 2)

		# 2823 HK Equity
		self.assertAlmostEqual( 1002490.16
							  , marketValueInCountryAsset(
							  		'China - Hong Kong'
							  	  , 'Fund'
							  	  , 'Exchange Traded Funds'
							  	  , 'SFC authorized'
							  	)
							  , 2)

		self.assertAlmostEqual( 15853886.87
							  , marketValueInCountryAsset(
							  		'China - Hong Kong'
							  	  , 'Fixed Income'
							  	  , 'Corporate'
							  	  , 'Investment Grade'
							  	  , 'Financial Institution'
							  	)
							  , 2)

		# XS2166383799 (APICORP) override
		self.assertAlmostEqual( 1999501.11
							  , marketValueInCountryAsset(
							  		'Saudi Arabia'
							  	  , 'Fixed Income'
							  	  , 'Government / Municipal'
							  	  , 'Investment Grade'
							  	)
							  , 2)



	def testDIF20200930AssetAllocation(self):
		"""
		on 2020-09-30, we test again.
		"""
		date = '20200930'
		mode = 'production'
		currency = 'USD'
		positions = list(getPortfolioPositions('19437', date, mode))
		blpData = getBlpData(date, mode)
		marketValueInCountryAsset = partial( getTotalMarketValueFromCountrynAssetType
										   , date, positions, blpData, currency)

		self.assertAlmostEqual( 1348591.11
							  , marketValueInCountryAsset(
							  		'Asia - others (1)'
							  	  , 'Fixed Income'
							  	  , 'Corporate'
							  	  , 'Investment Grade'
							  	  , 'Financial Institution'
							  	)
							  , 2)

		self.assertAlmostEqual( 1258.33
							  , marketValueInCountryAsset(
							  		'Asia - others (3)'
							  	  , 'Fixed Income'
							  	  , 'Government / Municipal'
							  	  , 'Non-Investment Grade'
							  	)
							  , 2)

		self.assertAlmostEqual( 54566752
							  , marketValueInCountryAsset('China - Hong Kong')
							  , 0)

		self.assertAlmostEqual( 375352414
							  , marketValueInCountryAsset('China - Mainland')
							  , 0)