# risk_report
The purpose of this package to convert Daphne Keung's Excel application into a Python application.

Purpose of this application:

1. Generate SFC report for DIF.

2. Generate liquidity report for all other portfolios in the company.



## To Do

Consider these special cases for asset types, whose "INDUSTRY_SECTOR" = "Funds"

JPMULCD LX Equity
2823 HK Equity
SPY US Equity
ICSUSPI ID Equity
CLFLDIF HK Equity
QQQ US Equity


NOTE: we can logic for ABS security, whose "INDUSTRY_SECTOR" = "Asset Backed Securities"

USG8116KAB82	ISIN



1. Bloomberg Position is in terms of 1,000s for Bond, should we X1000 for bond quantity when submitting for LQA request?

3. Consider refactor code to improve efficiency, tag each position with country and asset type first, then filter them.

4. Consider using Geneva as the asset type provider?




## Note

1. When a bond has no credit ratings, i.e., none of the 3 credit agencies gives a rating, then its rating score is set to 0. At least this is the logic on DIF 2020-04-29 report.

1. When running DIF end of month reports, back office team uses the last business day as the official reporting date, e.g., 29th for end of 2020 April. However, when a portfolio contains securities from other markets, say US equities, we may need to combine those prices on 30th Apr because 30th is not a US holiday. This is a consideration to be put here.

2. We may need to add duration data to all the bonds.


## Know Issues

1. REITs don't have the "SFC_AUTHORIZED_FUND" field, therefore used special case handling in isSFCAuthorized() function.


## Bloomberg Positions

To get position data from Bloomberg,

1. Go to MAV >> Views >> Open Position Views >> choose "Risk-Mon Steven" as the view.

2. Go to Settings >> MAV settings >> Accounts >> choose "RISK_M2" account group, then press "update".

3. On the date field, choose "As of" and input the desired date. Because the default is "Live", then in the output file there will be no date on the 4th line, causing the program to fail.

4. Go to Actions >> Export >> Export to Excel (formatted) to download the output Excel file.
