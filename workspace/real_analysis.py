#!/usr/bin/env python
import pandas as pd
# Load the data from a CSV file
data = pd.read_csv('your_data.csv')
# Perform some analysis on the data
summary = data.describe()
print(summary)