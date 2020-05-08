# risk_report
Generate LQA request files



++++++++++
Bloomberg Data File
++++++++++
To generate Bloomberg file, 

1. Go to MAV >> Views >> Open Position Views >> choose "Risk-Mon Steven" as the view.

2. Go to Settings >> MAV settings >> Accounts >> choose "RISK_M2" account group, then press "update".

3. On the date field, choose "As of" and input the desired date. If you don't do that then "Live" will be the default, then in the output file there will be no date on the 4th line, causing the program to fail.

4. Go to Actions >> Export >> Export to Excel (formatted) to download the output Excel file.
