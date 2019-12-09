# coding=utf-8
# 

import unittest2
from os.path import join



class TestALL(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestALL, self).__init__(*args, **kwargs)



	def test1(self):
		self.assertEqual(1, 1)