import streamlit as st
import asyncio
from langchain_client import LangchainMCPClient
import logging
from streamlit.runtime.scriptrunner import add_script_run_ctx
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()
import sys
import time
from datetime import datetime

llm = ChatGroq(model="llama-3.1-8b-instant",
               temperature=0.5,
               max_tokens=2000,
               )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = LangchainMCPClient()
        # Initialize the agent
        asyncio.run(st.session_state.agent.initialize_agent())
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'rag_results' not in st.session_state:
        st.session_state.rag_results = None
    if 'chunks' not in st.session_state:
        st.session_state.chunks = None
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

async def process_query(query: str):
    """Process the search query"""
    try:
        with status_placeholder:
            with st.spinner("🔄 Initializing intelligent search..."):
                if not hasattr(st.session_state.agent, 'tools'):
                    await st.session_state.agent.initialize_agent()
                
            with st.spinner("🔍 Analyzing and processing results..."):
                response = await st.session_state.agent.process_message(query)
                print(f"Response from MCP server: {response}")
                print(f"Type of response: {type(response)}")
                
                # Convert string response to dictionary if needed
                if isinstance(response, str):
                    try:
                        import json
                        response = json.loads(response)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        return "Error parsing response", "Error during analysis", []
                
                # Handle dictionary response from MCP server
                if isinstance(response, dict):
                    search_results = response.get("search_results", "No search results")
                    rag_analysis = response.get("rag_analysis", [])
                    
                    # Enhanced RAG Analysis formatting
                    analysis_text = f"# Analysis: {query}\n\n"
                    
                    if rag_analysis:
                        key_points = []
                        main_findings = []
                        
                        for item in rag_analysis:
                            content = item.get("content", "")
                            source = item.get("metadata", {}).get("source", "")
                            
                            # Extract meaningful sentences
                            sentences = [s.strip() for s in content.split('.') 
                                       if len(s.strip()) > 20 and 
                                       not s.strip().startswith(('Sign', 'Open', 'Listen'))]
                            
                            for sentence in sentences[:3]:  # Take top 3 meaningful sentences
                                if sentence:
                                    key_points.append({
                                        "point": sentence,
                                        "source": source
                                    })
                        
                        # Group similar points and create a coherent response
                        analysis_text += "## Key Information\n\n"
                        
                        # Format key points into a narrative
                        for idx, point in enumerate(key_points, 1):
                            analysis_text += f"{idx}. {point['point']}\n"
                            analysis_text += f"   *[Source]({point['source']})*\n\n"
                        
                        # Add a concise summary
                        analysis_text += "\n## Summary\n"
                        analysis_text += "Based on the analyzed sources:\n"
                        analysis_text += "\n".join([f"- {point['point'].split(',')[0]}." for point in key_points[:3]])
                        
                    else:
                        analysis_text += "\n⚠️ No detailed analysis available for this query.\n"
                        analysis_text += "Please try refining your search terms.\n"
                    
                    return search_results, analysis_text, rag_analysis
                    
                return "No results available", "No analysis available", []
                
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return f"An error occurred: {str(e)}", "Error during analysis", []

# Page configuration with modern theme
st.set_page_config(
    page_title="IntelliSearch RAG",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main > div {
        padding-top: 2rem;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom header styling */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: rgba(255,255,255,0.9);
        font-weight: 400;
        margin-bottom: 0;
    }
    
    /* Search container */
    .search-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Custom input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e1e5e9;
        padding: 1rem;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Card components */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .feature-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    /* Result containers */
    .result-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* Progress bar */
    .stProgress .css-1cpxqw2 {
        background-color: #667eea;
        border-radius: 10px;
    }
    
    /* Expandable sections */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        font-weight: 500;
        color: #334155;
    }
    
    .streamlit-expanderContent {
        background: white;
        border-radius: 0 0 10px 10px;
        border: 1px solid #e2e8f0;
        border-top: none;
    }
    
    /* Status messages */
    .status-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 500;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Search history */
    .search-history-item {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #667eea;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .search-history-item:hover {
        background: #e2e8f0;
        transform: translateX(5px);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Hero Section
st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">🚀 IntelliSearch RAG</h1>
    <p class="hero-subtitle">Advanced AI-Powered Search with Retrieval Augmented Generation</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with enhanced design
with st.sidebar:
    st.markdown("""
    <div class="info-card">
        <h2 style="color:#667eea; margin-bottom:1rem; font-size:1.5rem;">✨ About IntelliSearch</h2>
        <p style="color:#64748b; line-height:1.6;">
            Experience next-generation search powered by cutting-edge AI technologies:
        </p>
        <div style="margin-top:1rem;">
            <span class="feature-badge">🧠 RAG Technology</span>
            <span class="feature-badge">🔗 MCP Protocol</span>
            <span class="feature-badge">🌐 Web Integration</span>
            <span class="feature-badge">⚡ LangChain</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Searches Today</div>
        </div>
        """.format(len(st.session_state.search_history)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">⚡</div>
            <div class="metric-label">AI Powered</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Search History
    if st.session_state.search_history:
        st.markdown("""
        <div class="info-card">
            <h3 style="color:#667eea; margin-bottom:1rem;">📝 Recent Searches</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
            if st.button(f"🔍 {search[:30]}...", key=f"history_{i}", help=search):
                st.session_state.selected_query = search
                st.experimental_rerun()
    
    st.markdown("---")
    
    # Enhanced tips section
    st.markdown("""
    <div class="info-card">
        <h3 style="color:#667eea; margin-bottom:1rem;">💡 Pro Tips</h3>
        <div style="color:#64748b; line-height:1.6;">
            <p><strong>🎯 Be Specific:</strong> Use detailed queries for better results</p>
            <p><strong>⏱️ Processing Time:</strong> Complex queries may take a moment</p>
            <p><strong>📊 Multiple Views:</strong> Explore all tabs for comprehensive insights</p>
            <p><strong>🔄 Iterate:</strong> Refine your search based on initial results</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("### 🛠️ Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", help="Clear all data and start fresh"):
            for key in ['search_results', 'rag_results', 'chunks', 'search_history']:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()
    
    with col2:
        if st.button("🚪 Quit", help="Exit the application"):
            logger.info("User requested to quit the application")
            st.success("👋 Thanks for using IntelliSearch!")
            if 'agent' in st.session_state:
                del st.session_state.agent
            time.sleep(2)
            sys.exit(0)

# Main search interface
st.markdown("""
<div class="search-container">
    <h2 style="color:#334155; margin-bottom:1rem; font-size:1.5rem;">🔍 Enter Your Search Query</h2>
</div>
""", unsafe_allow_html=True)

# Handle pre-selected query from history
query = st.session_state.get('selected_query', '')
if 'selected_query' in st.session_state:
    del st.session_state.selected_query

# Search input with enhanced styling
query = st.text_input(
    "",
    value=query,
    placeholder="🌟 Ask anything... e.g., 'Latest developments in AI', 'Climate change solutions', 'Tech industry trends'",
    help="Enter your search query here. Be as specific as possible for better results."
)

# Create placeholder for status messages
status_placeholder = st.empty()

# Process query when entered
if query:
    # Add to search history
    if query not in st.session_state.search_history:
        st.session_state.search_history.append(query)
        if len(st.session_state.search_history) > 10:
            st.session_state.search_history.pop(0)
    
    # Search execution section
    st.markdown(f"""
    <div class="result-container">
        <h3 style="color:#667eea; margin-bottom:1rem;">🔎 Searching: "{query}"</h3>
        <p style="color:#64748b;">Processing your query with advanced AI analysis...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress tracking
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        status_text.markdown('<div class="status-message">🚀 Initializing AI search engine...</div>', unsafe_allow_html=True)
        progress_bar.progress(25)
        
        # Process the query
        search_results, analysis_text, chunks = asyncio.run(process_query(query))
        logger.info(f"Received response from agent")
        
        progress_bar.progress(75)
        status_text.markdown('<div class="status-message">📊 Generating insights and analysis...</div>', unsafe_allow_html=True)
        
        # Success message
        progress_bar.progress(100)
        status_text.markdown('<div class="status-message">✅ Search completed successfully!</div>', unsafe_allow_html=True)
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        # Enhanced results section
        st.markdown("""
        <div style="margin-top:2rem;">
            <h2 style="color:#334155; margin-bottom:1.5rem; font-size:2rem;">📊 Search Results & Analysis</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced tabs with icons and descriptions
        tab1, tab2, tab3, tab4 = st.tabs([
            "🌐 Web Results", 
            "🧠 AI Analysis", 
            "📑 Source Documents", 
            "📈 Insights"
        ])
        
        try:
            # Tab 1: Search Results
            with tab1:
                st.markdown("""
                <div class="result-container">
                    <h3 style="color:#667eea;">🌐 Raw Search Results</h3>
                    <p style="color:#64748b; margin-bottom:1rem;">Direct results from web search engines</p>
                </div>
                """, unsafe_allow_html=True)
                
                if search_results and search_results != "No results available":
                    if search_results.startswith("Search Results:"):
                        search_results = search_results.replace("Search Results:", "", 1)
                    
                    st.markdown(f"""
                    <div style="background:white; padding:2rem; border-radius:15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
                        {search_results.strip()}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("🚫 No search results available for this query")
                
                logger.info("Displayed search results")
            
            # Tab 2: AI Analysis
            with tab2:
                st.markdown("""
                <div class="result-container">
                    <h3 style="color:#667eea;">🧠 AI-Powered Analysis</h3>
                    <p style="color:#64748b; margin-bottom:1rem;">Enhanced insights generated by our RAG system</p>
                </div>
                """, unsafe_allow_html=True)
                
                if analysis_text and analysis_text != "No analysis available":
                    # Action buttons
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        st.download_button(
                            label="📥 Download Analysis",
                            data=analysis_text,
                            file_name=f"intellisearch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            help="Download the complete analysis as a Markdown file"
                        )
                    with col2:
                        if st.button("🔄 Regenerate", help="Generate a new analysis"):
                            st.experimental_rerun()
                    
                    # Generate enhanced analysis
                    prompt = f"""Based on the ANALYSIS provided below, please provide a clear, detailed, and well-structured response for the QUESTION asked.
                    
                    QUESTION: {query}
                    ANALYSIS: {analysis_text}
                    
                    Please:
                    - Stick strictly to the ANALYSIS provided
                    - Do not make up your own answers
                    - If you don't know the answer, say "I don't know"
                    - Provide the answer in MARKDOWN format with proper headings
                    - Include key insights and takeaways
                    - Make it easy to read and understand
                    """
                    
                    with st.spinner("🤖 Generating AI analysis..."):
                        analysis_response = llm.invoke(prompt)
                    
                    st.markdown(f"""
                    <div style="background:white; padding:2rem; border-radius:15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); border-left: 4px solid #667eea;">
                        {analysis_response.content}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Feedback section
                    st.markdown("---")
                    st.markdown("### 💬 Feedback")
                    st.markdown("Was this analysis helpful? Your feedback helps us improve!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("👍 Excellent"):
                            st.success("Thank you for your feedback!")
                    with col2:
                        if st.button("😊 Good"):
                            st.success("Thanks! We'll keep improving!")
                    with col3:
                        if st.button("😐 Okay"):
                            st.info("We'll work on making it better!")
                    with col4:
                        if st.button("👎 Poor"):
                            st.info("Sorry about that. We'll improve!")
                    
                else:
                    st.warning("🚫 No AI analysis available for this query")
            
            # Tab 3: Document Chunks
            with tab3:
                st.markdown("""
                <div class="result-container">
                    <h3 style="color:#667eea;">📑 Source Documents</h3>
                    <p style="color:#64748b; margin-bottom:1rem;">Individual document chunks analyzed by the system</p>
                </div>
                """, unsafe_allow_html=True)
                
                if chunks:
                    st.info(f"📊 Found {len(chunks)} document chunks for analysis")
                    
                    for i, chunk in enumerate(chunks, 1):
                        source = chunk.get("metadata", {}).get("source", "Unknown Source")
                        content_preview = chunk.get("content", "No content available")[:100] + "..."
                        
                        with st.expander(
                            f"📄 Document {i}: {source}",
                            expanded=False
                        ):
                            st.markdown(f"""
                            <div style="background:#f8fafc; padding:1rem; border-radius:8px; margin-bottom:1rem;">
                                <strong>Source:</strong> {source}<br>
                                <strong>Content Length:</strong> {len(chunk.get("content", ""))} characters
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(chunk.get("content", "No content available"))
                    
                    logger.info(f"Displayed {len(chunks)} document chunks")
                else:
                    st.warning("📭 No document chunks available for this query")
            
            # Tab 4: Insights Dashboard
            with tab4:
                st.markdown("""
                <div class="result-container">
                    <h3 style="color:#667eea;">📈 Search Insights</h3>
                    <p style="color:#64748b; margin-bottom:1rem;">Analytics and metadata about your search</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Sources Found</div>
                    </div>
                    """.format(len(chunks) if chunks else 0), unsafe_allow_html=True)
                
                with col2:
                    total_chars = sum(len(chunk.get("content", "")) for chunk in (chunks or []))
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Characters Analyzed</div>
                    </div>
                    """.format(f"{total_chars:,}"), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Query Length</div>
                    </div>
                    """.format(len(query.split())), unsafe_allow_html=True)
                
                with col4:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">⚡</div>
                        <div class="metric-label">AI Enhanced</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Query analysis
                st.markdown("### 🔍 Query Analysis")
                if chunks:
                    sources = [chunk.get("metadata", {}).get("source", "Unknown") for chunk in chunks]
                    unique_sources = list(set(sources))
                    
                    st.markdown(f"""
                    <div style="background:white; padding:1.5rem; border-radius:12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                        <p><strong>🎯 Search Query:</strong> {query}</p>
                        <p><strong>📊 Unique Sources:</strong> {len(unique_sources)}</p>
                        <p><strong>⏰ Processed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>🔍 Search Type:</strong> Web + RAG Analysis</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if unique_sources:
                        st.markdown("### 📚 Sources Overview")
                        for i, source in enumerate(unique_sources[:5], 1):
                            st.markdown(f"{i}. {source}")
                else:
                    st.info("🔍 No detailed insights available for this search.")
                    
        except Exception as e:
            st.error(f"💥 An error occurred while displaying results: {str(e)}")
            logger.error(f"Error in display: {str(e)}", exc_info=True)
        
    except Exception as e:
        st.error(f"🚨 An error occurred while processing the query: {str(e)}")
        logger.error(f"Error in query processing: {str(e)}", exc_info=True)
    finally:
        # Clean up progress indicators
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:2rem; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-radius:15px; margin-top:3rem;">
    <h3 style="margin-bottom:1rem;">🚀 Powered by Advanced AI Technologies</h3>
    <div>
        <span class="feature-badge" style="background:rgba(255,255,255,0.2);">Streamlit</span>
        <span class="feature-badge" style="background:rgba(255,255,255,0.2);">LangChain</span>
        <span class="feature-badge" style="background:rgba(255,255,255,0.2);">MCP Protocol</span>
        <span class="feature-badge" style="background:rgba(255,255,255,0.2);">RAG Technology</span>
    </div>
    <p style="margin-top:1rem; opacity:0.9;">Built for the future of intelligent search and knowledge discovery</p>
</div>
""", unsafe_allow_html=True)

# Session cleanup function
def cleanup_session():
    """Clean up session resources"""
    if 'agent' in st.session_state:
        logger.info("Cleaning up session resources")
        del st.session_state.agent

# Register the cleanup function
st.session_state["_cleanup"] = cleanup_session