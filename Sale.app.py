import streamlit as st

# Page setup
st.set_page_config(page_title="Margin Calculator", layout="wide")

# Helper function
def calculate_margin(list_price, cost):
    if list_price == 0:
        return 0
    return (list_price - cost) / list_price * 100

# Sidebar: Inputs
st.sidebar.header("Settings")
plan = st.sidebar.selectbox(
    "Select Plan", 
    ["Plus (Accelerator + Launchpad)", "Premium (Launchpad Premium)"]
)
billing = st.sidebar.selectbox(
    "Billing Option", 
    ["Monthly", "6-Month Prepaid", "Yearly Prepaid"]
)
discount_type = st.sidebar.radio(
    "Discount Type", ["Percentage", "Absolute Amount"]
)
if discount_type == "Percentage":
    discount_pct = st.sidebar.slider("Discount %", 0, 100, 0)
    discount_val = discount_pct / 100
else:
    discount_val = st.sidebar.number_input("Discount ($)", min_value=0.0, value=0.0)

min_margin = st.sidebar.slider(
    "Minimum Margin %", 0, 100, 40
)

# Pricing definitions
prices = {
    "Plus (Accelerator + Launchpad)": {"Monthly": 500, "6-Month Prepaid": 500 * 6 * 0.9, "Yearly Prepaid": 6000},
    "Premium (Launchpad Premium)": {"Monthly": 1416, "6-Month Prepaid": 1416 * 6 * 0.95, "Yearly Prepaid": 17000}
}
list_price = prices[plan][billing]

# Apply discount
if discount_type == "Percentage":
    net_price = list_price * (1 - discount_val)
else:
    net_price = max(0, list_price - discount_val)

# Cost calculations
if plan == "Plus (Accelerator + Launchpad)":
    st.sidebar.markdown("---")
    chloe_rate = st.sidebar.number_input("Chloe's Hourly Rate ($)", value=137.75)
    hours_per_account = st.sidebar.number_input("Hours per Account / Month", value=1.0)
    cost = chloe_rate * hours_per_account
else:
    st.sidebar.markdown("---")
    month_sel = st.sidebar.selectbox("Month of Service", ["1st Month", "Ongoing"])
    first_month_cost = 300
    ongoing_cost = 200
    cost = first_month_cost if month_sel == "1st Month" else ongoing_cost

# Calculate margin
margin_pct = calculate_margin(net_price, cost)

# Main: Display
st.title("📊 Margin Calculator")

# Show key metrics
col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
col1.metric("List Price", f"${list_price:,.2f}")
col2.metric("Net Price", f"${net_price:,.2f}")
col3.metric("Cost", f"${cost:,.2f}")
col4.metric(
    "Margin %", 
    f"{margin_pct:.2f}%", 
    delta_color="inverse",
    delta=(margin_pct - min_margin),
)

st.markdown("---")

# Margin meter
st.subheader("Margin Threshold Meter")
progress = margin_pct / min_margin if min_margin else 0
st.progress(min(max(progress, 0.0), 1.0))

if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Adjust discount or cost.")
else:
    st.success(f"✅ Margin meets or exceeds {min_margin}%.")

# Optional chart area
# Users can extend this with Altair or Plotly for richer visuals

st.markdown("---")
st.caption("Built with ❤️ on Streamlit. Integrate this script into your GitHub repo and deploy to Streamlit Cloud.")
