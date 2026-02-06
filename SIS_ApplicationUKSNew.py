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

# =========================================================
# 0. KONFIGURACIJA IN NAPREDNI STILI (CSS)
# =========================================================
st.set_page_config(
    page_title="SIS Universal Knowledge Synthesizer",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Integracija CSS za vizualne poudarke, Google linke in gladko navigacijo
# Vključuje stilske definicije za semantične poudarke in interaktivne elemente
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
        padding: 15px;
        border-radius: 10px;
        background-color: #f8f9fa;
        border-left: 5px solid #00B0F0;
        margin-bottom: 20px;
    }
    .idea-mode-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #fff4e6;
        border-left: 5px solid #ff922b;
        margin-bottom: 20px;
        font-weight: bold;
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
    Izriše interaktivno omrežje Cytoscape.js s podporo za oblike iz metamodela,
    shranjevanje slike in funkcijo lupe za fokusiranje vozlišč.
    """
    cyto_html = f"""
    <div style="position: relative;">
        <button id="save_btn" style="position: absolute; top: 10px; right: 10px; z-index: 100; padding: 8px 12px; background: #2a9d8f; color: white; border: none; border-radius: 5px; cursor: pointer; font-family: sans-serif; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">💾 Export Graph as PNG</button>
        <div id="{container_id}" style="width: 100%; height: 600px; background: #ffffff; border-radius: 15px; border: 1px solid #eee; box-shadow: 2px 2px 12px rgba(0,0,0,0.05);"></div>
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
                            'label': 'data(label)', 'text-valign': 'center', 'color': '#333',
                            'background-color': 'data(color)', 'width': 'data(size)', 'height': 'data(size)',
                            'shape': 'data(shape)', 
                            'font-size': '12px', 'font-weight': 'bold', 'text-outline-width': 2,
                            'text-outline-color': '#fff', 'cursor': 'pointer', 'z-index': 'data(z_index)',
                            'box-shadow': '0px 4px 6px rgba(0,0,0,0.1)'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 3, 'line-color': '#adb5bd', 'label': 'data(rel_type)',
                            'font-size': '10px', 'font-weight': 'bold', 'color': '#2a9d8f',
                            'target-arrow-color': '#adb5bd', 'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier', 'text-rotation': 'autorotate',
                            'text-background-opacity': 1, 'text-background-color': '#ffffff',
                            'text-background-padding': '2px', 'text-background-shape': 'roundrectangle'
                        }}
                    }},
                    /* DODATNI STILI ZA LOGIKO LUPE */
                    {{
                        selector: 'node.highlighted',
                        style: {{
                            'border-width': 4, 'border-color': '#e76f51', 'transform': 'scale(1.5)',
                            'z-index': 9999, 'font-size': '18px'
                        }}
                    }},
                    {{
                        selector: '.dimmed',
                        style: {{ 'opacity': 0.15, 'text-opacity': 0 }}
                    }}
                ],
                layout: {{ name: 'cose', padding: 50, animate: true, nodeRepulsion: 25000, idealEdgeLength: 120 }}
            }});

            /* LOGIKA LUPE (Fokusiranje na sosesko ob prehodu z miško) */
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
                    target.style.backgroundColor = "#ffffcc";
                    setTimeout(function(){{ target.style.backgroundColor = "transparent"; }}, 2500);
                }}
            }});

            document.getElementById('save_btn').addEventListener('click', function() {{
                var png64 = cy.png({{full: true, bg: 'white'}});
                var link = document.createElement('a');
                link.href = png64;
                link.download = 'sis_knowledge_graph.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=650)

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
# 1. POPOLNA ONTOLOGIJA Z IMPLEMENTACIJO METAMODELA (Basic Human Thinking)
# =========================================================================
HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": {"color": "#A6A6A6", "shape": "rectangle"},
        "Identity": {"color": "#C6EFCE", "shape": "rectangle"},
        "Autobiographical memory": {"color": "#C6EFCE", "shape": "rectangle"},
        "Mission": {"color": "#92D050", "shape": "rectangle"},
        "Vision": {"color": "#FFFF00", "shape": "rectangle"},
        "Goal": {"color": "#00B0F0", "shape": "rectangle"},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle"},
        "Ethics/moral": {"color": "#FFC000", "shape": "rectangle"},
        "Hierarchy of interests": {"color": "#F8CBAD", "shape": "rectangle"},
        "Rule": {"color": "#F2F2F2", "shape": "rectangle"},
        "Decision-making": {"color": "#FFFF99", "shape": "rectangle"},
        "Problem solving": {"color": "#D9D9D9", "shape": "rectangle"},
        "Conflict situation": {"color": "#00FF00", "shape": "rectangle"},
        "Knowledge": {"color": "#DDEBF7", "shape": "rectangle"},
        "Tool": {"color": "#00B050", "shape": "rectangle"},
        "Experience": {"color": "#00B050", "shape": "rectangle"},
        "Classification": {"color": "#CCC0DA", "shape": "rectangle"},
        "Psychological aspect": {"color": "#F8CBAD", "shape": "rectangle"},
        "Sociological aspect": {"color": "#00FFFF", "shape": "rectangle"}
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
        ("Problem solving", "Conflict situation", "yes or no"),
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

# =========================================================================
# MENTAL APPROACHES ONTOLOGY (Diagram Derived Logic)
# =========================================================================
MENTAL_APPROACHES_ONTOLOGY = {
    "nodes": {
        "Perspective shifting": {"color": "#00FF00", "shape": "rectangle"},
        "Similarity and difference": {"color": "#FFFF00", "shape": "rectangle"},
        "Core": {"color": "#FFC000", "shape": "rectangle"},
        "Attraction": {"color": "#F2A6A2", "shape": "rectangle"},
        "Repulsion": {"color": "#D9D9D9", "shape": "rectangle"},
        "Condensation": {"color": "#CCC0DA", "shape": "rectangle"},
        "Framework and foundation": {"color": "#F8CBAD", "shape": "rectangle"},
        "Bipolarity and dialectics": {"color": "#DDEBF7", "shape": "rectangle"},
        "Constant": {"color": "#E1C1D1", "shape": "rectangle"},
        "Associativity": {"color": "#E1C1D1", "shape": "rectangle"},
        "Induction": {"color": "#B4C6E7", "shape": "rectangle"},
        "Whole and part": {"color": "#00FF00", "shape": "rectangle"},
        "Mini-max": {"color": "#00FF00", "shape": "rectangle"},
        "Addition and composition": {"color": "#FF00FF", "shape": "rectangle"},
        "Hierarchy": {"color": "#C6EFCE", "shape": "rectangle"},
        "Balance": {"color": "#00B0F0", "shape": "rectangle"},
        "Deduction": {"color": "#92D050", "shape": "rectangle"},
        "Abstraction and elimination": {"color": "#00B0F0", "shape": "rectangle"},
        "Pleasure and displeasure": {"color": "#00FF00", "shape": "rectangle"},
        "Openness and closedness": {"color": "#FFC000", "shape": "rectangle"}
    },
    "relations": [
        ("Perspective shifting", "Similarity and difference", "leads to"),
        ("Core", "Similarity and difference", "influences"),
        ("Core", "Attraction", "has dynamic"),
        ("Core", "Repulsion", "has dynamic"),
        ("Repulsion", "Bipolarity and dialectics", "leads to"),
        ("Framework and foundation", "Bipolarity and dialectics", "mutually interacts"),
        ("Bipolarity and dialectics", "Constant", "stabilizes"),
        ("Constant", "Associativity", "allows"),
        ("Induction", "Whole and part", "bidirectional link"),
        ("Induction", "Hierarchy", "structures"),
        ("Whole and part", "Mini-max", "optimizes"),
        ("Mini-max", "Addition and composition", "results in"),
        ("Deduction", "Hierarchy", "defines taxonomy"),
        ("Deduction", "Abstraction and elimination", "processes through"),
        ("Deduction", "Pleasure and displeasure", "evaluates through"),
        ("Hierarchy", "Balance", "maintains"),
        ("Balance", "Addition and composition", "stabilizes"),
        ("Balance", "Abstraction and elimination", "reconciles"),
        ("Openness and closedness", "Pleasure and displeasure", "modulates response")
    ]
}

KNOWLEDGE_BASE = {
    "mental approaches": list(MENTAL_APPROACHES_ONTOLOGY["nodes"].keys()),
    "User profiles": {"Adventurers": {"description": "Explorers of hidden patterns."}, "Applicators": {"description": "Efficiency focused."}, "Know-it-alls": {"description": "Systemic clarity."}, "Observers": {"description": "System monitors."}},
    "Scientific paradigms": {"Empiricism": "Sensory experience.", "Rationalism": "Deductive logic.", "Constructivism": "Social build.", "Positivism": "Strict facts.", "Pragmatism": "Practical utility."},
    "Structural models": {"Causal Connections": "Causality.", "Principles & Relations": "Fundamental laws.", "Episodes & Sequences": "Time-flow.", "Facts & Characteristics": "Raw data.", "Generalizations": "Frameworks.", "Glossary": "Definitions.", "Concepts": "Abstract constructs."},
    "Science fields": {
        "Physics": {"cat": "Natural", "methods": ["Modeling", "Simulation"], "tools": ["Accelerator", "Spectrometer"], "facets": ["Quantum", "Relativity"]},
        "Chemistry": {"cat": "Natural", "methods": ["Synthesis", "Spectroscopy"], "tools": ["NMR", "Chromatography"], "facets": ["Organic", "Molecular"]},
        "Biology": {"cat": "Natural", "methods": ["Sequencing", "CRISPR"], "tools": ["Microscope", "Bio-Incubator"], "facets": ["Genetics", "Ecology"]},
        "Neuroscience": {"cat": "Natural", "methods": ["Neuroimaging", "Electrophys"], "tools": ["fMRI", "EEG"], "facets": ["Plasticity", "Synaptic"]},
        "Psychology": {"cat": "Social", "methods": ["Double-Blind Trials", "Psychometrics"], "tools": ["fMRI", "Testing Kits"], "facets": ["Behavioral", "Cognitive"]},
        "Sociology": {"cat": "Social", "methods": ["Ethnography", "Surveys"], "tools": ["Data Analytics", "Archives"], "facets": ["Stratification", "Dynamics"]},
        "Computer Science": {"cat": "Formal", "methods": ["Algorithm Design", "Verification"], "tools": ["LLMGraphTransformer", "GPU Clusters"], "facets": ["AI", "Cybersecurity"]},
        "Psychiatry": {"cat": "Applied/Medical", "methods": ["Diagnosis", "Clinical Trials"], "tools": ["DSM-5", "EEG"], "facets": ["Clinical Psychiatry", "Neuropsychiatry"]},
        "Medicine": {"cat": "Applied", "methods": ["Clinical Trials", "Epidemiology"], "tools": ["MRI/CT", "Bio-Markers"], "facets": ["Immunology", "Pharmacology"]},
        "Engineering": {"cat": "Applied", "methods": ["Prototyping", "FEA Analysis"], "tools": ["3D Printers", "CAD Software"], "facets": ["Robotics", "Nanotech"]},
        "Library Science": {"cat": "Applied", "methods": ["Taxonomy", "Appraisal"], "tools": ["OPAC", "Metadata"], "facets": ["Retrieval", "Knowledge Org"]},
        "Philosophy": {"cat": "Humanities", "methods": ["Socratic Method", "Phenomenology"], "tools": ["Logic Mapping", "Critical Analysis"], "facets": ["Epistemology", "Metaphysics"]},
        "Linguistics": {"cat": "Humanities", "methods": ["Corpus Analysis", "Syntactic Parsing"], "tools": ["Praat", "NLTK Toolkit"], "facets": ["Socioling", "CompLing"]},
        "Geography": {"cat": "Natural/Social", "methods": ["Spatial Analysis", "GIS"], "tools": ["ArcGIS"], "facets": ["Human Geo", "Physical Geo"]},
        "Geology": {"cat": "Natural", "methods": ["Stratigraphy", "Mineralogy"], "tools": ["Seismograph"], "facets": ["Tectonics", "Petrology"]},
        "Climatology": {"cat": "Natural", "methods": ["Climate Modeling"], "tools": ["Weather Stations"], "facets": ["Change Analysis"]},
        "History": {"cat": "Humanities", "methods": ["Archives"], "tools": ["Archives"], "facets": ["Social History"]},
        "Legal science": {"cat": "Social", "methods": ["Legal Hermeneutics", "Comparative Law", "Dogmatic Method", "Empirical Legal Research"], "tools": ["Legislative Databases", "Case Law Archives", "Constitutional Records"], "facets": ["Jurisprudence", "Constitutional Law", "Criminal Law", "Civil Law"]},
        "Economics": {"cat": "Social", "methods": ["Econometrics", "Game Theory", "Market Modeling"], "tools": ["Stata", "R", "Bloomberg"], "facets": ["Macroeconomics", "Behavioral Economics"]},
        "Politics": {"cat": "Social", "methods": ["Policy Analysis", "Comparative Politics"], "tools": ["Polls", "Legislative Databases"], "facets": ["International Relations", "Governance"]},
        "Criminology": {"cat": "Social", "methods": ["Case Studies", "Statistical Analysis", "Profiling"], "tools": ["NCVS", "Crime Mapping Software"], "facets": ["Victimology", "Penology", "Criminal Behavior"]},
        "Forensic sciences": {"cat": "Applied/Natural", "methods": ["DNA Profiling", "Ballistics", "Trace Analysis"], "tools": ["Mass Spectrometer", "Luminol", "Comparison Microscope"], "facets": ["Toxicology", "Pathology", "Digital Forensics"]}
    }
}

# =========================================================
# 2. STREAMLIT INTERFACE KONSTRUKCIJA
# =========================================================

if 'expertise_val' not in st.session_state: st.session_state.expertise_val = "Expert"
if 'show_user_guide' not in st.session_state: st.session_state.show_user_guide = False

# --- STRANSKA VRSTICA ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    st.header("⚙️ Control Panel")
    
    api_key = st.text_input(
        "Groq API Key:", 
        type="password", 
        help="Security: Your key is held only in volatile RAM and is never stored on our servers."
    )
    
    if st.button("📖 User Guide"):
        st.session_state.show_user_guide = not st.session_state.show_user_guide
        st.rerun()
    if st.session_state.show_user_guide:
        st.info("""
        1. **API Key**: Enter your key to connect the AI engine. It is NOT stored on the server.
        2. **Minimal Config**: Physics, CS, and Linguistics are pre-selected.
        3. **Authors**: Provide author names to fetch ORCID metadata.
        4. **Metamodel Logic**: The system now integrates the 'Basic Human Thinking' architecture.
        5. **Semantic Graph**: Explore colorful nodes interconnected via metamodel logic (TT, BT, NT).
        6. **Shapes & 3D**: Nodes use specific shapes: rectangles, ellipses, or diamonds.
        7. **Export PNG**: Use the 💾 button to save the graph to your local disk.
        """)
        if st.button("Close Guide ✖️"): st.session_state.show_user_guide = False; st.rerun()

    st.divider()
    st.subheader("📚 Knowledge Explorer")
    with st.expander("👤 User Profiles"):
        for p, d in KNOWLEDGE_BASE["User profiles"].items(): st.write(f"**{p}**: {d['description']}")
    with st.expander("🧠 mental approaches"):
        for a in KNOWLEDGE_BASE["mental approaches"]: st.write(f"• {a}")
    with st.expander("🌍 Scientific paradigms"):
        for p, d in KNOWLEDGE_BASE["Scientific paradigms"].items(): st.write(f"**{p}**: {d}")
    with st.expander("🔬 Science fields"):
        for s in sorted(KNOWLEDGE_BASE["Science fields"].keys()): st.write(f"• **{s}**")
    with st.expander("🏗️ Structural models"):
        for m, d in KNOWLEDGE_BASE["Structural models"].items(): st.write(f"**{m}**: {d}")
    
    st.divider()
    if st.button("♻️ Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['target_authors_key'] = ""
        st.session_state['user_query_key'] = ""
        st.rerun()
    
    st.link_button("🌐 GitHub Repository", "https://github.com/", use_container_width=True)
    st.link_button("🆔 ORCID Registry", "https://orcid.org/", use_container_width=True)
    st.link_button("🎓 Google Scholar", "https://scholar.google.com/", use_container_width=True)

st.title("🧱 SIS Universal Knowledge Synthesizer")
st.markdown("Advanced Multi-dimensional synthesis with **Basic Human Thinking Metamodel Integration**.")

# PRIKAZ METAMODELA KOT REFERENČNI OKVIR
st.markdown("""
<div class="metamodel-box">
    <b>🧠 Integrated Metamodel Architecture:</b> 
    The current session integrates nodes like <i>Concentration, Identity, Mission, Vision, Goal, Problem, </i> and outcomes like <i>Psychological & Sociological Aspects</i>. 
    The logic follows exact relationships: <code>Problem threatens Identity</code>, <code>Rule realizes Goal</code>, <code>Conflict results in Sociological outcome</code>.
</div>
""", unsafe_allow_html=True)

st.markdown("### 🛠️ Configure Your Multi-Dimensional Cognitive Build")

# ROW 1: AUTHORS
r1_c1, r1_c2, r1_c3 = st.columns([1, 2, 1])
with r1_c2:
    target_authors = st.text_input("👤 Research Authors:", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič", key="target_authors_key")
    st.caption("Active bibliographic analysis via ORCID (includes publication years).")

# ROW 2: CORE CONFIG (Minimal settings, specific fields)
r2_c1, r2_c2, r2_c3 = st.columns(3)
with r2_c1:
    sel_profiles = st.multiselect("1. User Profiles:", list(KNOWLEDGE_BASE["User profiles"].keys()), default=["Adventurers"])
with r2_c2:
    all_sciences = sorted(list(KNOWLEDGE_BASE["Science fields"].keys()))
    sel_sciences = st.multiselect("2. Science Fields:", all_sciences, default=["Physics", "Psychology", "Sociology"])
with r2_c3:
    expertise = st.select_slider("3. Expertise Level:", options=["Novice", "Intermediate", "Expert"], value=st.session_state.expertise_val)

# ROW 3: PARADIGMS & MODELS (Minimal settings)
r3_c1, r3_c2, r3_c3 = st.columns(3)
with r3_c1:
    sel_models = st.multiselect("4. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r3_c2:
    sel_paradigms = st.multiselect("5. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism"])
with r3_c3:
    goal_context = st.selectbox("6. Context / Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

# ROW 4: APPROACHES, METHODS, TOOLS (RESTORED - Minimal settings)
r4_c1, r4_c2, r4_c3 = st.columns(3)
with r4_c1:
    sel_approaches = st.multiselect("7. mental approaches:", KNOWLEDGE_BASE["mental approaches"], default=["Perspective shifting"])

agg_meth, agg_tool = [], []
for s in sel_sciences:
    if s in KNOWLEDGE_BASE["Science fields"]:
        agg_meth.extend(KNOWLEDGE_BASE["Science fields"][s]["methods"])
        agg_tool.extend(KNOWLEDGE_BASE["Science fields"][s]["tools"])

with r4_c2:
    sel_methods = st.multiselect("8. Methodologies:", sorted(list(set(agg_meth))), default=[])
with r4_c3:
    sel_tools = st.multiselect("9. Specific Tools:", sorted(list(set(agg_tool))), default=[])

st.divider()
# UI REVISION: Added file attachment to the right of the inquiry box
col_inq_main, col_inq_attach = st.columns([3, 1])
with col_inq_main:
    user_query = st.text_area("❓ Your Synthesis Inquiry:", 
                             placeholder="Type 'create useful ideas' to involve the Metamodel and Mental Approach Logic.",
                             height=150, key="user_query_key")

with col_inq_attach:
    uploaded_file = st.file_uploader("📂 Attach .txt (max 2MB):", type=['txt'], help="Append a text file as supplementary context for your inquiry.")
    file_attachment_content = ""
    if uploaded_file is not None:
        if uploaded_file.size > 2 * 1024 * 1024:
            st.error("File exceeds 2MB limit.")
        else:
            file_attachment_content = uploaded_file.read().decode("utf-8")
            st.success(f"File attached: {uploaded_file.name}")

# Logic to combine manual query with file attachment content
if file_attachment_content:
    processed_query = f"{user_query}\n\n[SUPPLEMENTAL DATA FROM ATTACHMENT]:\n{file_attachment_content}"
else:
    processed_query = user_query

# =========================================================
# 3. JEDRO SINTEZE: GROQ AI + INTERCONNECTED 18D GRAPH
# =========================================================
if st.button("🚀 Execute Multi-Dimensional Synthesis", use_container_width=True):
    if not api_key: st.error("Missing Groq API Key. Please provide your own key in the sidebar.")
    elif not user_query: st.warning("Please provide an inquiry.")
    else:
        try:
            # --- DEFINE LOGIC FLAGS ---
            q_lower = user_query.lower()
            
            # Phrase detection for production vs synthesis
            trigger_idea_prod = "use hierarchical associative logic and integrated metamodel architecture and mental approach logic"
            trigger_create_useful = "create useful ideas"
            trigger_hier_assoc = "use hierarchical associative logic"
            trigger_strict_hier = "use strict hierarchical logic"
            trigger_relational = "use relational logic"
            
            # Identify if the demand is for production + synthesis or just synthesis
            is_idea_mode = (trigger_idea_prod in q_lower) or (trigger_create_useful in q_lower) or ("innovative ideas" in q_lower)
            
            # Determine logic type based on specific demands
            if trigger_strict_hier in q_lower:
                logic_type = "Strict hierarchical logic"
                logic_desc = "Uporabi IZKLJUČNO hierarhične relacije: TT (Top Term), BT (Broader Term), NT (Narrower Term). Fokus na vertikalni taksonomiji."
            elif trigger_relational in q_lower:
                logic_type = "Relational logic"
                logic_desc = "Uporabi IZKLJUČNO lateralne relacije: AS (Associative), EQ (Equivalent), IN (Inheritance/Class). Fokus na mrežni povezanosti."
            else:
                logic_type = "Hierarchical associative logic"
                logic_desc = "Uporabi CELOTEN nabor relacij: TT (Top Term), BT (Broader Term), NT (Narrower Term), RT (Related Term), AS (Associative), EQ (Equivalent) in IN (Inheritance/Instance)."

            # --- STEP 2: SUPERIOR IDEA PRODUCTION LOGIC ---
            idea_production_prompt = ""
            metamodel_instruction = ""
            mental_approaches_instruction = ""
            
            if is_idea_mode:
                # ONLY involve Integrated Metamodel Architecture AND Mental Approach Logic when explicitly producing ideas
                metamodel_instruction = f"CORE METAMODEL INTEGRATION (MANDATORY): {json.dumps(HUMAN_THINKING_METAMODEL)}"
                
                # PRIPRAVA MENTAL APPROACHES KONTEKSTA
                mental_approaches_context = json.dumps(MENTAL_APPROACHES_ONTOLOGY)
                mental_approaches_instruction = f"""
                MENTAL APPROACHES DIAGRAM LOGIC (MANDATORY):
                Incorporate the directional logic and inter-node connections defined here: {mental_approaches_context}.
                Key structural paths to observe from the image:
                - 'Core' leads to 'Similarity and difference', 'Attraction', and 'Repulsion'.
                - 'Repulsion' triggers 'Bipolarity and dialectics'.
                - 'Induction' and 'Whole and part' are mutually dependent.
                - 'Whole and part' flows into 'Mini-max'.
                - 'Hierarchy' flows into 'Balance' which reconciliation 'Addition and composition' and 'Abstraction and elimination'.
                - 'Deduction' defines 'Hierarchy' and evaluations through 'Pleasure and displeasure'.
                """
                
                idea_production_prompt = """
                *** SUPERIOR IDEA PRODUCTION MODE ACTIVE ***
                The user explicitly commanded 'Create useful ideas' or combined logic with Metamodel/Mental frameworks.
                You are now expected to PERFORM KNOWLEDGE SYNTHESIS AND PRODUCE NEW USEFUL INNOVATIVE IDEAS.
                Shift from descriptive analysis to RADICAL INNOVATION. 
                Use nodes like 'Conflict situation', 'Problem', and 'Mental approaches' (e.g., Perspective shifting, Bipolarity) to:
                1. Forge entirely new cross-disciplinary theories.
                2. Design novel solutions that don't exist in current literature.
                3. Propose 'Useful Innovative Ideas' that solve the stated problem using the rules provided.
                Your response must emphasize original conceptual synthesis AND generative creativity.
                """
                st.markdown("""<div class="idea-mode-box">✨ Production & Synthesis Mode engaged: Generating novel innovative concepts using Metamodel and Mental Logic.</div>""", unsafe_allow_html=True)
            else:
                # STANDALONE Knowledge Synthesis (No Thinking Metamodel or Mental Approach logic involved)
                idea_production_prompt = """
                *** KNOWLEDGE SYNTHESIS MODE ***
                The user is looking for knowledge synthesis and structured organization.
                Focus on structured analysis, taxonomy, and interconnectedness within the provided science fields. 
                DO NOT focus on producing hypothetical innovative ideas. Focus strictly on existing knowledge structures and their relationships.
                """
                metamodel_instruction = "In this mode, do not use the 'Human Thinking' metamodel."
                mental_approaches_instruction = "In this mode, do not use the 'Mental Approach' logic. Focus purely on the domain-specific science fields selected."

            biblio = fetch_author_bibliographies(target_authors) if target_authors else ""
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            
            # SISTEMSKO NAVODILO
            sys_prompt = f"""
            You are the SIS Synthesizer. Perform an exhaustive dissertation (1500+ words).
            
            MANDATORY ARCHITECTURAL LOGIC: {logic_type}
            {logic_desc}

            {idea_production_prompt}

            {metamodel_instruction}
            
            {mental_approaches_instruction}
            
            FIELDS: {", ".join(sel_sciences)}. CONTEXT AUTHORS: {biblio}.
            
            THESAURUS ALGORITHM & UML LOGIC. Ensure dense interconnection.
            
            GEOMETRICAL VISUALIZATION TASK:
            - Analyze user inquiry for shape preferences. Default shape is 'ellipse'. 
            - Use colors and shapes from the contexts provided (Metamodel/Mental only if idea mode).
            
            STRICT FORMATTING & SPACE ALLOCATION:
            - Focus 100% of the textual content on deep research and interdisciplinary synergy.
            - DO NOT explain the visualization in the text.
            - End with '### SEMANTIC_GRAPH_JSON' followed by valid JSON only.
            
            GRAPH DENSITY REQUIREMENT:
            - GENERATE A DENSE SEMANTIC NETWORK WITH APPROXIMATELY 30-40 INTERCONNECTED NODES.
            - Every node must strictly follow the Color/Shape logic from the contexts.
            
            JSON schema: {{"nodes": [{{"id": "n1", "label": "Text", "type": "Root|Branch|Leaf|Class", "color": "#hex", "shape": "triangle|rectangle|ellipse|diamond"}}], "edges": [{{"source": "n1", "target": "n2", "rel_type": "BT|NT|AS|TT|outcome_of"}}]}}
            """
            
            with st.spinner('Synthesizing exhaustive interdisciplinary synergy (8–40s)...'):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": processed_query}],
                    temperature=0.75 if is_idea_mode else 0.45, 
                    max_tokens=4000
                )
                
                text_out = response.choices[0].message.content
                parts = text_out.split("### SEMANTIC_GRAPH_JSON")
                main_markdown = parts[0]
                
                # --- PROCESIRANJE BESEDILA (Google Search + Authors + Anchors) ---
                if len(parts) > 1:
                    try:
                        g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                        # 1. Koncepti -> Google Search + ID značka
                        for n in g_json.get("nodes", []):
                            lbl, nid = n["label"], n["id"]
                            g_url = urllib.parse.quote(lbl)
                            pattern = re.compile(re.escape(lbl), re.IGNORECASE)
                            replacement = f'<span id="{nid}"><a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}<i class="google-icon">↗</i></a></span>'
                            main_markdown = pattern.sub(replacement, main_markdown, count=1)
                        
                        # 2. Avtorji -> Google Search Link
                        if target_authors:
                            for auth_name in target_authors.split(","):
                                auth_stripped = auth_name.strip()
                                if auth_stripped:
                                    a_url = urllib.parse.quote(auth_stripped)
                                    a_pattern = re.compile(re.escape(auth_stripped), re.IGNORECASE)
                                    a_rep = f'<a href="https://www.google.com/search?q={a_url}" target="_blank" class="author-search-link">{auth_stripped}<i class="google-icon">↗</i></a>'
                                    main_markdown = a_pattern.sub(a_rep, main_markdown)
                    except: pass

                st.subheader("📊 Synthesis Output")
                st.markdown(main_markdown, unsafe_allow_html=True)

                # --- VIZUALIZACIJA (Interconnected Graph) ---
                if len(parts) > 1:
                    try:
                        g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                        st.subheader("🕸️ Metamodel-Driven Semantic Network")
                        st.caption(f"{logic_type} utilizing Human Thinking Metamodel Logic")
                        
                        elements = []
                        for n in g_json.get("nodes", []):
                            level = n.get("type", "Branch")
                            size = 100 if level == "Class" else (90 if level == "Root" else (70 if level == "Branch" else 50))
                            color = n.get("color", "#2a9d8f")
                            shape = n.get("shape", "ellipse")
                            elements.append({"data": {
                                "id": n["id"], "label": n["label"], "color": color,
                                "size": size, "shape": shape, "z_index": 10 if level in ["Root", "Class"] else 1
                            }})
                        for e in g_json.get("edges", []):
                            elements.append({"data": {
                                "source": e["source"], "target": e["target"], "rel_type": e.get("rel_type", "AS")
                            }})
                        render_cytoscape_network(elements, "semantic_viz_full")
                    except: st.warning("Graph data could not be parsed.")

                if biblio:
                    with st.expander("📚 View Metadata Fetched from Research Databases"):
                        st.text(biblio)
                
        except Exception as e:
            st.error(f"Synthesis failed: {e}")

# PODNOŽJE (ZAHVALA IN VERZIJA)
st.divider()
st.caption("SIS Universal Knowledge Synthesizer | v21.2 Synthesis vs Idea Production Engine | 2026")










