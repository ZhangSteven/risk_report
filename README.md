# risk_report
The purpose of this package to convert Daphne Keung's Excel application into a Python application.

Purpose of this application:

1. Generate SFC report for DIF.

2. Generate liquidity report for all other portfolios in the company.



## To Do

1. What is the country code if a security's geographical region is global, e.g., ICSUSPI ID Equity and JPMULCD LX Equity?

2. What asset type should we put REPO into?

3. What country code should we assign to REPO positions?

4. What's the credit rating for the below:
	1. Fitch, F1+
	2. Moody's NR, 
	3. Fitch A+ \*-
	4. Fitch A \*-
	5. Fitch A- \*-
	6. Fitch A+u
	7. Moody's A3 \*+
	8. S&P AA- \*-
	9. Moody's A1 \*-
	10. Fitch BBB-u

5. What market value should we use for a derivative position, like REPO or FX Forward, should we use net mv or gross mv?

6. Now ABS is treated using special case handling, is there a way to tell whether it's cash or synthetic?

7. Consider refactor code to improve efficiency, tag each position with country and asset type first, then filter them.

8. Consider using Geneva as the asset type provider?




## Note

1. Bloomberg has no concept of HTM bonds, all using market price. Therefore Bloomberg NAV and Geneva NAV will be different if HTM bonds are involved.

2. Bloomberg "Market Value" field (Net MV) for a bond consists of both the pricing and accured interest. However, there is always a small difference from a Geneva valuation. For example, 20051, MSINS 4.95 PERP REGS (USJ4517MAA74) as of 2020-05-29, what does the difference come from? Is it because of accurred interest?

1. When a bond has no credit ratings, i.e., none of the 3 credit agencies gives a rating, then its rating score is set to 0.

2. When running DIF end of month reports, back office team uses the last business day as the official reporting date, e.g., 29th for end of 2020 April. However, when a portfolio contains securities from other markets, say US equities, we may need to combine those prices on 30th Apr because 30th is not a US holiday. This is a consideration to be put here.

3. Duration data may be added later.


## Know Issues

1. REITs don't have the "SFC_AUTHORIZED_FUND" field, therefore used special case handling in isSFCAuthorized() function.


## Bloomberg Positions

To get position data from Bloomberg,

1. Go to MAV >> Views >> Open Position Views >> choose "Risk-Mon Steven" as the view.

2. Go to Settings >> MAV settings >> Accounts >> choose "RISK_M2" account group, then press "update".

3. On the date field, choose "As of" and input the desired date. Because the default is "Live", then in the output file there will be no date on the 4th line, causing the program to fail.

4. Go to Actions >> Export >> Export to Excel (formatted) to download the output Excel file.
