# coding=utf-8
# 

import unittest2
from risk_report.asset import byCountryFilter
from risk_report.geneva import getGenevaMarketValue
from risk_report.main import getTotalMarketValueFromAssetType \
							, getTotalMarketValueFromCountrynAssetType
from risk_report.data import getPortfolioPositions, getBlpData, getFX
from risk_report.utility import getCurrentDirectory
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join



class TestGenevaAll(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaAll, self).__init__(*args, **kwargs)



	def testSum(self):
		FX = getFX('20200429', 'USD')['HKD']
		blpData = getBlpData('20200429', 'test')
		positions = list(getPortfolioPositions('19437', '20200429', 'test'))

		
		# Now we test by different country groups
		self.assertAlmostEqual( 394165723.69
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China - Mainland')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 46753980.08
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China - Hong Kong')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 10019205.48
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China - Macau')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 15742145.41
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Singapore')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 1419901.34
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'America - others (1)')
							  	)(positions)
							  , 2
							  )


		# Purposedly made wrong, since there are no "XXX" country.
		self.assertAlmostEqual( 0
							  , compose(
							  		lambda x: x / FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'XXX')
							  	)(positions)
							  , 2
							  )


		# Now test different asset types
		"""
		Note that "XS1684793018	POSABK V4.5 PERP" is treated as a special case 
		in 19437, as Equity

		823 HK is also a special case, treated as listed equities instead of
		REITs.
		"""
		# self.assertAlmostEqual( 32572726.51
		# 					  , compose(
		# 					  		lambda x: x / FX
		# 					  	  , sum
		# 					  	  , partial(map, getGenevaMarketValue)
		# 					  	  , byAssetTypeFilter(blpData, 'Equity')
		# 					  	)(positions)
		# 					  , 2
		# 					  )


		# # 2823 HK
		# self.assertAlmostEqual( 953070.18
		# 					  , compose(
		# 					  		lambda x: x / FX
		# 					  	  , sum
		# 					  	  , partial(map, getGenevaMarketValue)
		# 					  	  , byAssetTypeFilter(blpData, 'Fund')
		# 					  	)(positions)
		# 					  , 2
		# 					  )



	def testSum2(self):
		blpData = getBlpData('20200429', 'test')
		positions = list(getPortfolioPositions('19437', '20200429', 'test'))

		self.assertAlmostEqual( 12513933.62
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Mainland'
								  , 'Fixed Income'
								  , 'Additional Tier 1, Contingent Convertibles'
								)
							  , 2
							  )


		self.assertAlmostEqual( 17208645.91
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Hong Kong'
								  , 'Fixed Income'
								  , 'Corporate'
								  , 'Investment Grade'
								  , 'Financial Institution'
								)
							  , 2
							  )


		self.assertAlmostEqual( 5020919.30
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Macau'
								  , 'Fixed Income'
								  , 'Corporate'
								  , 'Non-Investment Grade'
								  , 'Non-Financial Institution'
								)
							  , 2
							  )


		self.assertAlmostEqual( 2029888.56
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Government / Municipal'
								)
							  , 2
							  )


		self.assertAlmostEqual( 26308960.40
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Corporate'
								)
							  , 2
							  )


		# Purposely made wrong, since there are no such thing as 
		# 'Fixed Income', 'Government', 'Financial'
		self.assertAlmostEqual( 0
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Government / Municipal'
								  , 'Financial'
								)
							  , 2
							  )