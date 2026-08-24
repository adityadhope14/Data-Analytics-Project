from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sales_data.csv"

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="SA",
    layout="wide",
)


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1420px;
    }
    .dashboard-title {
        font-size: 2.15rem;
        font-weight: 800;
        color: #172033;
        margin-bottom: 0.2rem;
    }
    .dashboard-subtitle {
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 1.25rem;
    }
    .kpi-card {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 1rem;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        min-height: 118px;
    }
    .kpi-label {
        color: #5b6472;
        font-size: 0.85rem;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        color: #111827;
        font-size: 1.55rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-help {
        color: #6b7280;
        font-size: 0.78rem;
        margin-top: 0.35rem;
    }
    .insight-box {
        border-left: 4px solid #2563eb;
        background: #f8fafc;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.65rem;
        color: #1f2937;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.45rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_sales_data() -> pd.DataFrame:
    """Load and clean the sales dataset for dashboard analysis."""
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    numeric_columns = ["Sales", "Quantity", "Discount", "Profit"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["Order ID", "Order Date", "Sales", "Quantity"])
    df["Discount"] = df["Discount"].fillna(0)

    # Missing profit is estimated with the current row's sales and median profit margin.
    median_margin = (df["Profit"] / df["Sales"]).replace([float("inf"), -float("inf")], pd.NA).median()
    df["Profit"] = df["Profit"].fillna(df["Sales"] * median_margin)

    text_columns = ["Product", "Category", "Sub-Category", "Region", "State", "City", "Customer Segment"]
    for column in text_columns:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()

    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Label"] = df["Month"].dt.strftime("%b %Y")
    df["Profit Margin"] = df["Profit"] / df["Sales"]
    return df.sort_values("Order Date")


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_number(value: float) -> str:
    return f"{value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def multiselect_filter(label: str, values: pd.Series) -> list[str]:
    options = sorted(values.dropna().unique().tolist())
    return st.sidebar.multiselect(label, options=options, default=options)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    min_date = df["Order Date"].min().date()
    max_date = df["Order Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    selected_regions = multiselect_filter("Region", df["Region"])
    selected_states = multiselect_filter("State", df[df["Region"].isin(selected_regions)]["State"] if selected_regions else df["State"])
    selected_categories = multiselect_filter("Category", df["Category"])
    selected_subcategories = multiselect_filter(
        "Sub-Category",
        df[df["Category"].isin(selected_categories)]["Sub-Category"] if selected_categories else df["Sub-Category"],
    )
    selected_products = multiselect_filter(
        "Product",
        df[df["Sub-Category"].isin(selected_subcategories)]["Product"] if selected_subcategories else df["Product"],
    )
    selected_segments = multiselect_filter("Customer Segment", df["Customer Segment"])

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    filtered = df[
        (df["Order Date"].dt.date >= start_date)
        & (df["Order Date"].dt.date <= end_date)
        & (df["Region"].isin(selected_regions))
        & (df["State"].isin(selected_states))
        & (df["Category"].isin(selected_categories))
        & (df["Sub-Category"].isin(selected_subcategories))
        & (df["Product"].isin(selected_products))
        & (df["Customer Segment"].isin(selected_segments))
    ].copy()
    return filtered


def render_kpi_cards(df: pd.DataFrame) -> None:
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order ID"].nunique()
    total_quantity = df["Quantity"].sum()
    average_order_value = total_sales / total_orders if total_orders else 0
    profit_margin = total_profit / total_sales if total_sales else 0

    cards = [
        ("Total Sales", format_currency(total_sales), "Revenue after discounts"),
        ("Total Profit", format_currency(total_profit), "Profit from filtered orders"),
        ("Total Orders", format_number(total_orders), "Unique order count"),
        ("Total Quantity", format_number(total_quantity), "Items sold"),
        ("Average Order Value", format_currency(average_order_value), "Sales per order"),
        ("Profit Margin", format_percent(profit_margin), "Profit as a share of sales"),
    ]
    cols = st.columns(6)
    for col, (label, value, help_text) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-help">{help_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def make_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    fig = px.bar(data, x=x, y=y, color=color, title=title, text_auto=".2s")
    fig.update_layout(yaxis_tickprefix="$" if "Sales" in y or "Profit" in y else "", hovermode="x unified")
    fig.update_traces(hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>")
    return fig


def render_charts(df: pd.DataFrame) -> None:
    monthly = df.groupby("Month", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    category = df.groupby("Category", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"))
    region = df.groupby("Region", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    product = df.groupby("Product", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).sort_values("Sales", ascending=False).head(10)

    st.subheader("Sales and Profit Trends")
    left, right = st.columns(2)
    sales_trend = px.line(monthly, x="Month", y="Sales", markers=True, title="Monthly Sales Trend")
    sales_trend.update_layout(yaxis_tickprefix="$", hovermode="x unified", xaxis_title="Month", yaxis_title="Sales")
    right_profit = px.line(monthly, x="Month", y="Profit", markers=True, title="Monthly Profit Trend")
    right_profit.update_layout(yaxis_tickprefix="$", hovermode="x unified", xaxis_title="Month", yaxis_title="Profit")
    left.plotly_chart(sales_trend, width="stretch")
    right.plotly_chart(right_profit, width="stretch")

    st.subheader("Category and Regional Performance")
    c1, c2 = st.columns(2)
    c1.plotly_chart(make_bar_chart(category.sort_values("Sales", ascending=False), "Category", "Sales", "Sales by Category", "Category"), width="stretch")
    c2.plotly_chart(make_bar_chart(category.sort_values("Profit", ascending=False), "Category", "Profit", "Profit by Category", "Category"), width="stretch")

    c3, c4 = st.columns(2)
    region_fig = px.pie(region, names="Region", values="Sales", title="Sales by Region", hole=0.38)
    region_fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>$%{value:,.2f}<extra></extra>")
    c3.plotly_chart(region_fig, width="stretch")
    c4.plotly_chart(make_bar_chart(category.sort_values("Quantity", ascending=False), "Category", "Quantity", "Quantity by Category", "Category"), width="stretch")

    st.subheader("Product and Profitability Details")
    c5, c6 = st.columns(2)
    top_products = px.bar(product.sort_values("Sales"), x="Sales", y="Product", orientation="h", title="Top 10 Products by Sales", text_auto=".2s")
    top_products.update_layout(xaxis_tickprefix="$", xaxis_title="Sales", yaxis_title="Product")
    c5.plotly_chart(top_products, width="stretch")

    scatter = px.scatter(
        df,
        x="Sales",
        y="Profit",
        size="Quantity",
        color="Category",
        hover_data=["Order ID", "Product", "Region", "Customer Segment"],
        title="Sales vs Profit",
    )
    scatter.update_layout(xaxis_tickprefix="$", yaxis_tickprefix="$", xaxis_title="Sales", yaxis_title="Profit")
    c6.plotly_chart(scatter, width="stretch")

    monthly_region = df.groupby(["Month", "Region"], as_index=False)["Sales"].sum()
    region_trend = px.area(monthly_region, x="Month", y="Sales", color="Region", title="Monthly Sales Contribution by Region")
    region_trend.update_layout(yaxis_tickprefix="$", hovermode="x unified", xaxis_title="Month", yaxis_title="Sales")
    st.plotly_chart(region_trend, width="stretch")


def generate_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No insights are available because the selected filters returned no records."]

    category_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    category_profit = df.groupby("Category")["Profit"].sum().sort_values(ascending=False)
    region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    product_sales = df.groupby("Product")["Sales"].sum().sort_values(ascending=False)
    product_profit = df.groupby("Product")["Profit"].sum().sort_values(ascending=False)
    monthly_sales = df.groupby("Month")["Sales"].sum().sort_index()
    margin = df["Profit"].sum() / df["Sales"].sum() if df["Sales"].sum() else 0

    growth_text = "There is not enough monthly data to calculate a sales change."
    if len(monthly_sales) >= 2 and monthly_sales.iloc[0] != 0:
        growth = (monthly_sales.iloc[-1] - monthly_sales.iloc[0]) / monthly_sales.iloc[0]
        direction = "increased" if growth >= 0 else "decreased"
        growth_text = f"Sales {direction} by {abs(growth):.1%} from {monthly_sales.index[0].strftime('%b %Y')} to {monthly_sales.index[-1].strftime('%b %Y')}."

    return [
        f"{category_sales.index[0]} is the highest-selling category with {format_currency(category_sales.iloc[0])} in sales.",
        f"{category_profit.index[0]} is the most profitable category with {format_currency(category_profit.iloc[0])} profit.",
        f"{region_sales.index[0]} is the best-performing region by sales.",
        f"{product_sales.index[0]} is the top product by sales, while {product_profit.index[0]} is the top product by profit.",
        f"The best sales month is {monthly_sales.idxmax().strftime('%B %Y')} with {format_currency(monthly_sales.max())} in sales.",
        f"{category_sales.index[-1]} is the lowest-selling category in the current selection.",
        f"The current profit margin is {format_percent(margin)}, which helps explain how efficiently sales become profit.",
        growth_text,
    ]


def render_data_table(df: pd.DataFrame) -> None:
    table = df[
        [
            "Order ID",
            "Order Date",
            "Product",
            "Category",
            "Sub-Category",
            "Region",
            "State",
            "City",
            "Customer Segment",
            "Sales",
            "Quantity",
            "Discount",
            "Profit",
        ]
    ].sort_values("Order Date", ascending=False).copy()
    table["Discount"] = table["Discount"] * 100
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Order Date": st.column_config.DateColumn("Order Date", format="YYYY-MM-DD"),
            "Sales": st.column_config.NumberColumn("Sales", format="$%.2f"),
            "Discount": st.column_config.NumberColumn("Discount", format="%.0f%%"),
            "Profit": st.column_config.NumberColumn("Profit", format="$%.2f"),
        },
    )


def main() -> None:
    st.markdown('<div class="dashboard-title">Sales Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-subtitle">A local, beginner-friendly data analytics dashboard for exploring sales, profit, products, regions, and business performance.</div>',
        unsafe_allow_html=True,
    )

    df = load_sales_data()
    filtered_df = apply_filters(df)

    if filtered_df.empty:
        st.warning("No sales records match the selected filters. Please adjust the sidebar filters.")
        render_kpi_cards(filtered_df)
        st.subheader("Business Insights")
        st.info("No insights are available for an empty selection.")
        return

    render_kpi_cards(filtered_df)

    with st.expander("Dataset and Cleaning Summary", expanded=False):
        st.write(
            f"Loaded {len(df):,} cleaned sales records from the local CSV. Dates are converted, numeric columns are validated, missing discounts are treated as 0, and missing profit values are estimated from the median profit margin."
        )
        summary_columns = ["Sales", "Quantity", "Discount", "Profit", "Profit Margin"]
        st.dataframe(filtered_df[summary_columns].describe(), width="stretch")
        st.write("Missing values after cleaning:")
        st.dataframe(filtered_df.isna().sum().rename("Missing Values").reset_index().rename(columns={"index": "Column"}), width="stretch", hide_index=True)

    render_charts(filtered_df)

    st.subheader("Business Insights")
    for insight in generate_insights(filtered_df):
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

    st.subheader("Filtered Sales Records")
    render_data_table(filtered_df)


if __name__ == "__main__":
    main()
