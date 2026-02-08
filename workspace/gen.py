#!/usr/bin/env python3
import random
import csv
rows = []
for i in range(50):
    quantity = random.randint(1, 100)
    price = round(random.uniform(1.0, 100.0), 2)
    rows.append([quantity, price])
csv_columns = ['Quantity', 'Price']
with open('gen.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(csv_columns)
    writer.writerows(rows)