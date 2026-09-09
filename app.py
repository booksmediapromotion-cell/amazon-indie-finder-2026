"""Main Streamlit Application - Fixed for Streamlit Cloud"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
import sys
import os

# Add current directory to path (fixes import issues on Streamlit Cloud)
sys.path.insert(0, os.path.dirname(__file__))

# Now import our modules
from database import DatabaseManager
import config

st.set_page_config(page_title="Amazon Indie Author Finder 2026", page_icon="📚", layout="wide")

# Custom CSS
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
.main-header { font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #6366f1, #8b5cf6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stMetric { background: rgba(99, 102, 241, 0.1); border-radius: 12px; padding: 1rem; border: 1px solid rgba(99, 102, 241, 0.2); }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📚 Navigation")
    page = st.radio("Go to", ["🏠 Dashboard", "🔍 Discover", "📅 History"], label_visibility="collapsed")
    st.divider()

    try:
        db = DatabaseManager()
        st.metric("Total Books", db.count_books())
        st.metric("Total Authors", db.count_authors())
    except:
        st.info("Database not initialized yet")

# Main content
if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">📚 Amazon Indie Author Finder 2026</h1>', unsafe_allow_html=True)
    st.markdown("Discover newly published independent authors and books in the United States.")

    try:
        db = DatabaseManager()

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("📚 Total Books", f"{db.count_books():,}")
        with col2: st.metric("✍️ Total Authors", f"{db.count_authors():,}")
        with col3: st.metric("🆕 New Today", f"{db.get_new_today():,}")
        with col4: st.metric("📅 New This Month", f"{db.get_new_this_month():,}")

        st.divider()

        # Filters
        with st.sidebar:
            st.markdown("### 🔎 Filters")
            search_title = st.text_input("📖 Book Title")
            genre_options = ["All Genres", "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Horror", "Young Adult Fiction", "Nonfiction", "Self-Help"]
            genre_filter = st.selectbox("📚 Genre", genre_options)
            state_filter = st.selectbox("📍 USA State", config.USA_STATES)
            min_score = st.slider("Minimum Indie Score", 0, 100, 0)
            apply = st.button("Apply Filters", type="primary", use_container_width=True)

        # Get books
        filters = {}
        if search_title: filters['search_title'] = search_title
        if genre_filter and genre_filter != "All Genres": filters['genre'] = genre_filter
        if state_filter and state_filter != "All USA": filters['state'] = state_filter
        if min_score > 0: filters['min_indie_score'] = min_score

        books = db.get_books(filters, limit=50)

        st.markdown(f"### 📚 Discovered Books ({len(books)} results)")

        if not books:
            st.info("No books found. Database is empty. Add sample data or integrate with discovery sources.")
        else:
            for book in books:
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.markdown("📖")
                    with col2:
                        st.markdown(f"### {book.title}")
                        st.markdown(f"**Author:** {book.author.name}")
                        st.markdown(f"**Genre:** {book.genre or 'N/A'}")
                        st.markdown(f"**Published:** {book.publication_date.strftime('%B %d, %Y')}")
                        if book.author.state:
                            st.markdown(f"📍 {book.author.state}, USA")
                        score = book.indie_score
                        emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
                        st.markdown(f"{emoji} Score: {score}")
                        if book.amazon_url:
                            st.link_button("🛒 View on Amazon", book.amazon_url)
                    st.divider()

        # Export
        st.divider()
        st.markdown("### 📤 Export")
        if st.button("📄 Export CSV"):
            data = db.export_books(filters)
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name=f"indie_books_{date.today()}.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        st.info("The database needs to be initialized. This is normal for first-time setup.")

elif page == "🔍 Discover":
    st.markdown("### 🔍 Run Discovery")
    st.info("Daily limit: 100 books | Only 2026+ publications")
    if st.button("🚀 Run Discovery Now", type="primary"):
        st.success("Discovery feature coming soon! (Requires API integration)")

elif page == "📅 History":
    st.markdown("### 📅 Discovery History")
    try:
        db = DatabaseManager()
        history = db.get_discovery_history()
        if history:
            data = [{'Date': h.discovery_date.isoformat(), 'Books': h.books_found, 'Authors': h.new_authors_found, 'Status': h.status} for h in history]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No discovery history yet")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 1rem;">
    <p>Amazon Indie Author Finder 2026 | Version 1.0.0</p>
</div>
""", unsafe_allow_html=True)
