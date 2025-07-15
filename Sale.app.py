import streamlit as st
import pandas as pd

# --- CONFIGURATION ----------------------------------------------------------
# Fixed unit costs (hidden rates)
CHLOE_RATE = 137.75            # Chloe's hourly rate
CONTRACTOR_FIRST = 300         # $ per account in first month (Premium)
CONTRACTOR_ONGOING = 200       # $ per account per subsequent month (Premium)

# Default list prices per billing cycle
default_prices = {
    "Plus": {"Monthly": 500, "6-Month": 3900, "Yearly": 5100},
    "Premium": {"Monthly": 1416, "6-Month": 6000, "Yearly": 11900},
}
# Mapping billing cycle to month count
cycle_months = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR: SETTINGS ------------------------------------------------------
st.sidebar.header("Calculator Settings")

# 1. Plan & Billing
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# 2. Pricing override("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# 2. Pricing override
def_lp = default_prices[plan][billing]
list_price = st.sidebar.number_input(
    "List Price per Cycle ($)", min_value=0.0, value=float(def_lp), step=50.0
)

# 3. Discount
discount_type = st.sidebar.radio("Discount Type", ["% Off", "$ Off"])
if discount_type == "% Off":
    pct = st.sidebar.slider("Discount %", 0, 100, 0) / 100
    net_price = list_price * (1 - pct)
else:
    amt = st.sidebar.number_input("Discount Amount ($)", min_value=0.0, value=0.0)
    net_price = max(list_price - amt, 0)

# 4. Accounts & Period
duration = st.sidebar.selectbox(
    "Analysis Period", [1, 6, 12, 24],
    format_func=lambda x: f"{x} {'months' if x!=1 else 'month'}" if x<24 else "2 years"
)
accounts = st.sidebar.number_input("Number of Accounts", min_value=1, value=1)

# 5. Chloe hours per account/month (hidden rate)
chloe_hours = st.sidebar.number_input(
    "Chloe Hours per Account/Month", min_value=0.0, value=1.0, step=0.25
)

# 6. Premium-only: new accounts setup
new_accounts = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )

# 7. Minimum margin guard
min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)

# --- CALCULATIONS -----------------------------------------------------------
# Determine number of billing cycles within analysis period
months = duration
cycle_len = cycle_months[billing]
cycles = months / cycle_len

# Contract and revenue
tcv = list_price * accounts * cycles
revenue = net_price * accounts * cycles

# Cost calculations
chloe_cost = CHLOE_RATE * chloe_hours * accounts * months
contractor_cost = 0
if plan == "Premium":
    ongoing_accounts = accounts - new_accounts
    # Flat fees for Premium plan
    contractor_cost = (
        CONTRACTOR_FIRST * new_accounts +
        CONTRACTOR_ONGOING * ongoing_accounts * max(months - 1, 0)
    )

total_cost = chloe_cost + contractor_cost
margin_pct = ((revenue - total_cost) / revenue * 100) if revenue else 0

def format_currency(val):
    return f"${val:,.2f}"

def format_percent(val):
    return f"{val:.2f}%"

# --- MAIN OUTPUT ------------------------------------------------------------
st.subheader("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("List Price/Cycle", format_currency(list_price))
col2.metric("Net Price/Cycle", format_currency(net_price))
col3.metric("Total Revenue", format_currency(revenue))
col4.metric("Total Cost", format_currency(total_cost))
col5.metric("Margin %", format_percent(margin_pct), delta=format_percent(margin_pct - min_margin))

st.subheader("Margin Threshold")
prog = margin_pct / min_margin if min_margin else 0
st.progress(min(max(prog, 0), 1))
if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Please adjust discount or inputs.")
else:
    st.success(f"✅ Margin is at or above {min_margin}%.")

st.subheader("Total Contract Value (TCV)")
st.write(f"**Pre‑discount TCV:** {format_currency(tcv)}")

st.subheader("Cost Breakdown")
cost_items = {"Chloe Support": format_currency(chloe_cost)}
if contractor_cost:
    cost_items["Contractor Fees"] = format_currency(contractor_cost)
cost_items["Total Cost"] = format_currency(total_cost)

cost_df = (
    pd.DataFrame.from_dict(cost_items, orient="index", columns=["Cost"])  
    .rename_axis("Item")  
    .reset_index()
)
st.table(cost_df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
