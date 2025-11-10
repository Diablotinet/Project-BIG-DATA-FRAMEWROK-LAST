#!/usr/bin/env python3
"""
🎨 AFP REAL-TIME DASHBOARD - COMPLETE SYSTEM
Real-time visualization of AFP vs Reddit vs GDELT comparisons
AI-powered deformation and objectivity analysis
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
</style>
""", unsafe_allow_html=True)

class AFPDashboard:
    """Real-time AFP comparison dashboard"""
    
    def __init__(self):
        self.db_path = "afp_realtime_analysis.db"
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_afp_articles(self, limit=20):
        """Get recent AFP articles"""
        conn = self.get_connection()
        query = """
            SELECT id, title, content, category, timestamp, reliability_score, keywords
            FROM afp_articles
            ORDER BY timestamp DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_comparisons(self, afp_id=None, limit=100):
        """Get comparison results"""
        conn = self.get_connection()
        
        if afp_id:
            query = """
                SELECT c.*, a.title as afp_title, a.category
                FROM comparisons c
                JOIN afp_articles a ON c.afp_id = a.id
                WHERE c.afp_id = ?
                ORDER BY c.timestamp DESC
                LIMIT ?
            """
            params = (afp_id, limit)
        else:
            query = """
                SELECT c.*, a.title as afp_title, a.category
                FROM comparisons c
                JOIN afp_articles a ON c.afp_id = a.id
                ORDER BY c.timestamp DESC
                LIMIT ?
            """
            params = (limit,)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_realtime_metrics(self, hours=1):
        """Get real-time metrics"""
        conn = self.get_connection()
        query = """
            SELECT *
            FROM realtime_metrics
            WHERE timestamp > datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        """.format(hours)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_statistics(self):
        """Get overall statistics"""
        conn = self.get_connection()
        
        stats = {}
        
        # Total counts
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM afp_articles")
        stats['total_afp'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons")
        stats['total_comparisons'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE source_type = 'Reddit'")
        stats['reddit_comparisons'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE source_type = 'GDELT'")
        stats['gdelt_comparisons'] = cursor.fetchone()[0]
        
        # Averages
        cursor.execute("""
            SELECT 
                AVG(similarity_score),
                AVG(deformation_score),
                AVG(objectivity_score),
                AVG(sentiment_diff)
            FROM comparisons
        """)
        result = cursor.fetchone()
        stats['avg_similarity'] = result[0] or 0
        stats['avg_deformation'] = result[1] or 0
        stats['avg_objectivity'] = result[2] or 0
        stats['avg_sentiment_diff'] = result[3] or 0
        
        conn.close()
        return stats

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📰 AFP Real-Time Comparison Analytics</h1>
        <h3>AI-Powered Information Propagation & Deformation Analysis</h3>
        <p>Comparing trusted AFP news with Reddit & GDELT to detect information deformation</p>
    </div>
    """, unsafe_allow_html=True)
    
    dashboard = AFPDashboard()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Controls")
        
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 1, 30, 5)
        
        st.markdown("---")
        st.markdown("### 📊 Filters")
        
        time_window = st.selectbox(
            "Time window",
            ["Last hour", "Last 6 hours", "Last 24 hours", "Last week"],
            index=0
        )
        
        show_source = st.multiselect(
            "Sources",
            ["Reddit", "GDELT"],
            default=["Reddit", "GDELT"]
        )
        
        deformation_threshold = st.slider(
            "Deformation alert threshold",
            0.0, 1.0, 0.7, 0.1
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.info("""
        **Database:** SQLite  
        **Processing:** Spark Streaming  
        **Analysis:** AI-powered TF-IDF + Sentiment  
        **Update:** Real-time (5s batches)
        """)
    
    # Get statistics
    stats = dashboard.get_statistics()
    
    # Main metrics
    st.markdown("### 📊 Real-Time Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📰 AFP Articles",
            stats['total_afp'],
            "Official source",
            help="Total AFP articles analyzed"
        )
    
    with col2:
        st.metric(
            "💬 Reddit Comparisons",
            stats['reddit_comparisons'],
            f"{stats['reddit_comparisons']/max(stats['total_afp'],1):.1f} per article",
            help="Reddit discussions matched to AFP articles"
        )
    
    with col3:
        st.metric(
            "🌍 GDELT Events",
            stats['gdelt_comparisons'],
            f"{stats['gdelt_comparisons']/max(stats['total_afp'],1):.1f} per article",
            help="GDELT events correlated with AFP"
        )
    
    with col4:
        deformation_color = "inverse" if stats['avg_deformation'] < 0.3 else "normal"
        st.metric(
            "⚠️ Avg Deformation",
            f"{stats['avg_deformation']:.1%}",
            "Lower is better",
            delta_color=deformation_color,
            help="Average information deformation score"
        )
    
    with col5:
        st.metric(
            "🎯 Avg Similarity",
            f"{stats['avg_similarity']:.1%}",
            "Higher is better",
            help="Average content similarity with AFP"
        )
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Live Comparisons",
        "📊 Analytics Dashboard",
        "📰 AFP Articles",
        "🚨 Deformation Alerts"
    ])
    
    with tab1:
        st.markdown("### 🔍 Latest Comparisons")
        
        comparisons = dashboard.get_comparisons(limit=50)
        
        if not comparisons.empty:
            # Filter by source
            if show_source:
                comparisons = comparisons[comparisons['source_type'].isin(show_source)]
            
            # Display recent comparisons
            for idx, row in comparisons.head(20).iterrows():
                with st.expander(
                    f"{'💬' if row['source_type'] == 'Reddit' else '🌍'} "
                    f"{row['afp_title'][:60]}... "
                    f"(Similarity: {row['similarity_score']:.1%}, "
                    f"Deformation: {row['deformation_score']:.1%})"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🎯 Analysis Metrics**")
                        st.metric("Similarity Score", f"{row['similarity_score']:.1%}")
                        st.metric("Deformation Score", f"{row['deformation_score']:.1%}")
                        st.metric("Objectivity Diff", f"{row['objectivity_score']:.1%}")
                        st.metric("Sentiment Difference", f"{row['sentiment_diff']:.3f}")
                    
                    with col2:
                        st.markdown("**📋 Details**")
                        st.write(f"**Source:** {row['source_type']}")
                        st.write(f"**AFP Article:** {row['afp_title']}")
                        st.write(f"**Category:** {row['category']}")
                        st.write(f"**Timestamp:** {row['timestamp']}")
                        
                        # Deformation alert
                        if row['deformation_score'] > deformation_threshold:
                            st.markdown("""
                            <div class="alert-high">
                                🚨 HIGH DEFORMATION DETECTED
                            </div>
                            """, unsafe_allow_html=True)
                        elif row['deformation_score'] > 0.4:
                            st.markdown("""
                            <div class="alert-medium">
                                ⚠️ MODERATE DEFORMATION
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="alert-low">
                                ✅ LOW DEFORMATION
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Key differences
                    if row['key_differences']:
                        try:
                            differences = json.loads(row['key_differences'])
                            if differences:
                                st.markdown("**🔍 Key Differences Detected:**")
                                for diff in differences:
                                    st.write(f"• {diff.get('description', 'N/A')}")
                        except:
                            pass
        else:
            st.info("⏳ Waiting for data... Make sure the producer and consumer are running.")
    
    with tab2:
        st.markdown("### 📊 Analytics Dashboard")
        
        if not comparisons.empty:
            # Similarity distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Similarity Score Distribution")
                fig_similarity = go.Figure()
                fig_similarity.add_trace(go.Histogram(
                    x=comparisons['similarity_score'],
                    nbinsx=20,
                    marker_color='#4ECDC4',
                    name='Similarity'
                ))
                fig_similarity.update_layout(
                    xaxis_title="Similarity Score",
                    yaxis_title="Count",
                    height=300
                )
                st.plotly_chart(fig_similarity, use_container_width=True)
            
            with col2:
                st.markdown("#### ⚠️ Deformation Score Distribution")
                fig_deformation = go.Figure()
                fig_deformation.add_trace(go.Histogram(
                    x=comparisons['deformation_score'],
                    nbinsx=20,
                    marker_color='#FF6B6B',
                    name='Deformation'
                ))
                fig_deformation.update_layout(
                    xaxis_title="Deformation Score",
                    yaxis_title="Count",
                    height=300
                )
                st.plotly_chart(fig_deformation, use_container_width=True)
            
            # By source comparison
            st.markdown("#### 📊 Comparison by Source")
            
            source_stats = comparisons.groupby('source_type').agg({
                'similarity_score': 'mean',
                'deformation_score': 'mean',
                'objectivity_score': 'mean',
                'sentiment_diff': 'mean'
            }).reset_index()
            
            fig_source = go.Figure()
            
            fig_source.add_trace(go.Bar(
                name='Similarity',
                x=source_stats['source_type'],
                y=source_stats['similarity_score'],
                marker_color='#4ECDC4'
            ))
            
            fig_source.add_trace(go.Bar(
                name='Deformation',
                x=source_stats['source_type'],
                y=source_stats['deformation_score'],
                marker_color='#FF6B6B'
            ))
            
            fig_source.add_trace(go.Bar(
                name='Objectivity Diff',
                x=source_stats['source_type'],
                y=source_stats['objectivity_score'],
                marker_color='#FFD93D'
            ))
            
            fig_source.update_layout(
                barmode='group',
                xaxis_title="Source",
                yaxis_title="Score",
                height=400
            )
            
            st.plotly_chart(fig_source, use_container_width=True)
            
            # Category analysis
            st.markdown("#### 📂 Analysis by Category")
            
            category_stats = comparisons.groupby('category').agg({
                'similarity_score': 'mean',
                'deformation_score': 'mean'
            }).reset_index()
            
            fig_category = px.scatter(
                category_stats,
                x='similarity_score',
                y='deformation_score',
                size=[20]*len(category_stats),
                color='category',
                text='category',
                title="Similarity vs Deformation by Category"
            )
            
            fig_category.update_traces(textposition='top center')
            st.plotly_chart(fig_category, use_container_width=True)
        
        else:
            st.info("⏳ No comparison data available yet")
    
    with tab3:
        st.markdown("### 📰 AFP Articles")
        
        afp_articles = dashboard.get_afp_articles(limit=10)
        
        if not afp_articles.empty:
            for idx, article in afp_articles.iterrows():
                with st.expander(f"📰 {article['title']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Content:** {article['content']}")
                        st.markdown(f"**Category:** {article['category']}")
                        st.markdown(f"**Published:** {article['timestamp']}")
                    
                    with col2:
                        st.metric("Reliability", f"{article['reliability_score']:.1%}")
                        st.markdown(f"**Keywords:** {article['keywords']}")
                        
                        # Get comparison count
                        comp_count = len(dashboard.get_comparisons(afp_id=article['id']))
                        st.metric("Comparisons", comp_count)
        else:
            st.info("⏳ No AFP articles yet")
    
    with tab4:
        st.markdown("### 🚨 Deformation Alerts")
        
        # High deformation comparisons
        if not comparisons.empty:
            high_deformation = comparisons[comparisons['deformation_score'] > deformation_threshold]
            
            st.markdown(f"**Found {len(high_deformation)} high deformation cases**")
            
            for idx, row in high_deformation.head(10).iterrows():
                st.markdown(f"""
                <div class="alert-high">
                    <strong>🚨 HIGH DEFORMATION ALERT</strong><br>
                    <strong>Article:</strong> {row['afp_title'][:60]}...<br>
                    <strong>Source:</strong> {row['source_type']}<br>
                    <strong>Deformation Score:</strong> {row['deformation_score']:.1%}<br>
                    <strong>Similarity:</strong> {row['similarity_score']:.1%}<br>
                    <strong>Time:</strong> {row['timestamp']}
                </div>
                <br>
                """, unsafe_allow_html=True)
        else:
            st.info("⏳ No alerts yet")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666;">
        <p><strong>🔄 Last updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>📊 Total comparisons:</strong> {stats['total_comparisons']} | 
           <strong>📰 AFP articles:</strong> {stats['total_afp']}</p>
        <p><em>Real-time AFP Information Propagation Analysis System</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
