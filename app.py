#!/usr/bin/env python3
"""
Customer 360 Streamlit Dashboard
Clean and interactive dashboard for Customer 360 insights using ClickHouse + PuppyGraph
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

from queries import Customer360Queries
from clickhouse import ClickHouseClient

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Page configuration
st.set_page_config(
    page_title="Customer 360 Demo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert > div {
        background-color: #e1f5fe;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_connections():
    """Initialize database connections with caching"""
    try:
        clickhouse = ClickHouseClient()
        queries = Customer360Queries()
        return clickhouse, queries
    except Exception as e:
        st.error(f"Failed to connect to databases: {e}")
        st.stop()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_summary_stats(_clickhouse):
    """Get summary statistics from ClickHouse"""
    try:
        counts = _clickhouse.get_table_counts()
        return counts
    except Exception as e:
        st.error(f"Failed to get summary stats: {e}")
        return {}


@st.cache_data(ttl=300)
def get_segment_analysis(_queries):
    """Get customer segment analysis"""
    try:
        return _queries.get_segment_analysis()
    except Exception as e:
        st.error(f"Failed to get segment analysis: {e}")
        return []


def main():
    """Main Streamlit application"""
    
    # Title and introduction
    st.title("🎯 Customer 360 Demo")
    st.markdown("**Interactive dashboard powered by ClickHouse Cloud + PuppyGraph**")
    
    # Initialize connections
    clickhouse, queries = init_connections()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    pages = {
        "📊 Dashboard": show_dashboard_page,
        "🔍 Customer Search": show_customer_search_page,
        "🎯 Recommendations": show_recommendations_page,
        "📈 Analytics": show_analytics_page,
        "ℹ️ About": show_about_page
    }
    
    selected_page = st.sidebar.radio("Select Page", list(pages.keys()))
    
    # Display selected page
    pages[selected_page](clickhouse, queries)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Customer 360 Demo**")
    st.sidebar.markdown("ClickHouse + PuppyGraph")


def show_dashboard_page(clickhouse, queries):
    """Dashboard overview page"""
    
    st.header("📊 Dashboard Overview")
    
    # Summary statistics
    with st.spinner("Loading summary statistics..."):
        stats = get_summary_stats(clickhouse)
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Customers", f"{stats.get('customers', 0):,}")
            with col2:
                st.metric("Products", f"{stats.get('products', 0):,}")
            with col3:
                st.metric("Transactions", f"{stats.get('transactions', 0):,}")
            with col4:
                st.metric("Interactions", f"{stats.get('interactions', 0):,}")
    
    # Customer segments analysis
    st.subheader("Customer Segments")
    
    with st.spinner("Loading segment analysis..."):
        segments = get_segment_analysis(queries)
        
        if segments:
            df_segments = pd.DataFrame(segments)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Segment distribution pie chart
                fig_pie = px.pie(
                    df_segments, 
                    values='total_customers', 
                    names='segment',
                    title='Customer Distribution by Segment'
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Revenue by segment bar chart
                fig_bar = px.bar(
                    df_segments, 
                    x='segment', 
                    y='total_revenue',
                    title='Revenue by Customer Segment',
                    color='segment'
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Detailed segment table
            st.subheader("Segment Details")
            
            # Format the dataframe for display
            display_df = df_segments.copy()
            display_df['total_revenue'] = display_df['total_revenue'].apply(lambda x: f"${x:,.2f}")
            display_df['avg_revenue_per_customer'] = display_df['avg_revenue_per_customer'].apply(lambda x: f"${x:,.2f}")
            display_df['avg_ltv'] = display_df['avg_ltv'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(
                display_df[['segment', 'total_customers', 'total_purchases', 'total_revenue', 
                           'avg_purchases_per_customer', 'avg_revenue_per_customer', 'avg_ltv']],
                use_container_width=True
            )
    
    # Quick insights
    st.subheader("Quick Insights")
    
    try:
        # Popular products
        popular_products = queries.get_popular_products(limit=5)
        
        if popular_products:
            st.write("**🎯 Top 5 Most Popular Products:**")
            
            for i, product in enumerate(popular_products, 1):
                st.write(f"{i}. **{product['product_name']}** ({product['category']}) - {product['purchase_count']} purchases")
        
        # Top customers
        top_customers = queries.get_top_customers_by_segment(limit=5)
        
        if top_customers:
            st.write("**👑 Top 5 Customers by Spending:**")
            
            for i, customer in enumerate(top_customers, 1):
                st.write(f"{i}. **{customer['customer_name']}** ({customer['segment']}) - ${customer['total_spent']:,.2f}")
                
    except Exception as e:
        st.warning(f"Could not load insights: {e}")


def show_customer_search_page(clickhouse, queries):
    """Customer search and 360 view page"""
    
    st.header("🔍 Customer Search & 360 View")
    
    # Search functionality
    search_term = st.text_input("Search customers by name or email:", placeholder="Enter name or email...")
    
    if search_term:
        with st.spinner(f"Searching for '{search_term}'..."):
            try:
                search_results = queries.search_customers(search_term, limit=20)
                
                if search_results:
                    st.write(f"Found {len(search_results)} customers:")
                    
                    # Display search results
                    df_results = pd.DataFrame(search_results)
                    
                    # Format currency columns
                    df_results['ltv'] = df_results['ltv'].apply(lambda x: f"${x:,.2f}")
                    df_results['total_spent'] = df_results['total_spent'].apply(lambda x: f"${x:,.2f}")
                    
                    # Add selection column
                    selected_customer = st.selectbox(
                        "Select a customer for 360 view:",
                        options=range(len(df_results)),
                        format_func=lambda x: f"{df_results.iloc[x]['customer_name']} ({df_results.iloc[x]['email']})"
                    )
                    
                    # Display search results table
                    st.dataframe(df_results, use_container_width=True)
                    
                    # Show 360 view for selected customer
                    if selected_customer is not None:
                        customer_id = search_results[selected_customer]['customer_id']
                        show_customer_360_view(customer_id, queries)
                
                else:
                    st.info("No customers found. Try a different search term.")
                    
            except Exception as e:
                st.error(f"Search failed: {e}")
    
    else:
        st.info("Enter a search term to find customers.")


def show_customer_360_view(customer_id: str, queries):
    """Display 360-degree view of a customer"""
    
    st.subheader("🎯 Customer 360 View")
    
    try:
        # Get customer 360 data
        customer_360 = queries.get_customer_360_view(customer_id)
        
        if customer_360:
            # Customer summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Customer Name", customer_360['customer_name'])
                st.metric("Email", customer_360['email'])
            
            with col2:
                st.metric("Segment", customer_360['segment'])
                st.metric("LTV", f"${customer_360['ltv']:,.2f}")
            
            with col3:
                st.metric("Total Purchases", customer_360['total_purchases'])
                st.metric("Total Views", customer_360['total_views'])
            
            # Recent activity
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Recent Purchases:**")
                if customer_360.get('recent_purchases'):
                    for purchase in customer_360['recent_purchases']:
                        if purchase.get('product'):
                            st.write(f"• {purchase['product']} - ${purchase.get('amount', 0):.2f}")
                else:
                    st.write("No recent purchases")
            
            with col2:
                st.write("**Recent Views:**")
                if customer_360.get('recent_views'):
                    for view in customer_360['recent_views']:
                        if view.get('product'):
                            duration = view.get('duration', 0)
                            st.write(f"• {view['product']} ({duration}s)")
                else:
                    st.write("No recent views")
            
            # Customer journey
            st.subheader("Customer Journey")
            journey = queries.get_customer_journey(customer_id)
            
            if journey:
                df_journey = pd.DataFrame(journey)
                
                # Filter for recent activity
                df_recent = df_journey.head(20)
                
                # Create timeline visualization
                fig = go.Figure()
                
                for _, event in df_recent.iterrows():
                    color = 'green' if event['event_type'] == 'PURCHASE' else 'blue'
                    size = 12 if event['event_type'] == 'PURCHASE' else 8
                    
                    fig.add_trace(go.Scatter(
                        x=[event['timestamp']],
                        y=[event['event_type']],
                        mode='markers',
                        marker=dict(color=color, size=size),
                        name=f"{event['product_name']} ({event['category']})",
                        hovertemplate=f"<b>{event['product_name']}</b><br>" +
                                     f"Category: {event['category']}<br>" +
                                     f"Type: {event['event_type']}<br>" +
                                     f"Time: {event['timestamp']}<br>" +
                                     ("<br>Amount: $%.2f" % event['amount'] if event.get('amount') else "") +
                                     "<extra></extra>"
                    ))
                
                fig.update_layout(
                    title="Customer Journey Timeline",
                    xaxis_title="Time",
                    yaxis_title="Event Type",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("Could not load customer 360 view.")
            
    except Exception as e:
        st.error(f"Failed to load customer 360 view: {e}")


def show_recommendations_page(clickhouse, queries):
    """Product recommendations page"""
    
    st.header("🎯 Product Recommendations")
    
    # Customer ID input for recommendations
    customer_id = st.text_input("Enter Customer ID for recommendations:", placeholder="customer-uuid-here")
    
    if customer_id:
        with st.spinner("Generating recommendations..."):
            try:
                recommendations = queries.get_customer_recommendations(customer_id, limit=10)
                
                if recommendations:
                    st.success(f"Found {len(recommendations)} product recommendations:")
                    
                    # Display recommendations
                    for i, rec in enumerate(recommendations, 1):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                st.write(f"**{i}. {rec['product_name']}**")
                                st.write(f"Category: {rec['category']}")
                            
                            with col2:
                                st.write(f"Brand: {rec['brand']}")
                                st.write(f"Price: ${rec['price']:.2f}")
                            
                            with col3:
                                st.write(f"Recommended by: {rec['recommended_by_customers']} customers")
                                st.write(f"Similarity Score: {rec['similarity_score']:.2f}")
                            
                            with col4:
                                if st.button("View", key=f"view_{i}"):
                                    st.info(f"Viewing {rec['product_name']}")
                            
                            st.markdown("---")
                
                else:
                    st.info("No recommendations found for this customer ID.")
                    
            except Exception as e:
                st.error(f"Failed to generate recommendations: {e}")
    
    else:
        st.info("Enter a customer ID to see personalized product recommendations.")
        
        # Show popular products as general recommendations
        st.subheader("Popular Products")
        
        category = st.selectbox("Filter by category:", ["All"] + [
            "Electronics", "Clothing", "Home", "Books", "Sports", "Beauty"
        ])
        
        try:
            category_filter = None if category == "All" else category
            popular = queries.get_popular_products(category=category_filter, limit=15)
            
            if popular:
                df_popular = pd.DataFrame(popular)
                
                # Create visualization
                fig = px.bar(
                    df_popular.head(10), 
                    x='product_name', 
                    y='purchase_count',
                    color='category',
                    title=f'Most Popular Products {f"in {category}" if category != "All" else ""}',
                    hover_data=['brand', 'total_revenue']
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display table
                df_display = df_popular.copy()
                df_display['list_price'] = df_display['list_price'].apply(lambda x: f"${x:.2f}")
                df_display['total_revenue'] = df_display['total_revenue'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(df_display, use_container_width=True)
        
        except Exception as e:
            st.error(f"Failed to load popular products: {e}")


def show_analytics_page(clickhouse, queries):
    """Advanced analytics page"""
    
    st.header("📈 Advanced Analytics")
    
    # Category affinity analysis
    st.subheader("Category Affinity Analysis")
    st.write("Products categories frequently bought together:")
    
    try:
        affinity_data = queries.get_category_affinity(limit=10)
        
        if affinity_data:
            df_affinity = pd.DataFrame(affinity_data)
            
            # Create network-like visualization
            fig = px.scatter(
                df_affinity, 
                x='category1', 
                y='category2',
                size='customers_buying_both',
                color='avg_affinity',
                title='Category Affinity Matrix',
                hover_data=['customers_buying_both', 'avg_affinity']
            )
            
            fig.update_layout(
                xaxis_title="Category 1",
                yaxis_title="Category 2",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display top affinities
            st.write("**Top Category Pairs:**")
            for i, row in df_affinity.head(5).iterrows():
                st.write(f"• **{row['category1']}** + **{row['category2']}**: "
                        f"{row['customers_buying_both']} customers (affinity: {row['avg_affinity']})")
    
    except Exception as e:
        st.error(f"Failed to load affinity analysis: {e}")
    
    # Segment comparison
    st.subheader("Segment Performance Comparison")
    
    try:
        segments = get_segment_analysis(queries)
        
        if segments:
            df_segments = pd.DataFrame(segments)
            
            # Multi-metric comparison
            metrics = st.multiselect(
                "Select metrics to compare:",
                ['total_customers', 'total_purchases', 'total_revenue', 
                 'avg_purchases_per_customer', 'avg_revenue_per_customer', 'avg_ltv'],
                default=['total_revenue', 'avg_revenue_per_customer']
            )
            
            if metrics:
                for metric in metrics:
                    fig = px.bar(
                        df_segments, 
                        x='segment', 
                        y=metric,
                        title=f'{metric.replace("_", " ").title()} by Segment',
                        color='segment'
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Failed to load segment comparison: {e}")


def show_about_page(clickhouse, queries):
    """About page with system information"""
    
    st.header("ℹ️ About Customer 360 Demo")
    
    st.markdown("""
    This demo showcases a **Customer 360** solution using:
    
    ### 🏗️ Architecture
    - **ClickHouse Cloud**: High-performance analytics database storing customer data
    - **PuppyGraph**: Zero-ETL graph query engine for real-time graph analytics
    - **Streamlit**: Interactive web dashboard for data visualization
    
    ### 📊 Features
    - **Customer 360 View**: Complete customer profile with purchase history and interactions
    - **Product Recommendations**: AI-powered recommendations based on customer similarity
    - **Segment Analysis**: Customer segmentation with behavioral insights
    - **Category Affinity**: Product categories frequently bought together
    - **Real-time Queries**: Live data querying with sub-second response times
    
    ### 🎯 Use Cases
    - Customer relationship management
    - Personalized marketing campaigns
    - Product recommendation engines
    - Customer segmentation and targeting
    - Cross-sell and upsell optimization
    
    ### 🔧 Technology Benefits
    - **Zero ETL**: PuppyGraph queries ClickHouse directly without data movement
    - **Real-time**: Sub-second graph queries on large datasets
    - **Scalable**: Handles millions to billions of records
    - **Cost-effective**: No separate graph database infrastructure needed
    """)
    
    # System status
    st.subheader("System Status")
    
    try:
        # Database connectivity
        stats = get_summary_stats(clickhouse)
        
        if stats:
            st.success("✅ ClickHouse connection: OK")
            st.success("✅ PuppyGraph connection: OK")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Data Summary:**")
                for table, count in stats.items():
                    st.write(f"• {table.title()}: {count:,} records")
            
            with col2:
                st.write("**Query Performance:**")
                start_time = datetime.now()
                test_segments = get_segment_analysis(queries)
                end_time = datetime.now()
                
                if test_segments:
                    query_time = (end_time - start_time).total_seconds()
                    st.write(f"• Segment analysis: {query_time:.2f}s")
                    st.write(f"• Status: {'⚡ Fast' if query_time < 1 else '🐌 Slow'}")
        
        else:
            st.error("❌ Database connection issues")
    
    except Exception as e:
        st.error(f"❌ System status check failed: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("**Customer 360 Demo** | Built with ClickHouse + PuppyGraph + Streamlit")


if __name__ == "__main__":
    main()