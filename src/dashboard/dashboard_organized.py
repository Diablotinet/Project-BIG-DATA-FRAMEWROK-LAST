#!/usr/bin/env python3
"""
🎨 AFP REAL-TIME DASHBOARD - ORGANIZED BY SOURCE TYPES
Displays comparisons in three clear categories:
1. AFP + Reddit + GDELT (multi-source)
2. AFP + Reddit only
3. AFP + GDELT only
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import json
import time

# Page configuration
st.set_page_config(
    page_title="AFP Real-Time Analytics",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .category-header-multi {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .category-header-reddit {
        background: linear-gradient(90deg, #FF6B6B, #FF8E72);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .category-header-gdelt {
        background: linear-gradient(90deg, #4ECDC4, #45B7D1);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        font-size: 18px;
        font-weight: bold;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FF6B6B;
    }
    .alert-high {
        background: #ff4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-medium {
        background: #ffaa00;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-low {
        background: #44ff44;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .source-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 5px;
        margin: 2px;
        font-weight: bold;
        color: white;
    }
    .badge-reddit {
        background: #FF6B6B;
    }
    .badge-gdelt {
        background: #4ECDC4;
    }
    .badge-afp {
        background: #FFB84D;
    }
</style>
""", unsafe_allow_html=True)

class AFPDashboardOrganized:
    """Organized AFP comparison dashboard by source types"""
    
    def __init__(self):
        self.db_path = "/app/data/afp_realtime_analysis.db"
        
    def get_connection(self):
        """Get database connection with timeout and read-only mode"""
        conn = sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True, timeout=10.0)
        return conn
    
    def get_comparisons(self, limit=100):
        """Get comparison results grouped by AFP article"""
        conn = self.get_connection()
        
        query = """
            SELECT id, afp_id, source_type, source_id, timestamp,
                   similarity_score, deformation_score, objectivity_score,
                   sentiment_diff, key_differences, bias_type,
                   distorted_facts, emotional_manipulation, ai_explanation
            FROM comparisons
            ORDER BY timestamp DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        # Parse source_id JSON
        if not df.empty:
            df['source_data'] = df['source_id'].apply(self._parse_json)
        
        return df
    
    def _parse_json(self, json_str):
        """Safely parse JSON from source_id"""
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            return json_str
        except:
            return {}
    
    def get_statistics(self):
        """Get overall statistics"""
        conn = self.get_connection()
        
        try:
            c = conn.cursor()
            
            # Total comparisons by source
            c.execute("SELECT COUNT(*) FROM comparisons")
            total = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM comparisons WHERE source_type = 'Reddit'")
            reddit_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM comparisons WHERE source_type = 'GDELT'")
            gdelt_count = c.fetchone()[0]
            
            # Averages
            c.execute("SELECT AVG(similarity_score) FROM comparisons")
            avg_similarity = c.fetchone()[0] or 0
            
            c.execute("SELECT AVG(deformation_score) FROM comparisons")
            avg_deformation = c.fetchone()[0] or 0
            
            # Count multi-source articles
            c.execute("""
                SELECT COUNT(*) FROM (
                    SELECT afp_id FROM comparisons 
                    GROUP BY afp_id 
                    HAVING COUNT(DISTINCT source_type) > 1
                )
            """)
            multi_source_count = c.fetchone()[0]
            
            conn.close()
            
            return {
                'total_comparisons': total,
                'reddit_comparisons': reddit_count,
                'gdelt_comparisons': gdelt_count,
                'avg_similarity': avg_similarity,
                'avg_deformation': avg_deformation,
                'multi_source_articles': multi_source_count
            }
        except Exception as e:
            conn.close()
            return {
                'total_comparisons': 0,
                'reddit_comparisons': 0,
                'gdelt_comparisons': 0,
                'avg_similarity': 0,
                'avg_deformation': 0,
                'multi_source_articles': 0
            }
    
    def organize_comparisons(self, comparisons):
        """Organize comparisons into three categories"""
        if comparisons.empty:
            return [], [], []
        
        # Group by AFP ID to find multi-source matches
        grouped = comparisons.groupby('afp_id')
        
        multi_source = []
        reddit_only = []
        gdelt_only = []
        
        for afp_id, group in grouped:
            sources = group['source_type'].unique()
            
            if len(sources) > 1:
                # Multi-source (has both Reddit and GDELT)
                multi_source.append(group)
            elif sources[0] == 'Reddit':
                reddit_only.append(group.iloc[0])
            elif sources[0] == 'GDELT':
                gdelt_only.append(group.iloc[0])
        
        return multi_source, reddit_only, gdelt_only
    
    def display_comparison(self, row, show_full=False, key_suffix=""):
        """Display a single comparison result"""
        source_data = row.get('source_data', {})
        
        # Header with source badge and similarity
        similarity_color = "🟢" if row['similarity_score'] > 0.7 else "🟡" if row['similarity_score'] > 0.4 else "🔴"
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{source_data.get('title', 'N/A')[:100]}**")
        with col2:
            st.write(f"{similarity_color} **{row['similarity_score']:.1%}** similarity")
        with col3:
            deform_indicator = "🔴" if row['deformation_score'] > 0.7 else "🟡" if row['deformation_score'] > 0.3 else "🟢"
            st.write(f"{deform_indicator} {row['deformation_score']:.1%} deformation")
        
        # Details
        if show_full:
            st.markdown("---")
            
            # Source info
            st.markdown("#### 📰 Source Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Source Type:** {row['source_type']}")
            with col2:
                st.write(f"**Timestamp:** {row['timestamp']}")
            with col3:
                st.write(f"**Message ID:** {source_data.get('message_id', 'N/A')}")
            
            # Source-specific metadata
            if row['source_type'] == 'Reddit':
                st.markdown("##### 💬 Reddit Metadata")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Subreddit:** r/{source_data.get('subreddit', 'N/A')}")
                with col2:
                    st.write(f"**Author:** {source_data.get('author', 'N/A')}")
                with col3:
                    st.write(f"**Score:** {source_data.get('score', 0)}")
                with col4:
                    st.write(f"**Comments:** {source_data.get('num_comments', 0)}")
            
            elif row['source_type'] == 'GDELT':
                st.markdown("##### 🌍 GDELT Event Metadata")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Source:** {source_data.get('source_name', 'N/A')}")
                with col2:
                    st.write(f"**Tone:** {source_data.get('tone', 'N/A')}")
                with col3:
                    st.write(f"**Location:** {source_data.get('location', 'N/A')}")
            
            # Full content
            st.markdown("#### 📄 Full Content")
            content = source_data.get('content', 'N/A')
            st.text_area("Article Content", content, height=150, disabled=True, key=f"content_{key_suffix}")
            
            # Analysis scores
            st.markdown("#### 🔍 Analysis Scores")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Similarity", f"{row['similarity_score']:.1%}")
            with col2:
                st.metric("Objectivity", f"{row['objectivity_score']:.1%}")
            with col3:
                st.metric("Deformation", f"{row['deformation_score']:.1%}")
            with col4:
                st.metric("Sentiment Diff", f"{row['sentiment_diff']:.2f}")
            
            # AI Analysis
            if row['ai_explanation'] and row['ai_explanation'] != 'AI analysis not available - Gemini API key required':
                st.markdown("#### 🤖 AI Analysis")
                st.info(f"**Analysis:** {row['ai_explanation']}")
            elif row['bias_type'] != 'unknown':
                st.markdown("#### 🤖 ML Analysis Results")
                st.info(f"""
                **Bias Type:** {row['bias_type']}  
                **Distorted Facts:** {row['distorted_facts'] or 'None detected'}  
                **Emotional Manipulation:** {row['emotional_manipulation']}  
                **Key Differences:** {row['key_differences'] or 'Minimal differences'}
                """)
            else:
                st.markdown("#### 🤖 Analysis Status")
                st.warning("""
                ⚙️ **ML-Based Analysis Active**  
                TF-IDF vectorization, VADER sentiment analysis, and TextBlob objectivity scoring are being used.
                
                💡 **To Enable Gemini AI:**
                1. Add your API key to `.env` file: `GEMINI_API_KEY=your_key_here`
                2. Restart the consumer: `docker-compose restart spark-consumer`
                3. Model: `gemini-1.5-flash` (free, no credits needed)
                """)


def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📰 AFP Real-Time Comparison Analytics</h1>
        <h3>AI-Powered Information Propagation & Deformation Analysis</h3>
        <p>Organized by Source Type: Multi-Source | Reddit-Only | GDELT-Only</p>
    </div>
    """, unsafe_allow_html=True)
    
    dashboard = AFPDashboardOrganized()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Controls")
        
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 1, 30, 5)
            time.sleep(refresh_interval)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Comparison Limit")
        limit = st.slider("Show comparisons", 10, 500, 100, 10)
        
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.info("""
        **Status:** ✅ Active  
        **Database:** SQLite  
        **Processing:** Spark Streaming  
        **Analysis:** ML-based (TF-IDF + Sentiment)  
        **Gemini AI:** Disabled (set API key to enable)
        """)
    
    # Get statistics
    stats = dashboard.get_statistics()
    
    # Main metrics
    st.markdown("### 📊 Real-Time Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("📊 Total", stats['total_comparisons'], "comparisons")
    
    with col2:
        st.metric("💬 Reddit", stats['reddit_comparisons'], "sources")
    
    with col3:
        st.metric("🌍 GDELT", stats['gdelt_comparisons'], "sources")
    
    with col4:
        st.metric("🎯 Multi-Source", stats['multi_source_articles'], "articles")
    
    with col5:
        st.metric("🔗 Avg Similarity", f"{stats['avg_similarity']:.1%}", "match rate")
    
    with col6:
        st.metric("⚠️ Avg Deformation", f"{stats['avg_deformation']:.1%}", "change level")
    
    # Get comparisons
    comparisons = dashboard.get_comparisons(limit=limit)
    
    if comparisons.empty:
        st.warning("⏳ No comparisons found yet. The system is collecting data...")
        st.info("Data will appear here as the producer generates content and the consumer finds matches.")
    else:
        # Organize by category
        multi_source, reddit_only, gdelt_only = dashboard.organize_comparisons(comparisons)
        
        # Category 1: Multi-Source (AFP + Reddit + GDELT)
        if multi_source:
            st.markdown("""
            <div class="category-header-multi">
            🔥 MULTI-SOURCE MATCHES (AFP + Reddit + GDELT)
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**{len(multi_source)} AFP articles found on multiple sources - Perfect for cross-analysis!**")
            
            for i, group in enumerate(multi_source[:10]):  # Show top 10
                source_counts = group['source_type'].value_counts()
                sources_str = ' + '.join([f"{count}x {src}" for src, count in source_counts.items()])
                
                # Aggregate similarity across sources
                avg_similarity = group['similarity_score'].mean()
                avg_deformation = group['deformation_score'].mean()
                
                with st.expander(
                    f"📌 {group.iloc[0]['source_data'].get('title', 'N/A')[:80]} "
                    f"({sources_str}) - {avg_similarity:.1%}",
                    expanded=(i == 0)
                ):
                    # Show each source comparison
                    for j, (_, row) in enumerate(group.iterrows()):
                        st.markdown(f"**{row['source_type']}** comparison:")
                        dashboard.display_comparison(row, show_full=True, key_suffix=f"multi_{i}_{j}")
                        st.markdown("---")
        
        # Category 2: Reddit + AFP only
        if reddit_only:
            st.markdown("""
            <div class="category-header-reddit">
            💬 REDDIT + AFP COMPARISONS ONLY
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**{len(reddit_only)} AFP articles matched with Reddit posts (no GDELT matches)**")
            
            for i, row in enumerate(pd.DataFrame(reddit_only).iterrows()):
                with st.expander(
                    f"📌 {row[1]['source_data'].get('title', 'N/A')[:80]} - {row[1]['similarity_score']:.1%}",
                    expanded=(i == 0)
                ):
                    dashboard.display_comparison(row[1], show_full=True, key_suffix=f"reddit_{i}")
        
        # Category 3: GDELT + AFP only
        if gdelt_only:
            st.markdown("""
            <div class="category-header-gdelt">
            🌍 GDELT + AFP COMPARISONS ONLY
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**{len(gdelt_only)} AFP articles matched with GDELT events (no Reddit matches)**")
            
            for i, row in enumerate(pd.DataFrame(gdelt_only).iterrows()):
                with st.expander(
                    f"📌 {row[1]['source_data'].get('title', 'N/A')[:80]} - {row[1]['similarity_score']:.1%}",
                    expanded=(i == 0)
                ):
                    dashboard.display_comparison(row[1], show_full=True, key_suffix=f"gdelt_{i}")
        
        # Analytics charts
        st.markdown("### 📈 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Similarity distribution by source
            if not comparisons.empty:
                fig = px.box(
                    comparisons,
                    x='source_type',
                    y='similarity_score',
                    title="Similarity Score Distribution by Source",
                    color='source_type',
                    points='all'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Deformation distribution by source
            if not comparisons.empty:
                fig = px.box(
                    comparisons,
                    x='source_type',
                    y='deformation_score',
                    title="Deformation Score Distribution by Source",
                    color='source_type',
                    points='all'
                )
                st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
