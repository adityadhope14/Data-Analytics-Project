# Sales Analytics Dashboard

## Problem Statement

Businesses collect sales data every day, but raw order records are difficult to explain in a presentation. This project turns local historical sales data into a clear analytics dashboard that helps users understand sales, profit, products, customers, and regional performance.

## Objective

The objective is to analyze sales performance using traditional Data Analytics techniques and present the results through an interactive Streamlit dashboard.

## Data Analytics Concepts Used

- Data loading and inspection
- Missing-value handling
- Data type conversion
- Date processing
- Filtering
- Grouping and aggregation
- Descriptive statistics
- KPI calculation
- Trend analysis
- Category and regional comparison
- Business insight generation

## Technology Stack

- Python
- Pandas
- Streamlit
- Plotly

No machine learning libraries or algorithms are used.

## Dataset Description

The dataset is generated locally and saved at:

`data/sales_data.csv`

Main fields include:

- Order ID
- Order Date
- Product
- Category
- Sub-Category
- Region
- State
- City
- Customer Segment
- Sales
- Quantity
- Discount
- Profit

## Data Preprocessing

The app performs simple, explainable preprocessing:

- Converts `Order Date` into a date type
- Converts sales, quantity, discount, and profit into numeric values
- Drops records missing essential order/date/sales/quantity data
- Fills missing discounts with 0
- Estimates missing profit values using the median profit margin
- Creates monthly date fields for trend analysis

## Analysis Methodology

The dashboard uses filtered data to calculate KPIs, group records by month/category/region/product, compare sales and profit performance, and generate business insights from the actual selected records.

## Dashboard Features

- Dynamic KPI cards
- Date, region, state, category, sub-category, product, and segment filters
- Monthly sales and profit trends
- Sales and profit by category
- Sales by region
- Top 10 products by sales
- Sales vs profit scatter plot
- Quantity by category
- Regional contribution trend
- Interactive filtered data table
- Automatically generated business insights

## How to Install

From this project folder, run:

```bash
python3 -m pip install -r requirements.txt
```

## How to Run

```bash
streamlit run app.py
```

If `streamlit` is not on your PATH, use:

```bash
python3 -m streamlit run app.py
```

## Expected Output

A local browser window opens with a professional sales analytics dashboard. Sidebar filters update the KPI cards, charts, insights, and data table dynamically.

## Key Insights You Can Present

- Which category produces the highest sales
- Which category produces the highest profit
- Which region performs best
- Which products sell the most
- How sales and profit change over time
- How discounts and product mix influence profitability

## Future Improvements

- Add more years of sales data
- Add return or refund analysis
- Add customer-level order history
- Export filtered reports to Excel or PDF
