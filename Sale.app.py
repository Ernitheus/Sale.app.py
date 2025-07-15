import streamlit as st
import pandas as pd

# --- CONFIGURATION ----------------------------------------------------------
# Hidden rate constants
CHLOE_RATE = 137.75             # $ per Chloe hour (hidden)
CONTRACTOR_FIRST_FEE = 300       # $ per account month 1 (Premium)
CONTRACTOR_ONGOING_FEE = 200     # $ per account per subsequent month (Premium)

# Default list prices per billing cycle (overrideable)
DEFAULT_PRICES = {
    "Plus": {"Monthly": 500, "6-Month": 3900, "Yearly": 5100},
    "Premium": {"Monthly": 1416, "6-Month": 6000, "Yearly": 11900},
}
# Map billing cycles to month counts
CYCLE_MONTHS = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR: SETTINGS ------------------------------------------------------
st.sidebar.header("Calculator Settings")

# 1. Plan & Billing
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# 2. Pricing override
default_lp = DEFAULT_PRICES[plan][billing]
list_price = st.sidebar.number_input(
    "List Price per Cycle ($)", min_value=0.0, value=float(default_lp), step=50.0
)

# 3. Discount
discount_type = st.sidebar.radio("Discount Type", ["% Off", "$ Off"])
if discount_type == "% Off":
    discount_pct = st.sidebar.slider("Discount %", 0, 100, 0) / 100
    net_price = list_price * (1 - discount_pct)
    discount_amount = list_price * discount_pct
else:
    discount_amount = st.sidebar.number_input("Discount Amount ($)", min_value=0.0, value=0.0)
    net_price = max(list_price - discount_amount, 0)

# 4. Accounts & Period
duration_months = st.sidebar.selectbox(
    "Analysis Period", [1, 6, 12, 24],
    format_func=lambda x: f"{x} {'month' if x==1 else 'months'}" if x<24 else "2 years"
)
accounts = st.sidebar.number_input("Number of Accounts", min_value=1, value=1)

# 5. Chloe hours per account
st.sidebar.markdown("---")
st.sidebar.subheader("Chloe Time per Account")
chloe_hours_first = st.sidebar.number_input(
    "First Month Hours", min_value=0.0, value=2.0, step=0.25
)
chloe_hours_ongoing = st.sidebar.number_input(
    "Ongoing Monthly Hours", min_value=0.0, value=1.0, step=0.25
)

# 6. Premium-only: new accounts vs ongoing
new_accounts = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )

# 7. Minimum margin guard
min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)

# --- CALCULATIONS -----------------------------------------------------------
# Billing cycles in the analysis period
cycle_len = CYCLE_MONTHS[billing]
cycles = duration_months / cycle_len

# Total Contract Value & Revenue
tcv = list_price * accounts * cycles
revenue = net_price * accounts * cycles

# Chloe cost: dynamic hours per account
total_chloe_cost = (
    CHLOE_RATE * chloe_hours_first * accounts +
    CHLOE_RATE * chloe_hours_ongoing * accounts * max(duration_months - 1, 0)
)

# Contractor cost (Premium): flat fees per account
contractor_cost = 0
if plan == "Premium":
    ongoing_accounts = accounts - new_accounts
    contractor_cost = (
        CONTRACTOR_FIRST_FEE * new_accounts +
        CONTRACTOR_ONGOING_FEE * ongoing_accounts * max(duration_months - 1, 0)
    )

# Total cost and margin
total_cost = round(total_chloe_cost + contractor_cost, 2)
margin_pct = ((revenue - total_cost) / revenue * 100) if revenue else 0

# Formatting helpers
def format_currency(v): return f"${v:,.2f}"
def format_percent(v): return f"{v:.2f}%"

# --- MAIN OUTPUT ------------------------------------------------------------
st.subheader("Key Metrics")
# Columns: List Price, Discount, Net Price, Revenue, Chloe Cost, Contractor Cost, Total Cost, Margin
cols = st.columns(8)
cols[0].metric("List Price/Cycle", format_currency(list_price))
cols[1].metric("Discount", format_currency(discount_amount))
cols[2].metric("Net Price/Cycle", format_currency(net_price))
cols[3].metric("Total Revenue", format_currency(revenue))
cols[4].metric("Chloe Cost", format_currency(total_chloe_cost))
cols[5].metric("Contractor Cost", format_currency(contractor_cost))
cols[6].metric("Total Cost", format_currency(total_cost))
cols[7].metric("Margin %", format_percent(margin_pct), delta=format_percent(margin_pct - min_margin))

st.subheader("Margin Threshold")
progress = margin_pct / min_margin if min_margin else 0
st.progress(min(max(progress, 0.0), 1.0))
if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Adjust inputs.")
else:
    st.success(f"✅ Margin at or above {min_margin}%.")

st.subheader("Total Contract Value (TCV)")
st.write(f"**Pre‑discount TCV:** {format_currency(tcv)}")

st.subheader("Cost Breakdown")
costs = {
    "Chloe Support": format_currency(total_chloe_cost)
}
if contractor_cost:
    costs["Contractor Fees"] = format_currency(contractor_cost)
costs["Total Cost"] = format_currency(total_cost)
cost_df = (
    pd.DataFrame.from_dict(costs, orient="index", columns=["Cost"])  
    .rename_axis("Item")  
    .reset_index()
)
st.table(cost_df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
