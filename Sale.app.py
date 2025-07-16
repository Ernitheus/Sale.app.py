import streamlit as st
import pandas as pd

# --- CONFIGURATION ----------------------------------------------------------
CHLOE_RATE = 137.75             # hidden hourly cost for Chloe
CONTRACTOR_FIRST_FEE = 300       # $ per account month 1 (Premium)
CONTRACTOR_ONGOING_FEE = 200     # $ per account per subsequent month (Premium)

DEFAULT_PRICES = {
    "Plus": {"Monthly": 500, "6-Month": 3900, "Yearly": 5100},
    "Premium": {"Monthly": 1416, "6-Month": 6000, "Yearly": 11900},
}
CYCLE_MONTHS = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR: SETTINGS ------------------------------------------------------
st.sidebar.header("Calculator Settings")

# 1. Plan & Billing
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# 2. Pricing Override Pricing Override
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

# 5. Chloe Time per Account
st.sidebar.markdown("---")
st.sidebar.subheader("Chloe Time per Account")
chloe_hours_first = st.sidebar.number_input(
    "First Month Hours", min_value=0.0, value=2.0, step=0.25
)
chloe_hours_ongoing = st.sidebar.number_input(
    "Ongoing Monthly Hours", min_value=0.0, value=1.0, step=0.25
)

# 6. Premium-only: New vs. Ongoing Accounts & Contractor Cost
new_accounts = 0
contractor_estimate = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )
    ongoing_accounts = accounts - new_accounts
    # Estimate contractor flat fees
    contractor_estimate = (
        CONTRACTOR_FIRST_FEE * new_accounts
        + CONTRACTOR_ONGOING_FEE * ongoing_accounts * max(duration_months - 1, 0)
    )
    st.sidebar.metric("Contractor Cost (est.)", f"${contractor_estimate:,.2f}")

# 7. Minimum Margin Guard
min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)

# --- CORE CALCULATIONS ------------------------------------------------------
# Billing cycles count
cycles = duration_months / CYCLE_MONTHS[billing]

# TCV & Revenue
tcv = list_price * accounts * cycles
revenue = net_price * accounts * cycles

# Chloe cost total
total_chloe_cost = (
    CHLOE_RATE * chloe_hours_first * accounts
    + CHLOE_RATE * chloe_hours_ongoing * accounts * max(duration_months - 1, 0)
)

# Contractor cost actual
contractor_cost = contractor_estimate if plan == "Premium" else 0

# Total cost & margin
total_cost = round(total_chloe_cost + contractor_cost, 2)
margin_pct = ((revenue - total_cost) / revenue * 100) if revenue else 0

# --- MAIN OUTPUT ------------------------------------------------------------
def fmt_cur(v): return f"${v:,.2f}"
def fmt_pct(v): return f"{v:.2f}%"

st.subheader("Key Metrics")
cols = st.columns(8)
cols[0].metric("List Price/Cycle", fmt_cur(list_price))
cols[1].metric("Discount", fmt_cur(discount_amount))
cols[2].metric("Net Price/Cycle", fmt_cur(net_price))
cols[3].metric("Total Revenue", fmt_cur(revenue))
cols[4].metric("Chloe Cost", fmt_cur(total_chloe_cost))
cols[5].metric("Contractor Cost", fmt_cur(contractor_cost))
cols[6].metric("Total Cost", fmt_cur(total_cost))
cols[7].metric("Margin %", fmt_pct(margin_pct), delta=fmt_pct(margin_pct - min_margin))

st.subheader("Margin Threshold")
prog = margin_pct / min_margin if min_margin else 0
st.progress(min(max(prog, 0), 1))
if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Adjust inputs.")
else:
    st.success(f"✅ Margin at or above {min_margin}%.")

st.subheader("Total Contract Value (TCV)")
st.write(f"**Pre‑discount TCV:** {fmt_cur(tcv)}")

st.subheader("Cost Breakdown")
cost_items = {"Chloe Support": fmt_cur(total_chloe_cost)}
if contractor_cost:
    cost_items["Contractor Fees"] = fmt_cur(contractor_cost)
cost_items["Total Cost"] = fmt_cur(total_cost)
cost_df = (
    pd.DataFrame.from_dict(cost_items, orient="index", columns=["Cost"])  
    .rename_axis("Item")  
    .reset_index()
)
st.table(cost_df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
