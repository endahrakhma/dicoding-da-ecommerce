import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

import warnings
warnings.filterwarnings("ignore")

sns.set(style='dark')

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_english").cnt.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_city").customer_unique_id.nunique().sort_values(ascending=False).reset_index().head(10)
    bystate_df.rename(columns={
        "customer_unique_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_bypayment_df(df):
    bypayment_df = df.groupby(by="payment_type").order_id.nunique().sort_values(ascending=False).reset_index().head(4)
    bypayment_df.rename(columns={
        "order_id": "order_count"
    }, inplace=True)
    
    return bypayment_df

def create_byseller_df(df):
    byseller_df = df.groupby(by="seller_id").agg({'price':'sum'}).sort_values(by='price', ascending=False).reset_index().head(10)
    byseller_df.rename(columns={
        "price": "sales"
    }, inplace=True)
    
    return byseller_df

def create_byreview_df(df):
    byreview_df = df.groupby(by="review_score").product_id.nunique().sort_values(ascending=False).reset_index()
    byreview_df.rename(columns={
        "product_id": "review_count"
    }, inplace=True)
    
    return byreview_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

# Load cleaned data
all_df = pd.read_csv("merged_df.csv")

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("ecomm-logo.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Date Range',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    
    # Get unique values for the filter
    cities = ['All'] + list(all_df['customer_city'].unique())
    categories = ['All'] + list(all_df['product_category_english'].unique())
    
    # Create a multiselect widget for filtering by 'City'
    selected_cities = st.selectbox("Select a City", options=cities)
    selected_cat = st.selectbox("Select a Product Category", options=categories)

    if selected_cities == 'All' and selected_cat == 'All':
        main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & \
                         (all_df["order_purchase_timestamp"] <= str(end_date))]
    elif selected_cities != 'All' and selected_cat == 'All':
        main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & \
                         (all_df["order_purchase_timestamp"] <= str(end_date)) & \
                             (all_df["customer_city"]==selected_cities)]
    elif selected_cat != 'All' and selected_cities == 'All':
        main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & \
                         (all_df["order_purchase_timestamp"] <= str(end_date)) &\
                             (all_df["product_category_english"]==selected_cat)]
    else:
        main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & \
                         (all_df["order_purchase_timestamp"] <= str(end_date)) &\
                             (all_df["customer_city"]==selected_cities) & (all_df["product_category_english"]==selected_cat)]

# st.dataframe(main_df)

# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)
bypayment_df = create_bypayment_df(main_df)
byreview_df = create_byreview_df(main_df)
byseller_df = create_byseller_df(main_df)

# plot number of daily orders (2021)
st.header('Dicoding e-Commerce Dashboard :sparkles:')
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)


# Product performance
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="cnt", y="product_category_english", data=sum_order_items_df.sort_values(by="cnt", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="cnt", y="product_category_english", data=sum_order_items_df.sort_values(by="cnt", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

# customer behaviour
st.subheader("Customer Behaviour")

col1, col2 = st.columns(2)

# Create the pie chart
with col1:
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    #explode = (0.05, 0, 0, 0)
    colors = sns.color_palette('Blues')[0:len(bypayment_df)] # Use a Seaborn color palette
    ax.pie(bypayment_df['order_count'], labels=bypayment_df['payment_type'], autopct='%1.2f%%', colors=colors, startangle=45, textprops={'fontsize': 25})
    ax.axis('equal') # Ensures the pie chart is drawn as a circle
    ax.set_title("Trend of Payment Type", loc="center", fontsize=30, weight='bold')
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(dpi=170)
    #explode = (0.05, 0, 0, 0, 0)
    colors = sns.light_palette('seagreen')[0:len(byreview_df)] # Use a Seaborn color palette
    ax.pie(byreview_df['review_count'], labels=byreview_df['review_score'], autopct='%1.2f%%', colors=colors, startangle=45, textprops={'fontsize': 12})
    ax.axis('equal') # Ensures the pie chart is drawn as a circle
    ax.set_title("Distribution of Review Score", loc="center", fontsize=15, weight='bold')
    st.pyplot(fig)

st.subheader("Top 10 Number of Customer by City")

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3"]
sns.barplot(
    x="customer_count", 
    y="customer_city",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    palette=colors,
    ax=ax
)
#ax.set_title("Top 10 Number of Customer by City", loc="center", fontsize=30, weight='bold')
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader("Top 10 Seller by Total Sales")

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3","#D3D3D3"]
sns.barplot(
    x="sales", 
    y="seller_id",
    data=byseller_df.sort_values(by='sales', ascending=False),
    palette=colors,
    ax=ax
)
#ax.set_title("Top 10 Number of Customer by City", loc="center", fontsize=30, weight='bold')
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)


# Best Customer Based on RFM Parameters
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(30, 30))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(x="recency", y="customer_unique_id", orient='h', data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_xlabel(None)
ax[0].set_ylabel("customer_unique_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='x', labelsize=30, labelrotation=0)
ax[0].tick_params(axis='y', labelsize=30)


sns.barplot(x="frequency", y="customer_unique_id", orient='h', data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_xlabel(None)
ax[1].set_ylabel("customer_unique_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='x', labelsize=30, labelrotation=0)
ax[1].tick_params(axis='y', labelsize=30)


sns.barplot(x="monetary", y="customer_unique_id", orient='h', data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_xlabel(None)
ax[2].set_ylabel("customer_unique_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='x', labelsize=30, labelrotation=0)
ax[2].tick_params(axis='y', labelsize=30)


st.pyplot(fig)

st.caption('Dicoding e-Commerce Dashboard 2025')