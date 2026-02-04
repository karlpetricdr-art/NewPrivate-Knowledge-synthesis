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
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    """Pretvori SVG v base64 format za prikaz slike."""
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
    Izriše interaktivno omrežje Cytoscape.js s podporo za oblike, shranjevanje slike in funkcijo lupe.
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

# =========================================================
# 1. POPOLNA MULTIDIMENZIONALNA ONTOLOGIJA (IMAGE LOGIC)
# =========================================================
KNOWLEDGE_BASE = {
    "mental approaches": ["Perspective shifting", "Induction", "Deduction", "Hierarchy", "Mini-max", "Whole and part", "Addition and composition", "Balance", "Abstraction and elimination", "Openness and closedness", "Bipolarity and dialectics", "Framework and foundation", "Pleasure and displeasure", "Similarity and difference", "Core (Attraction & Repulsion)", "Condensation", "Constant", "Associativity"],
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
        "Computer Science": {"cat": "Formal", "methods": ["Algorithm Design", "Verification"], "tools": ["LLMGraphTransformer", "GPU Clusters", "Git"], "facets": ["AI", "Cybersecurity"]},
        "Medicine": {"cat": "Applied", "methods": ["Clinical Trials", "Epidemiology"], "tools": ["MRI/CT", "Bio-Markers"], "facets": ["Immunology", "Pharmacology"]},
        "Engineering": {"cat": "Applied", "methods": ["Prototyping", "FEA Analysis"], "tools": ["3D Printers", "CAD Software"], "facets": ["Robotics", "Nanotech"]},
        "Library Science": {"cat": "Applied", "methods": ["Taxonomy", "Appraisal"], "tools": ["OPAC", "Metadata"], "facets": ["Retrieval", "Knowledge Org"]},
        "Philosophy": {"cat": "Humanities", "methods": ["Socratic Method", "Phenomenology"], "tools": ["Logic Mapping", "Critical Analysis"], "facets": ["Epistemology", "Metaphysics"]},
        "Linguistics": {"cat": "Humanities", "methods": ["Corpus Analysis", "Syntactic Parsing"], "tools": ["Praat", "NLTK Toolkit"], "facets": ["Socioling", "CompLing"]},
        "Geography": {"cat": "Natural/Social", "methods": ["Spatial Analysis", "GIS"], "tools": ["ArcGIS"], "facets": ["Human Geo", "Physical Geo"]},
        "Geology": {"cat": "Natural", "methods": ["Stratigraphy", "Mineralogy"], "tools": ["Seismograph"], "facets": ["Tectonics", "Petrology"]},
        "Climatology": {"cat": "Natural", "methods": ["Climate Modeling"], "tools": ["Weather Stations"], "facets": ["Change Analysis"]},
        "History": {"cat": "Humanities", "methods": ["Archives"], "tools": ["Archives"], "facets": ["Social History"]},
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
        4. **Inquiry**: Submit a complex query for an exhaustive dissertation.
        5. **Semantic Graph**: Explore colorful nodes interconnected via TT, BT, NT logic.
        6. **Shapes & 3D**: Request triangles, rectangles or 3D bodies in your inquiry.
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
st.markdown("Advanced Multi-dimensional synthesis with **Geometrical Exportable Interdisciplinary Architecture**.")

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
    # PRIVZETO: Physics, Computer science in Linguistics
    sel_sciences = st.multiselect("2. Science Fields:", all_sciences, default=["Physics", "Computer Science", "Linguistics"])
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
user_query = st.text_area("❓ Your Synthesis Inquiry:", 
                         placeholder="Create a synergy for global problems using triangle shapes for causes and 3D geometric bodies for solutions.",
                         height=150, key="user_query_key")

# =========================================================
# 3. JEDRO SINTEZE: GROQ AI + INTERCONNECTED 18D GRAPH
# =========================================================
if st.button("🚀 Execute Multi-Dimensional Synthesis", use_container_width=True):
    if not api_key: st.error("Missing Groq API Key. Please provide your own key in the sidebar.")
    elif not user_query: st.warning("Please provide an inquiry.")
    else:
        try:
            biblio = fetch_author_bibliographies(target_authors) if target_authors else ""
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            
            # --- DODAJANJE HIERARHIČNE ASOCIATIVNE LOGIKE ---
            q_lower = user_query.lower()
            is_strict_hier = "striktna hierarhična logika" in q_lower
            is_relational_only = "relacijska logika" in q_lower

            if is_strict_hier:
                logic_type = "Strict hierarchical logic"
                logic_desc = "Uporabi IZKLJUČNO hierarhične relacije: TT (Top Term), BT (Broader Term), NT (Narrower Term). Fokus na vertikalni taksonomiji."
            elif is_relational_only:
                logic_type = "Relational logic"
                logic_desc = "Uporabi IZKLJUČNO lateralne relacije: AS (Associative), EQ (Equivalent), IN (Inheritance/Class). Fokus na mrežni povezanosti."
            else:
                logic_type = "Hierarchical associative logic"
                logic_desc = "Integriraj CELOTEN nabor relacij: Hierarhične (TT, BT, NT) za strukturo in asociativne (AS, EQ, IN) za lateralne povezave."

            # SISTEMSKO NAVODILO (Z INTEGRIRANO LOGIKO IN POVEČANIM ŠTEVILOM VOZLIŠČ)
            sys_prompt = f"""
            You are the SIS Synthesizer. Perform an exhaustive dissertation (1500+ words).
            
            MANDATORY ARCHITECTURAL LOGIC: {logic_type}
            {logic_desc}

            STRUCTURE (MANDATORY IMAGE LOGIC): 
            1. Root: Authors --TT--> User profiles, Science fields, Expertise level.
            2. Science fields --BT--> Expertise level --NT--> Structural models.
            3. Structural models --AS--> Scientific paradigms.
            4. Scientific paradigms --RT--> mental approaches, methodologies in specific tools.
            5. Scientific paradigms --AS--> Context/Goal.
            6. In all graph edges, use the correct tags: TT, BT, NT, AS, EQ, IN.
            
            FIELDS: {", ".join(sel_sciences)}. CONTEXT AUTHORS: {biblio}.
            
            THESAURUS ALGORITHM & UML LOGIC.

            GEOMETRICAL VISUALIZATION TASK:
            - Analyze user inquiry for shape preferences (triangle, rectangle, hexagon, 3D/diamond).
            - Default shape is 'ellipse'.
            
            STRICT FORMATTING & SPACE ALLOCATION:
            - Focus 100% of the textual content on deep research, causal analysis, and innovative problem-solving synergy.
            - ABSOLUTELY PROHIBITED: Do not list nodes, edges, properties, shapes, or colors in text.
            - DO NOT explain the visualization or JSON schema in the text.
            - End with '### SEMANTIC_GRAPH_JSON' followed by valid JSON only.
            
            GRAPH DENSITY REQUIREMENT:
            - GENERATE A DENSE SEMANTIC NETWORK WITH APPROXIMATELY 30 INTERCONNECTED NODES.
            - Ensure every scientific field and structural model is represented by multiple specific leaf nodes.
            
            JSON schema: {{"nodes": [{{"id": "n1", "label": "Text", "type": "Root|Branch|Leaf|Class", "color": "#hex", "shape": "triangle|rectangle|ellipse|diamond"}}], "edges": [{{"source": "n1", "target": "n2", "rel_type": "BT|NT|AS|Inheritance|EQ|TT|IN"}}]}}
            """
            
            with st.spinner('Synthesizing exhaustive interdisciplinary synergy (8–40s)...'):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_query}],
                    temperature=0.6, max_tokens=4000
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
                        st.subheader("🕸️ LLMGraphTransformer: Unified Interdisciplinary Network")
                        st.caption(f"{logic_type}")
                        
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

st.divider()
st.caption("SIS Universal Knowledge Synthesizer | v18.0 Comprehensive 18D Geometrical Export Edition | 2026")