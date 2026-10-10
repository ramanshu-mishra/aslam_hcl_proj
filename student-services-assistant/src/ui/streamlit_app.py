"""Streamlit UI for Student Services Assistant."""
import streamlit as st
import requests
import os
from datetime import date


# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")


st.set_page_config(
    page_title="Student Services Assistant",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI-Powered Student Services Assistant")
st.markdown("*Accurate, grounded, and explainable answers to student queries*")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    student_id = st.text_input(
        "Student ID (optional)",
        placeholder="S1001",
        help="Required for personal queries like attendance or eligibility"
    )
    
    as_of_date = st.date_input(
        "As of Date",
        value=date.today(),
        help="The date for which to evaluate rules and policies"
    )
    
    st.divider()
    
    st.header("Example Questions")
    st.markdown("""
    **Policy Questions:**
    - What is the minimum attendance required?
    - How do I apply for supplementary exam?
    
    **Personal Questions (need Student ID):**
    - What is my attendance in Data Structures?
    - Am I eligible for the exam?
    """)


# Main content
tab1, tab2, tab3 = st.tabs(["Ask Question", "Documents", "Audit Trail"])

with tab1:
    st.header("Ask a Question")
    
    question = st.text_area(
        "Your Question",
        placeholder="e.g., What is the minimum attendance required to appear for end-semester exams?",
        height=100
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("Ask", type="primary", use_container_width=True)
    
    if ask_button and question:
        with st.spinner("Processing your question..."):
            try:
                # Prepare request
                headers = {}
                if student_id:
                    headers["X-Student-Id"] = student_id
                
                payload = {
                    "question": question,
                    "as_of_date": str(as_of_date)
                }
                
                # Call API
                response = requests.post(
                    f"{API_URL}/ask",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display answer
                    st.success("Answer")
                    st.write(result["answer"])
                    
                    # Display metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Answer Type", result["answer_type"])
                    with col2:
                        st.metric("Trace ID", result["trace_id"])
                    with col3:
                        st.metric("Citations", len(result["citations"]))
                    
                    # Display citations
                    if result["citations"]:
                        st.subheader("Citations")
                        for cit in result["citations"]:
                            with st.expander(f"📄 {cit['title']}"):
                                st.write(f"**Document:** {cit['doc_id']}")
                                st.write(f"**Section:** {cit.get('section', 'N/A')}")
                                st.write(f"**Page:** {cit.get('page', 'N/A')}")
                                st.write(f"**Version:** {cit['version']}")
                                st.write(f"**Effective From:** {cit['effective_from']}")
                    
                    # Display tools invoked
                    if result["tools_invoked"]:
                        st.subheader("Tools Used")
                        for tool in result["tools_invoked"]:
                            with st.expander(f"🔧 {tool['tool']}"):
                                st.json({"input": tool["input"], "output": tool["output"]})
                    
                    # Display explanation
                    if result.get("explanation"):
                        st.info(result["explanation"])
                    
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to API: {e}")
                st.info(f"Make sure the API is running at {API_URL}")

with tab2:
    st.header("Ingested Documents")
    
    try:
        response = requests.get(f"{API_URL}/sources", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get("sources", [])
            
            if sources:
                st.write(f"Found {len(sources)} documents")
                
                for source in sources:
                    with st.expander(f"📄 {source.get('title', 'Untitled')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Document ID:** {source.get('doc_id')}")
                            st.write(f"**Type:** {source.get('doc_type')}")
                            st.write(f"**Version:** {source.get('version')}")
                        with col2:
                            st.write(f"**Authority Level:** {source.get('authority_level')}")
                            st.write(f"**Chunks:** {source.get('chunk_count', 0)}")
                            st.write(f"**Rules:** {source.get('rule_count', 0)}")
                        
                        st.write(f"**Effective From:** {source.get('effective_from')}")
                        if source.get('effective_to'):
                            st.write(f"**Effective To:** {source['effective_to']}")
            else:
                st.info("No documents have been ingested yet.")
                st.write("Upload documents using the API:")
                st.code("""
curl -X POST http://localhost:8000/ingest \\
  -F "file=@document.pdf" \\
  -F 'metadata={"doc_id":"DOC-001",...}'
                """)
        else:
            st.error("Failed to fetch documents")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to API: {e}")

with tab3:
    st.header("Audit Trail")
    
    trace_id_input = st.text_input("Enter Trace ID", placeholder="e.g., 7f3c2a9e")
    
    if st.button("Fetch Audit Record"):
        if trace_id_input:
            try:
                headers = {}
                if student_id:
                    headers["X-Student-Id"] = student_id
                
                response = requests.get(
                    f"{API_URL}/audit/{trace_id_input}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    audit = response.json()
                    st.json(audit)
                elif response.status_code == 404:
                    st.error("Trace ID not found")
                elif response.status_code == 403:
                    st.error("Access denied")
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to API: {e}")
        else:
            st.warning("Please enter a trace ID")

# Footer
st.divider()
st.caption("AI-Powered University Student Services Assistant | HCLTech Future Ready AI Engineer Hackathon")
