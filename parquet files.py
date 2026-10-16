import pandas as pd

sales1 = [
    [1001, "2026-10-01", 1, 101, 2, 500.00],
    [1002, "2026-10-01", 2, 102, 3, 250.00],
    [1003, "2026-10-01", 1, 103, 1, 1000.00]
]

sales2 = [
    [1004, "2026-10-02", 3, 101, 2, 500.00],
    [1005, "2026-10-02", 2, 104, 4, 300.00],
    [1006, "2026-10-02", 1, 102, 2, 250.00]
]

sales3 = [
    [1007, "2026-10-03", 3, 103, 2, 1000.00],
    [1008, "2026-10-03", 2, 101, 1, 500.00],
    [1009, "2026-10-03", 1, 104, 3, 300.00]
]

columns = [
    "OrderID",
    "OrderDate",
    "EmployeeID",
    "ProductID",
    "Quantity",
    "UnitPrice"
]

pd.DataFrame(sales1, columns=columns).to_parquet(
    "Sales_20261001.parquet",
    index=False
)

pd.DataFrame(sales2, columns=columns).to_parquet(
    "Sales_20261002.parquet",
    index=False
)

pd.DataFrame(sales3, columns=columns).to_parquet(
    "Sales_20261003.parquet",
    index=False
)

print("Parquet files created successfully.")