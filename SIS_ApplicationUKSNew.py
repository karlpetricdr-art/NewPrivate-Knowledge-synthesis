import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
from datetime import datetime
from openai import OpenAI
import streamlit.components.v1 as components

# =========================================================================
# 0. KONFIGURACIJA IN NAPREDNI STILI (CSS)
# =========================================================================
# Setting up the platform architecture with wide layout and custom branding.
st.set_page_config(
    page_title="SIS Universal Knowledge Synthesizer",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Integracija CSS za vizualne poudarke, Google linke in gladko navigacijo.
# This styling block is critical for the "Lupa" (Magnifying glass) effect 
# and the semantic highlighting that links the text to the knowledge graph.
st.markdown("""
<style>
    .semantic-node-highlight {
        color: #2a9d8f;
        font-weight: bold;
        border-bottom: 2px solid #2a9d8f;
        padding: 0 2px;
        background-color: #f0fdfa;
        border-radius: 4px;
        transition: all 0.3s ease;
        text-decoration: none !important;
    }
    .semantic-node-highlight:hover {
        background-color: #ccfbf1;
        color: #264653;
        border-bottom: 2px solid #e76f51;
    }
    .author-search-link {
        color: #1d3557;
        font-weight: bold;
        text-decoration: none;
        border-bottom: 1px double #457b9d;
        padding: 0 1px;
    }
    .author-search-link:hover {
        color: #e63946;
        background-color: #f1faee;
    }
    .google-icon {
        font-size: 0.75em;
        vertical-align: super;
        margin-left: 2px;
        color: #457b9d;
        opacity: 0.8;
    }
    .stMarkdown {
        line-height: 1.8;
        font-size: 1.05em;
    }
    .metamodel-box {
        padding: 20px;
        border-radius: 12px;
        background-color: #f1f3f5;
        border-left: 6px solid #00B0F0;
        margin-bottom: 25px;
        font-family: 'Inter', sans-serif;
    }
    .mental-approaches-infobox {
        padding: 20px;
        border-radius: 12px;
        background-color: #fffbeb;
        border-left: 6px solid #fab005;
        margin-bottom: 25px;
        color: #453700;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    /* Enhanced UI elements for scroll-to-node focus */
    .highlight-active {
        background-color: #fffae6 !important;
        transition: background-color 1.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    """Pretvori SVG v base64 format za prikaz slike v Streamlit sidebarju."""
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

# --- LOGOTIP: 3D RELIEF (Embedded SVG) ---
SVG_3D_RELIEF = """
<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="reliefShadow" x="-20%" y="-20%" width="150%" height="150%">
            <feDropShadow dx="4" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.4"/>
        </filter>
        <linearGradient id="pyramidSide" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#e0e0e0;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#bdbdbd;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="treeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#66bb6a;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2e7d32;stop-opacity:1" />
        </linearGradient>
    </defs>
    <circle cx="120" cy="120" r="100" fill="#f0f0f0" stroke="#000000" stroke-width="4" filter="url(#reliefShadow)" />
    <path d="M120 40 L50 180 L120 200 Z" fill="url(#pyramidSide)" />
    <path d="M120 40 L190 180 L120 200 Z" fill="#9e9e9e" />
    <rect x="116" y="110" width="8" height="70" rx="2" fill="#5d4037" />
    <circle cx="120" cy="85" r="30" fill="url(#treeGrad)" filter="url(#reliefShadow)" />
    <circle cx="95" cy="125" r="22" fill="#43a047" filter="url(#reliefShadow)" />
    <circle cx="145" cy="125" r="22" fill="#43a047" filter="url(#reliefShadow)" />
    <rect x="70" y="170" width="20" height="12" rx="2" fill="#1565c0" filter="url(#reliefShadow)" />
    <rect x="150" y="170" width="20" height="12" rx="2" fill="#c62828" filter="url(#reliefShadow)" />
    <rect x="110" y="185" width="20" height="12" rx="2" fill="#f9a825" filter="url(#reliefShadow)" />
</svg>
"""

# --- CYTOSCAPE RENDERER Z DINAMIČNIMI OBLIKAMI IN IZVOZOM + LUPA ---
def render_cytoscape_network(elements, container_id="cy"):
    """
    Izriše interaktivno omrežje Cytoscape.js s podporo za oblike iz metamodelov,
    shranjevanje slike in funkcijo lupe za fokusiranje vozlišč.
    """
    cyto_html = f"""
    <div style="position: relative;">
        <button id="save_btn" style="position: absolute; top: 10px; right: 10px; z-index: 100; padding: 10px 15px; background: #2a9d8f; color: white; border: none; border-radius: 6px; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: bold; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">💾 Export Graph as PNG</button>
        <div id="{container_id}" style="width: 100%; height: 650px; background: #ffffff; border-radius: 18px; border: 1px solid #ddd; box-shadow: 4px 4px 15px rgba(0,0,0,0.08);"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)', 'text-valign': 'center', 'color': '#212529',
                            'background-color': 'data(color)', 'width': 'data(size)', 'height': 'data(size)',
                            'shape': 'data(shape)', 
                            'font-size': '12px', 'font-weight': 'bold', 'text-outline-width': 2,
                            'text-outline-color': '#ffffff', 'cursor': 'pointer', 'z-index': 'data(z_index)',
                            'box-shadow': '0px 4px 8px rgba(0,0,0,0.12)'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 3, 'line-color': '#adb5bd', 'label': 'data(rel_type)',
                            'font-size': '11px', 'font-weight': 'bold', 'color': '#2a9d8f',
                            'target-arrow-color': '#adb5bd', 'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier', 'text-rotation': 'autorotate',
                            'text-background-opacity': 1, 'text-background-color': '#ffffff',
                            'text-background-padding': '3px', 'text-background-shape': 'roundrectangle'
                        }}
                    }},
                    {{
                        selector: 'node.highlighted',
                        style: {{
                            'border-width': 5, 'border-color': '#e76f51', 'transform': 'scale(1.6)',
                            'z-index': 9999, 'font-size': '18px'
                        }}
                    }},
                    {{
                        selector: '.dimmed',
                        style: {{ 'opacity': 0.1, 'text-opacity': 0 }}
                    }}
                ],
                layout: {{ name: 'cose', padding: 60, animate: true, nodeRepulsion: 30000, idealEdgeLength: 150 }}
            }});

            // Logic for 'Lupa' / Neighbourhood Focus
            cy.on('mouseover', 'node', function(e){{
                var sel = e.target;
                cy.elements().addClass('dimmed');
                sel.neighborhood().add(sel).removeClass('dimmed').addClass('highlighted');
            }});
            
            cy.on('mouseout', 'node', function(e){{
                cy.elements().removeClass('dimmed highlighted');
            }});
            
            cy.on('tap', 'node', function(evt){{
                var elementId = evt.target.id();
                var target = window.parent.document.getElementById(elementId);
                if (target) {{
                    target.scrollIntoView({{behavior: "smooth", block: "center"}});
                    target.classList.add('highlight-active');
                    setTimeout(function(){{ target.classList.remove('highlight-active'); }}, 3000);
                }}
            }});

            document.getElementById('save_btn').addEventListener('click', function() {{
                var png64 = cy.png({{full: true, bg: 'white'}});
                var link = document.createElement('a');
                link.href = png64;
                link.download = 'sis_universal_metamodel.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=700)

# --- PRIDOBIVANJE BIBLIOGRAFIJ Z LETNICAMI ---
def fetch_author_bibliographies(author_input):
    """Zajame bibliografske podatke z letnicami preko ORCID in Scholar API baz."""
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    comprehensive_biblio = ""
    headers = {"Accept": "application/json"}
    
    for auth in author_list:
        orcid_id = None
        try:
            search_url = f"https://pub.orcid.org/v3.0/search/?q={auth}"
            s_res = requests.get(search_url, headers=headers, timeout=5).json()
            if s_res.get('result'):
                orcid_id = s_res['result'][0]['orcid-identifier']['path']
        except: pass

        if orcid_id:
            try:
                record_url = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
                r_res = requests.get(record_url, headers=headers, timeout=5).json()
                works = r_res.get('activities-summary', {}).get('works', {}).get('group', [])
                comprehensive_biblio += f"\n--- ORCID BIBLIOGRAPHY: {auth.upper()} ({orcid_id}) ---\n"
                if works:
                    for work in works[:5]:
                        summary = work.get('work-summary', [{}])[0]
                        title = summary.get('title', {}).get('title', {}).get('value', 'N/A')
                        pub_date = summary.get('publication-date')
                        year = pub_date.get('year').get('value', 'n.d.') if pub_date and pub_date.get('year') else "n.d."
                        comprehensive_biblio += f"- [{year}] {title}\n"
                else: comprehensive_biblio += "No public works found.\n"
            except: pass
        else:
            try:
                ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query=author:\"{auth}\"&limit=3&fields=title,year"
                ss_res = requests.get(ss_url, timeout=5).json()
                papers = ss_res.get("data", [])
                if papers:
                    comprehensive_biblio += f"\n--- SCHOLAR BIBLIOGRAPHY: {auth.upper()} ---\n"
                    for p in papers:
                        comprehensive_biblio += f"- [{p.get('year','n.d.')}] {p['title']}\n"
            except: pass
    return comprehensive_biblio

# =========================================================================
# 1. POPOLNA ONTOLOGIJA Z INTEGRACIJO DVEH METAMODELOV
# =========================================================================

# METAMODEL LOGIKA 1: BASIC HUMAN THINKING (Image 1 Integration)
# Reflecting the path from mental concentration to sociological/psychological aspects.
HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": {"color": "#A6A6A6", "shape": "rectangle", "level": "root"},
        "Identity": {"color": "#C6EFCE", "shape": "rectangle", "level": "branch"},
        "Autobiographical memory": {"color": "#C6EFCE", "shape": "rectangle", "level": "leaf"},
        "Mission": {"color": "#92D050", "shape": "rectangle", "level": "branch"},
        "Vision": {"color": "#FFFF00", "shape": "rectangle", "level": "branch"},
        "Goal": {"color": "#00B0F0", "shape": "rectangle", "level": "branch"},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle", "level": "event"},
        "Ethics/moral": {"color": "#FFC000", "shape": "rectangle", "level": "branch"},
        "Hierarchy of interests": {"color": "#F8CBAD", "shape": "rectangle", "level": "branch"},
        "Rule": {"color": "#F2F2F2", "shape": "rectangle", "level": "logic"},
        "Decision-making": {"color": "#FFFF99", "shape": "rectangle", "level": "process"},
        "Problem solving": {"color": "#D9D9D9", "shape": "rectangle", "level": "process"},
        "Conflict situation": {"color": "#00FF00", "shape": "rectangle", "level": "outcome"},
        "Knowledge": {"color": "#DDEBF7", "shape": "rectangle", "level": "resource"},
        "Tool": {"color": "#00B050", "shape": "rectangle", "level": "resource"},
        "Experience": {"color": "#00B050", "shape": "rectangle", "level": "resource"},
        "Classification": {"color": "#CCC0DA", "shape": "rectangle", "level": "logic"},
        "Psychological aspect": {"color": "#F8CBAD", "shape": "rectangle", "level": "outcome"},
        "Sociological aspect": {"color": "#00FFFF", "shape": "rectangle", "level": "outcome"}
    },
    "relations": [
        ("Human mental concentration", "Identity", "has"),
        ("Human mental concentration", "Mission", "can have"),
        ("Identity", "Autobiographical memory", "has"),
        ("Mission", "Vision", "can have"),
        ("Vision", "Goal", "can have"),
        ("Problem", "Identity", "threatens"),
        ("Problem", "Mission", "impedes"),
        ("Problem", "Vision", "impedes"),
        ("Problem", "Goal", "threatens"),
        ("Problem", "Ethics/moral", "has"),
        ("Ethics/moral", "Problem", "can solve"),
        ("Problem", "Rule", "can be connected"),
        ("Hierarchy of interests", "Goal", "realizes"),
        ("Hierarchy of interests", "Knowledge", "realizes or hinders"),
        ("Rule", "Goal", "realizes or hinders"),
        ("Rule", "Decision-making", "realizes or hinders"),
        ("Knowledge", "Goal", "acquisition"),
        ("Decision-making", "Problem solving", "realizes or hinders"),
        ("Ethics/moral", "Problem solving", "helps or hinders"),
        ("Problem", "Problem solving", "should"),
        ("Problem solving", "Conflict situation", "yes or no result"),
        ("Knowledge", "Classification", "with the help of"),
        ("Knowledge", "Tool", "with the help of"),
        ("Knowledge", "Experience", "with the help of"),
        ("Experience", "Psychological aspect", "can be the outcome"),
        ("Experience", "Sociological aspect", "can be the outcome"),
        ("Conflict situation", "Psychological aspect", "can be the outcome"),
        ("Conflict situation", "Sociological aspect", "can be the outcome"),
        ("Psychological aspect", "Sociological aspect", "interconnected")
    ]
}

# METAMODEL LOGIKA 2: MENTAL APPROACHES (Image 2 Integration)
# Detailed mapping of logical loops: Induction/Deduction, Core Forces, and Associativity.
MENTAL_APPROACHES_METAMODEL = {
    "nodes": {
        "Mental approaches": {"color": "#FFFF00", "shape": "rectangle", "desc": "Meta-structure for logic."},
        "Perspective shifting": {"color": "#92D050", "shape": "rectangle", "desc": "Angular cognitive focus."},
        "Similarity and difference": {"color": "#FFFF00", "shape": "rectangle", "desc": "Comparison engine."},
        "Core": {"color": "#FFC000", "shape": "rectangle", "desc": "The central attractor."},
        "Attraction": {"color": "#F28B82", "shape": "rectangle", "desc": "Convergent logical force."},
        "Repulsion": {"color": "#D9D9D9", "shape": "rectangle", "desc": "Divergent logical force."},
        "Condensation": {"color": "#D7BDE2", "shape": "rectangle", "desc": "Data compression."},
        "Framework and foundation": {"color": "#EDBB99", "shape": "rectangle", "desc": "Underlying logic."},
        "Bipolarity and dialectics": {"color": "#AED6F1", "shape": "rectangle", "desc": "Managing dualities."},
        "Pleasure and displeasure": {"color": "#58D68D", "shape": "rectangle", "desc": "Emotional thinking state."},
        "Constant": {"color": "#F5B7B1", "shape": "rectangle", "desc": "Invariant parameters."},
        "Associativity": {"color": "#FBFCFC", "shape": "rectangle", "desc": "Network linking capacity."},
        "Induction": {"color": "#A9CCE3", "shape": "rectangle", "desc": "Bottom-up reasoning."},
        "Deduction": {"color": "#ABEBC6", "shape": "rectangle", "desc": "Top-down reasoning."},
        "Hierarchy": {"color": "#D5F5E3", "shape": "rectangle", "desc": "Priority structure."},
        "Whole and part": {"color": "#2ECC71", "shape": "rectangle", "desc": "Holistic scaling."},
        "Mini-max": {"color": "#00FF00", "shape": "rectangle", "desc": "Optimal result logic."},
        "Addition and composition": {"color": "#FF00FF", "shape": "rectangle", "desc": "Combinatorial logic."},
        "Balance": {"color": "#00B0F0", "shape": "rectangle", "desc": "Equilibrium state."},
        "Abstraction and elimination": {"color": "#00FFFF", "shape": "rectangle", "desc": "Noise removal."},
        "Openness and closedness": {"color": "#E67E22", "shape": "rectangle", "desc": "System boundaries."}
    },
    "relations": [
        ("Mental approaches", "Perspective shifting", "leads to"),
        ("Mental approaches", "Similarity and difference", "leads to"),
        ("Perspective shifting", "Core", "defines"),
        ("Similarity and difference", "Core", "defines"),
        ("Core", "Attraction", "drives"),
        ("Core", "Repulsion", "drives"),
        ("Mental approaches", "Induction", "triggers"),
        ("Induction", "Hierarchy", "organizes into"),
        ("Hierarchy", "Deduction", "directs"),
        ("Hierarchy", "Induction", "directs"),
        ("Hierarchy", "Whole and part", "classifies"),
        ("Whole and part", "Mini-max", "optimizes"),
        ("Addition and composition", "Mini-max", "optimizes"),
        ("Mini-max", "Balance", "targets"),
        ("Balance", "Abstraction and elimination", "maintains"),
        ("Framework and foundation", "Bipolarity and dialectics", "supports"),
        ("Bipolarity and dialectics", "Constant", "stabilizes"),
        ("Constant", "Associativity", "allows"),
        ("Associativity", "Mental approaches", "feeds back to")
    ]
}

# --- GLOBAL KNOWLEDGE BASE ---
KNOWLEDGE_BASE = {
    "User profiles": {
        "Adventurers": {"description": "Explorers of hidden patterns."},
        "Applicators": {"description": "Efficiency focused logic."},
        "Know-it-alls": {"description": "Systemic clarity advocates."},
        "Observers": {"description": "Monitors of systemic flow."}
    },
    "Scientific paradigms": {
        "Empiricism": "Focus on sensory data.",
        "Rationalism": "Focus on deductive certainty.",
        "Constructivism": "Focus on social construction of reality.",
        "Positivism": "Strict adherence to scientific facts.",
        "Pragmatism": "Practical utility over abstract theory."
    },
    "Structural models": {
        "Causal Connections": "Analyzing A to B flow.",
        "Principles & Relations": "Fundamental laws of nature.",
        "Episodes & Sequences": "Temporal flow of events.",
        "Facts & Characteristics": "Raw data attributes.",
        "Generalizations": "Broad framework applications.",
        "Glossary": "Precise nomenclature.",
        "Concepts": "Abstract thinking constructs."
    },
    "Science fields": {
        "Physics": {"cat": "Natural", "methods": ["Modeling", "Simulation"], "tools": ["Accelerator"], "facets": ["Quantum"]},
        "Neuroscience": {"cat": "Natural", "methods": ["Neuroimaging"], "tools": ["fMRI", "EEG"], "facets": ["Plasticity"]},
        "Psychology": {"cat": "Social", "methods": ["Psychometrics"], "tools": ["Testing Kits"], "facets": ["Behavioral"]},
        "Sociology": {"cat": "Social", "methods": ["Ethnography", "Surveys"], "tools": ["Archives"], "facets": ["Dynamics"]},
        "Computer Science": {"cat": "Formal", "methods": ["Algorithm Design"], "tools": ["GPU Clusters"], "facets": ["AI"]},
        "Philosophy": {"cat": "Humanities", "methods": ["Phenomenology"], "tools": ["Logic Mapping"], "facets": ["Epistemology"]},
        "Linguistics": {"cat": "Humanities", "methods": ["Corpus Analysis"], "tools": ["NLTK Toolkit"], "facets": ["Socioling"]}
    }
}

# =========================================================================
# 2. STREAMLIT INTERFACE KONSTRUKCIJA
# =========================================================================

if 'expertise_val' not in st.session_state: st.session_state.expertise_val = "Expert"
if 'show_user_guide' not in st.session_state: st.session_state.show_user_guide = False

# --- STRANSKA VRSTICA (Sidebar Architecture) ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    st.header("⚙️ Control Panel")
    
    api_key = st.text_input("Groq API Key:", type="password", help="Your volatile RAM key for Groq Cloud.")
    
    if st.button("📖 User Guide"):
        st.session_state.show_user_guide = not st.session_state.show_user_guide
        st.rerun()
        
    if st.session_state.show_user_guide:
        st.info("""
        1. **Dual Metamodel Logic**: This engine integrates BOTH the Thinking/Decision Making model and the Mental Approaches model.
        2. **ORCID & Bibliographies**: Input author names to fetch real research context.
        3. **Inquiry**: Submit a complex query. The AI will adhere to the node paths from the images.
        4. **Export**: Use the 💾 button on the graph to save your interdisciplinary map.
        """)
        if st.button("Close Guide ✖️"): st.session_state.show_user_guide = False; st.rerun()

    st.divider()
    st.subheader("📚 Active Meta-Architectures")
    with st.expander("🧠 Human Thinking Model (Img 1)"):
        for n in HUMAN_THINKING_METAMODEL["nodes"].keys(): st.write(f"• {n}")
    with st.expander("🛠️ Mental Approaches Model (Img 2)"):
        for a in MENTAL_APPROACHES_METAMODEL["nodes"].keys(): st.write(f"• {a}")
    
    st.divider()
    if st.button("♻️ Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    
    st.link_button("🆔 ORCID Search", "https://orcid.org/", use_container_width=True)
    st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)

st.title("🧱 SIS Universal Knowledge Synthesizer")
st.markdown("Multi-dimensional synthesis via **Thinking & Mental Approaches Metamodel Integration**.")

# PRIKAZ AKTIVNIH METAMODELOV V GLAVNEM OKNU
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.markdown("""
    <div class="metamodel-box">
        <b>🧠 Thinking & Decision Metamodel:</b><br>
        Integrating Concentration, Identity, Problem-solving, and Sociological/Psychological feedback loops.
    </div>
    """, unsafe_allow_html=True)
with col_info2:
    st.markdown("""
    <div class="mental-approaches-infobox">
        <b>🛠️ Mental Approaches Metamodel:</b><br>
        Implementing Hierarchy, Induction/Deduction cycles, Core Forces (Attraction), and Dialectics.
    </div>
    """, unsafe_allow_html=True)

st.markdown("### 🛠️ Configure Your Interdisciplinary Synthesis")

# ROW 1: AUTHORS & CONTEXT
r1_c1, r1_c2, r1_c3 = st.columns([1, 2, 1])
with r1_c2:
    target_authors = st.text_input("👤 Research Authors:", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič", key="target_authors_key")
    st.caption("Active bibliographic context fetching via ORCID.")

# ROW 2: CORE PARAMETERS
r2_c1, r2_c2, r2_c3 = st.columns(3)
with r2_c1:
    sel_profiles = st.multiselect("1. User Profiles:", list(KNOWLEDGE_BASE["User profiles"].keys()), default=["Adventurers"])
with r2_c2:
    sel_sciences = st.multiselect("2. Science Fields:", sorted(list(KNOWLEDGE_BASE["Science fields"].keys())), default=["Physics", "Psychology", "Sociology"])
with r2_c3:
    expertise = st.select_slider("3. Expertise Level:", options=["Novice", "Intermediate", "Expert"], value="Expert")

# ROW 3: MODELS & PARADIGMS
r3_c1, r3_c2, r3_c3 = st.columns(3)
with r3_c1:
    sel_models = st.multiselect("4. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r3_c2:
    sel_paradigms = st.multiselect("5. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism"])
with r3_c3:
    context_goal = st.selectbox("6. Context / Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

st.divider()
user_query = st.text_area("❓ Your Synthesis Inquiry:", 
                         placeholder="Synthesize how Bipolarity logic (Mental Approach) solves the Problem of Identity in quantum neuroscience environments.",
                         height=150, key="user_query_key")

# =========================================================================
# 3. JEDRO SINTEZE: GROQ AI + DUAL METAMODEL LOGIC ENGINE
# =========================================================================
if st.button("🚀 Execute Multi-Metamodel Synthesis", use_container_width=True):
    if not api_key: st.error("Missing Groq API Key.")
    elif not user_query: st.warning("Please provide an inquiry.")
    else:
        try:
            biblio = fetch_author_bibliographies(target_authors) if target_authors else ""
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            
            # --- THE MASTER SYSTEM PROMPT ---
            # Integrating logic gate requirements from both metamodel images.
            # This prompt is engineered to be verbose and logically strict.
            sys_prompt = f"""
            You are the SIS Universal Synthesizer. Perform an exhaustive interdisciplinary dissertation (1500+ words).
            
            MANDATORY ARCHITECTURAL LOGIC GATES:
            
            BLOCK 1: HUMAN THINKING METAMODEL (Image 1)
            - Start analysis with 'Human mental concentration'.
            - Define how 'Problem' threatens 'Identity' or 'Goal'.
            - Map out 'Rule' and 'Decision-making' as mediators.
            - Ensure 'Problem solving' leads to 'Conflict situation'.
            - Conclude with 'Psychological aspect' and 'Sociological aspect' interconnected outcomes.
            
            BLOCK 2: MENTAL APPROACHES METAMODEL (Image 2)
            - Use the 'Hierarchy' <-> 'Induction' <-> 'Deduction' structural loop.
            - Relate 'Perspective shifting' and 'Similarity/Difference' to the 'Core'.
            - Explain the attraction/repulsion forces of the core in your synthesis.
            - Use 'Mini-max' logic for efficiency/optimization.
            - Stabilize concepts via 'Bipolarity and dialectics' and 'Constant' nodes.
            
            BLOCK 3: SELECTION CONTEXT
            - Scientific Fields: {", ".join(sel_sciences)}
            - User Profile: {", ".join(sel_profiles)}
            - Expertise: {expertise}
            - Context Bibliography: {biblio}
            
            STRICT FORMATTING:
            - Focus textual content on research, causal analysis, and innovative synergy.
            - Do not explain the JSON or node types in text.
            - End with '### SEMANTIC_GRAPH_JSON' followed by valid JSON only.
            
            GRAPH DENSITY REQUIREMENT:
            - Generate 35-45 interconnected nodes.
            - Assign colors and shapes according to:
              {json.dumps(HUMAN_THINKING_METAMODEL['nodes'])}
              {json.dumps(MENTAL_APPROACHES_METAMODEL['nodes'])}
            
            JSON schema: {{"nodes": [{{"id": "n1", "label": "Text", "type": "Root|Branch|Leaf", "color": "#hex", "shape": "rectangle"}}], "edges": [{{"source": "n1", "target": "n2", "rel_type": "AS|BT|outcome"}}]}}
            """
            
            with st.spinner('Synthesizing exhaustive interdisciplinary synergy with Dual Metamodels (10–45s)...'):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_query}],
                    temperature=0.6, max_tokens=4000
                )
                
                text_out = response.choices[0].message.content
                parts = text_out.split("### SEMANTIC_GRAPH_JSON")
                main_markdown = parts[0]
                
                # --- POST-PROCESIRANJE (Link injection & Author Anchoring) ---
                if len(parts) > 1:
                    try:
                        g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                        # Concept Search Links
                        for n in g_json.get("nodes", []):
                            lbl, nid = n["label"], n["id"]
                            g_url = urllib.parse.quote(lbl)
                            main_markdown = re.sub(re.escape(lbl), f'<span id="{nid}"><a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}<i class="google-icon">↗</i></a></span>', main_markdown, count=1, flags=re.I)
                        
                        # Author Search Links
                        if target_authors:
                            for auth in target_authors.split(","):
                                a_stripped = auth.strip()
                                if a_stripped:
                                    a_url = urllib.parse.quote(a_stripped)
                                    main_markdown = re.sub(re.escape(a_stripped), f'<a href="https://www.google.com/search?q={a_url}" target="_blank" class="author-search-link">{a_stripped}<i class="google-icon">↗</i></a>', main_markdown)
                    except: pass

                st.subheader("📊 Synthesis Dissertative Output")
                st.markdown(main_markdown, unsafe_allow_html=True)

                # --- VIZUALIZACIJA (Dual-Model Interconnected Graph) ---
                if len(parts) > 1:
                    try:
                        g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                        st.subheader("🕸️ Integrated Dual-Metamodel Network")
                        st.caption("Combined Visualization of Thinking (Img 1) & Mental Approaches (Img 2)")
                        
                        elements = []
                        for n in g_json.get("nodes", []):
                            elements.append({"data": {
                                "id": n["id"], "label": n["label"], "color": n.get("color", "#2a9d8f"),
                                "size": 75, "shape": n.get("shape", "rectangle"), "z_index": 1
                            }})
                        for e in g_json.get("edges", []):
                            elements.append({"data": {
                                "source": e["source"], "target": e["target"], "rel_type": e.get("rel_type", "AS")
                            }})
                        render_cytoscape_network(elements, "semantic_viz_full")
                    except: st.warning("Graph data could not be parsed.")

                if biblio:
                    with st.expander("📚 View Metadata Context"):
                        st.text(biblio)
                
        except Exception as e:
            st.error(f"Synthesis engine failure: {e}")

# PODNOŽJE (Footer & Versioning)
st.divider()
st.caption("SIS Universal Knowledge Synthesizer | v23.0 Multi-Metamodel Logic Edition | 2026")
# TOTAL COMMAND LINE ESTIMATION: > 620 lines.

