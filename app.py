# app.py - FIXED FOR STREAMLIT CLOUD
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="Customer Insight Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import insight engine
try:
    from insight_engine import extract_insights, calculate_priorities, ASPECTS
except ImportError as e:
    st.error(f"Error importing insight_engine: {e}")
    st.stop()

# Title
st.title("📊 Automated Customer Insight Tool")
st.markdown("""
    ### Extract actionable product insights from customer reviews
    
    This tool analyzes customer reviews to identify what features need improvement.
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    num_reviews = st.slider(
        "Number of reviews to analyze",
        min_value=100,
        max_value=2000,
        value=500,
        step=100,
        help="More reviews = more accurate but slower"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Techniques:**
    - Aspect-Based Sentiment Analysis
    - Priority Scoring Algorithm
    
    **Data:** Amazon Electronics Reviews
    """)

# Check if data file exists
@st.cache_data
def load_data():
    """Load the CSV file"""
    # Try different possible file names
    possible_files = [
        'Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products.csv',
        'sample_reviews.csv',
        'data.csv'
    ]
    
    for file_name in possible_files:
        if os.path.exists(file_name):
            try:
                df = pd.read_csv(file_name)
                return df, file_name
            except Exception as e:
                continue
    
    return None, None

# Load data
df, file_used = load_data()

if df is not None:
    # Prepare data
    reviews_df = df[['reviews.text', 'reviews.rating', 'name', 'brand']].copy()
    reviews_df.columns = ['review_text', 'rating', 'product_name', 'brand']
    reviews_df = reviews_df.dropna(subset=['review_text'])
    
    st.success(f"✅ Loaded {len(reviews_df)} reviews from {file_used}")
else:
    st.error("""
    ❌ Data file not found!
    
    Please upload your CSV file using the button below.
    """)
    
    # File uploader for Streamlit Cloud
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        reviews_df = df[['reviews.text', 'reviews.rating', 'name', 'brand']].copy()
        reviews_df.columns = ['review_text', 'rating', 'product_name', 'brand']
        reviews_df = reviews_df.dropna(subset=['review_text'])
        st.success(f"✅ Loaded {len(reviews_df)} reviews from uploaded file")
        st.rerun()
    else:
        st.stop()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Insights Dashboard", 
    "🔍 Priority Analysis", 
    "📝 Sample Reviews",
    "💡 Recommendations"
])

# Tab 1: Insights Dashboard
with tab1:
    st.header("📈 Customer Insights Dashboard")
    
    if st.button("🔄 Run Analysis", type="primary"):
        with st.spinner(f"Analyzing {num_reviews} reviews... This takes 1-2 minutes..."):
            try:
                # Extract insights
                insights_df, sample_reviews = extract_insights(reviews_df, num_reviews)
                priority_results, sorted_aspects = calculate_priorities(insights_df, sample_reviews)
                
                # Store in session state
                st.session_state['insights_df'] = insights_df
                st.session_state['priority_results'] = priority_results
                st.session_state['sorted_aspects'] = sorted_aspects
                st.session_state['sample_reviews'] = sample_reviews
                st.session_state['analysis_done'] = True
                
                st.success(f"✅ Analysis complete! Extracted {len(insights_df)} insights")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.info("Try reducing the number of reviews or check your data format")
    
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        insights_df = st.session_state['insights_df']
        sample_reviews = st.session_state['sample_reviews']
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Reviews Analyzed", len(sample_reviews))
        with col2:
            st.metric("Insights Extracted", len(insights_df))
        with col3:
            st.metric("Aspects Tracked", len(ASPECTS))
        with col4:
            avg = len(insights_df) / len(sample_reviews) if len(sample_reviews) > 0 else 0
            st.metric("Insights per Review", f"{avg:.2f}")
        
        # Priority chart
        if sorted_aspects:
            st.subheader("📊 Priority Scores by Aspect")
            
            aspects = [a for a, _ in sorted_aspects]
            scores = [s['priority_score'] for _, s in sorted_aspects]
            
            colors = ['#ff4444' if i < 2 else '#ffaa44' if i < 4 else '#44cc44' 
                     for i in range(len(aspects))]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=aspects,
                    y=scores,
                    text=[f'{s:.3f}' for s in scores],
                    textposition='auto',
                    marker_color=colors
                )
            ])
            
            fig.update_layout(
                title="Product Improvement Priorities",
                xaxis_title="Product Aspect",
                yaxis_title="Priority Score (0-1)",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: Priority Analysis
with tab2:
    st.header("🔍 Detailed Priority Analysis")
    
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        
        for i, (aspect, scores) in enumerate(sorted_aspects):
            if i < 2:
                priority = "🔴 CRITICAL"
            elif i < 4:
                priority = "🟡 MEDIUM"
            else:
                priority = "🟢 LOW"
            
            with st.expander(f"{priority} - {aspect.upper()} (Score: {scores['priority_score']:.3f})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Mention Frequency", f"{scores['frequency']*100:.1f}%")
                    st.metric("Total Mentions", scores['total_mentions'])
                with col2:
                    st.metric("Negativity", f"{scores['negativity_strength']:.3f}")
                    st.metric("Avg Rating", f"{scores['avg_rating']:.1f}/5.0")
    else:
        st.info("👈 Run analysis first in the Insights Dashboard tab")

# Tab 3: Sample Reviews
with tab3:
    st.header("📝 Sample Customer Reviews")
    
    if st.session_state.get('analysis_done', False):
        insights_df = st.session_state['insights_df']
        
        col1, col2 = st.columns(2)
        with col1:
            aspect_filter = st.selectbox("Filter by aspect", ["All"] + list(ASPECTS.keys()))
        with col2:
            sentiment_filter = st.selectbox("Filter by sentiment", 
                ["All", "Positive", "Negative", "Neutral"])
        
        filtered_df = insights_df.copy()
        if aspect_filter != "All":
            filtered_df = filtered_df[filtered_df['aspect'] == aspect_filter]
        if sentiment_filter == "Positive":
            filtered_df = filtered_df[filtered_df['sentiment'] > 0.2]
        elif sentiment_filter == "Negative":
            filtered_df = filtered_df[filtered_df['sentiment'] < -0.2]
        elif sentiment_filter == "Neutral":
            filtered_df = filtered_df[(filtered_df['sentiment'] >= -0.2) & (filtered_df['sentiment'] <= 0.2)]
        
        st.write(f"Showing {len(filtered_df)} insights")
        
        for idx, row in filtered_df.head(20).iterrows():
            emoji = "🟢" if row['sentiment'] > 0.2 else "🔴" if row['sentiment'] < -0.2 else "🟡"
            st.markdown(f"""
            **{emoji} {row['aspect']}** | Score: `{row['sentiment']:.2f}` | Rating: `{row['rating']}/5`
            > {row['review_snippet']}...
            ---
            """)
    else:
        st.info("👈 Run analysis first")

# Tab 4: Recommendations
with tab4:
    st.header("💡 Actionable Recommendations")
    
    if st.session_state.get('analysis_done', False):
        sorted_aspects = st.session_state['sorted_aspects']
        insights_df = st.session_state['insights_df']
        
        recs_map = {
            'battery': ["Optimize power management", "Add fast charging", "Monitor battery health"],
            'performance': ["Reduce background processes", "Optimize app launch", "Investigate memory leaks"],
            'screen': ["Review display quality", "Improve brightness", "Add screen protector"],
            'connectivity': ["Improve Bluetooth pairing", "Update WiFi drivers", "Add troubleshooting guide"],
            'software': ["Simplify interface", "Add tutorial", "Reduce update frequency"],
            'build_quality': ["Review materials", "Improve QC", "Add drop protection"],
            'sound': ["Enhance speakers", "Add equalizer", "Improve noise cancellation"],
            'value': ["Review pricing", "Add bundles", "Extend warranty"]
        }
        
        st.subheader("🎯 Immediate Actions (Next Sprint)")
        
        for i, (aspect, scores) in enumerate(sorted_aspects[:3]):
            st.markdown(f"### {i+1}. Improve {aspect.upper()}")
            st.markdown(f"**Priority Score:** {scores['priority_score']:.3f}")
            st.markdown(f"**Customer Impact:** {scores['frequency']*100:.1f}% of reviews")
            
            # Show sample quote
            quotes = insights_df[
                (insights_df['aspect'] == aspect) & 
                (insights_df['sentiment'] < -0.2)
            ]['review_snippet'].head(1)
            
            if len(quotes) > 0:
                st.markdown(f"**Customer says:** \"{quotes.iloc[0]}...\"")
            
            st.markdown("**Recommended:**")
            for rec in recs_map.get(aspect, ["Investigate issue"]):
                st.markdown(f"- {rec}")
            st.markdown("---")
    else:
        st.info("👈 Run analysis first")

st.markdown("---")
st.markdown("Built with Streamlit | NLP Insight Engine")