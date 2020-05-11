# risk_report
Generate LQA request files


++++++++++
To do
++++++++++
A bond has an invest id "XS1684793018 Perfshs" in DIF 2020-04-29 tax file. We need to convert that to ISIN.

1) use a special case handler.
2) after that, use a detector to check all ISIN codes.


++++++++++
Bloomberg Data File
++++++++++
To generate Bloomberg file, 

1. Go to MAV >> Views >> Open Position Views >> choose "Risk-Mon Steven" as the view.

2. Go to Settings >> MAV settings >> Accounts >> choose "RISK_M2" account group, then press "update".

3. On the date field, choose "As of" and input the desired date. If you don't do that then "Live" will be the default, then in the output file there will be no date on the 4th line, causing the program to fail.

4. Go to Actions >> Export >> Export to Excel (formatted) to download the output Excel file.
