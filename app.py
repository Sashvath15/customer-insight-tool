# app.py - FIXED FOR STREAMLIT CLOUD (Using sample file)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_config="Customer Insight Tool",
    page_icon="📊",
    layout="wide"
)

# Import insight engine
try:
    from insight_engine import extract_insights, calculate_priorities, ASPECTS
except ImportError as e:
    st.error(f"Error: {e}")
    st.stop()

st.title("📊 Automated Customer Insight Tool")
st.markdown("Extract actionable product insights from customer reviews")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    num_reviews = st.slider("Reviews to analyze", 100, 500, 300)
    st.markdown("---")
    st.markdown("**Data:** Amazon Electronics Reviews (500 samples)")

# Load data - USE SAMPLE FILE
@st.cache_data
def load_data():
    """Load the smaller sample file"""
    if os.path.exists('sample_reviews.csv'):
        df = pd.read_csv('sample_reviews.csv')
        return df
    elif os.path.exists('Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products.csv'):
        # If original exists, take first 500 rows
        df = pd.read_csv('Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products.csv')
        df = df.head(500)
        df.to_csv('sample_reviews.csv', index=False)
        return df
    else:
        return None

# Load data
df = load_data()

if df is not None:
    # Prepare data
    reviews_df = pd.DataFrame()
    reviews_df['review_text'] = df['reviews.text']
    reviews_df['rating'] = df['reviews.rating']
    reviews_df['product_name'] = df['name'] if 'name' in df.columns else 'Unknown'
    reviews_df['brand'] = df['brand'] if 'brand' in df.columns else 'Unknown'
    reviews_df = reviews_df.dropna(subset=['review_text'])
    
    st.success(f"✅ Loaded {len(reviews_df)} reviews")
else:
    st.error("No data file found. Please ensure sample_reviews.csv is in the app directory.")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "🔍 Analysis", "💡 Recommendations"])

# Tab 1: Dashboard
with tab1:
    st.header("Run Analysis")
    
    if st.button("🚀 Start Analysis", type="primary"):
        with st.spinner(f"Analyzing {num_reviews} reviews..."):
            try:
                insights_df, sample_reviews = extract_insights(reviews_df, num_reviews)
                priority_results, sorted_aspects = calculate_priorities(insights_df, sample_reviews)
                
                st.session_state['insights_df'] = insights_df
                st.session_state['sorted_aspects'] = sorted_aspects
                st.session_state['priority_results'] = priority_results
                st.session_state['analysis_done'] = True
                
                st.success(f"✅ Done! Found {len(insights_df)} insights")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Reviews", num_reviews)
        with col2:
            st.metric("Aspects", len(ASPECTS))
        with col3:
            total_insights = len(st.session_state['insights_df'])
            st.metric("Insights", total_insights)
        
        # Priority Chart
        if sorted_aspects:
            aspects = [a for a, _ in sorted_aspects]
            scores = [s['priority_score'] for _, s in sorted_aspects]
            
            colors = ['red' if i < 2 else 'orange' if i < 4 else 'green' 
                     for i in range(len(aspects))]
            
            fig = go.Figure(data=[go.Bar(x=aspects, y=scores, 
                                        text=[f'{s:.3f}' for s in scores],
                                        textposition='auto',
                                        marker_color=colors)])
            fig.update_layout(title="Priority Scores", height=450)
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: Analysis
with tab2:
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        
        st.subheader("Priority Breakdown")
        for i, (aspect, scores) in enumerate(sorted_aspects[:5]):
            level = "🔴 CRITICAL" if i < 2 else "🟡 MEDIUM" if i < 4 else "🟢 LOW"
            st.markdown(f"**{level} - {aspect.upper()}**")
            st.markdown(f"- Score: {scores['priority_score']:.3f}")
            st.markdown(f- Mentions: {scores['total_mentions']} ({scores['frequency']*100:.1f}%)")
            st.markdown(f- Avg Rating: {scores['avg_rating']:.1f}/5.0")
            st.markdown("---")
    else:
        st.info("Click 'Start Analysis' first")

# Tab 3: Recommendations
with tab3:
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        insights_df = st.session_state['insights_df']
        
        recs = {
            'battery': ["🔋 Optimize power management", "⚡ Add fast charging"],
            'performance': ["🚀 Reduce lag", "💾 Fix memory leaks"],
            'screen': ["📱 Improve display quality", "🛡️ Add screen protector"],
            'connectivity': ["📶 Fix Bluetooth pairing", "🌐 Update WiFi drivers"],
            'software': ["🎨 Simplify interface", "📖 Add tutorial"],
            'build_quality': ["🔧 Improve materials", "✅ Better QC"],
            'sound': ["🔊 Enhance speakers", "🎚️ Add equalizer"],
            'value': ["💰 Adjust pricing", "📦 Add bundles"]
        }
        
        st.subheader("Top 3 Priorities")
        for i, (aspect, scores) in enumerate(sorted_aspects[:3]):
            st.markdown(f"### {i+1}. {aspect.upper()}")
            st.markdown(f"**Impact:** {scores['frequency']*100:.1f}% of customers")
            
            # Show a real quote
            quotes = insights_df[insights_df['aspect'] == aspect]['review_snippet'].head(1)
            if len(quotes) > 0:
                st.info(f"💬 Customer: \"{quotes.iloc[0][:100]}...\"")
            
            for rec in recs.get(aspect, ["Investigate issue"]):
                st.markdown(f"- {rec}")
            st.markdown("---")
    else:
        st.info("Click 'Start Analysis' first")

st.markdown("---")
st.caption("Built with Streamlit | Analyzes customer reviews to find actionable insights")