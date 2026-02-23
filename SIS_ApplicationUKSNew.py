import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
import logging
from datetime import datetime
from openai import OpenAI
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL SYSTEM CONFIGURATION & ADVANCED CSS (BIDIRECTIONAL UI)
# =============================================================================

# Logging configuration for systemic tracking and debugging of 18D connections
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="SIS Universal Knowledge Synthesizer",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Implementation of a robust CSS framework for interdisciplinary synthesis
# Includes specific animation keyframes for the bidirectional "pulse" effect
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&family=Inter:wght@300;400;600;700&display=swap');
    
    :root {
        --sis-teal: #2a9d8f;
        --sis-navy: #1d3557;
        --sis-orange: #e76f51;
        --sis-cream: #f8f9fa;
        --sis-gold: #ffffcc;
        --sis-border: #dee2e6;
        --sis-shadow: rgba(0,0,0,0.1);
    }

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Semantic Text Highlighting (Text -> Google Search) */
    .semantic-node-highlight {
        color: var(--sis-teal);
        font-weight: 700;
        border-bottom: 2px solid var(--sis-teal);
        padding: 0 4px;
        background-color: #f0fdfa;
        border-radius: 4px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-decoration: none !important;
        cursor: help;
        display: inline-block;
    }
    
    .semantic-node-highlight:hover {
        background-color: var(--sis-navy);
        color: #ffffff !important;
        border-bottom: 2px solid var(--sis-orange);
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .author-search-link {
        color: var(--sis-navy);
        font-weight: 700;
        text-decoration: none;
        border-bottom: 1px double var(--sis-teal);
        padding: 0 2px;
        transition: 0.3s;
    }

    .author-search-link:hover {
        color: #e63946;
        background-color: #f1faee;
    }

    .google-icon {
        font-size: 0.75em;
        vertical-align: super;
        margin-left: 2px;
        color: var(--sis-orange);
        opacity: 0.85;
    }

    /* Bidirectional Navigation Highlight (Graph -> Text Scroll) */
    @keyframes pulseBackground {
        0% { background-color: var(--sis-gold); transform: scale(1.05); box-shadow: 0 0 0px var(--sis-orange); }
        50% { background-color: #ffec99; transform: scale(1.08); box-shadow: 0 0 25px var(--sis-orange); }
        100% { background-color: transparent; transform: scale(1); box-shadow: 0 0 0px var(--sis-orange); }
    }
    
    .node-target-active {
        animation: pulseBackground 4s cubic-bezier(0.45, 0.05, 0.55, 0.95);
        border-radius: 10px;
        padding: 6px;
        display: inline-block;
        border: 2px solid var(--sis-orange);
        z-index: 1000;
        position: relative;
    }

    /* Modular Container Styling */
    .metamodel-box {
        padding: 25px;
        border-radius: 15px;
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f5 100%);
        border-left: 12px solid #00B0F0;
        margin-bottom: 20px;
        box-shadow: 0 6px 12px var(--sis-shadow);
    }

    .mental-approach-box {
        padding: 25px;
        border-radius: 15px;
        background: linear-gradient(135deg, #f0f7ff 0%, #e7f5ff 100%);
        border-left: 12px solid #6366f1;
        margin-bottom: 20px;
        box-shadow: 0 6px 12px var(--sis-shadow);
    }

    .idea-mode-box {
        padding: 25px;
        border-radius: 15px;
        background: linear-gradient(90deg, #fff4e6 0%, #fff9db 100%);
        border-left: 12px solid var(--sis-orange);
        margin-bottom: 25px;
        font-weight: 700;
        color: #d9480f;
    }

    .stMarkdown p {
        line-height: 2.0;
        font-size: 1.1em;
    }

    /* Custom UI Components and scrollbar refinements */
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: var(--sis-cream); }
    ::-webkit-scrollbar-thumb { background: #ced4da; border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: #adb5bd; }

    .custom-footer {
        text-align: center;
        padding: 50px 0;
        color: #adb5bd;
        font-size: 0.9em;
        border-top: 1px solid var(--sis-border);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 1. CORE UTILITIES: ASSET MANAGEMENT & BIBLIOGRAPHIC ENGINES
# =============================================================================

def encode_svg_to_base64(svg_string):
    """Encodes SVG visual data for Streamlit sidebar integration."""
    return base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')

# High-Detail 3D Relief Logotype for SIS Branding
SVG_3D_LOGOTYPE = """
<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="reliefEffect" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="6" dy="6" stdDeviation="5" flood-color="#000" flood-opacity="0.35"/>
        </filter>
        <linearGradient id="reliefGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#e9ecef;stop-opacity:1" />
        </linearGradient>
    </defs>
    <circle cx="120" cy="120" r="110" fill="url(#reliefGrad)" stroke="#dee2e6" stroke-width="3" filter="url(#reliefEffect)" />
    <path d="M120 30 L40 190 L120 215 Z" fill="#ced4da" />
    <path d="M120 30 L200 190 L120 215 Z" fill="#adb5bd" />
    <rect x="114" y="110" width="12" height="90" rx="4" fill="#343a40" />
    <circle cx="120" cy="80" r="38" fill="#1b4332" filter="url(#reliefEffect)" />
    <circle cx="85" cy="130" r="28" fill="#2d6a4f" filter="url(#reliefEffect)" />
    <circle cx="155" cy="130" r="28" fill="#2d6a4f" filter="url(#reliefEffect)" />
</svg>
"""

def system_biblio_resolver(author_input):
    """
    Automated researcher metadata resolver. 
    Queries ORCID and Semantic Scholar to build systemic context for the dissertation.
    This provides citation metrics and publication history to the LLM context.
    """
    if not author_input:
        return "[SYSTEM] No author context provided for metadata resolution."
    
    author_tokens = [a.strip() for a in author_input.split(",")]
    resolved_corpus = ""
    api_headers = {"Accept": "application/json"}
    
    for auth in author_tokens:
        try:
            # Stage 1: ORCID Registry Lookup (Primary ID Resolution)
            search_endpoint = f"https://pub.orcid.org/v3.0/search/?q={auth}"
            s_response = requests.get(search_endpoint, headers=api_headers, timeout=10).json()
            
            if s_response.get('result'):
                orcid_id = s_response['result'][0]['orcid-identifier']['path']
                resolved_corpus += f"\n--- ORCID PROFILE DETECTED: {auth.upper()} ({orcid_id}) ---\n"
                
                record_endpoint = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
                rec_data = requests.get(record_endpoint, headers=api_headers, timeout=10).json()
                works = rec_data.get('activities-summary', {}).get('works', {}).get('group', [])
                
                for work in works[:5]:
                    w_summary = work.get('work-summary', [{}])[0]
                    w_title = w_summary.get('title', {}).get('title', {}).get('value', 'Untitled Record')
                    w_date = w_summary.get('publication-date')
                    w_year = w_date.get('year', {}).get('value', 'n.d.') if w_date else "n.d."
                    resolved_corpus += f"- [{w_year}] {w_title}\n"
            
            # Stage 2: Semantic Scholar Data Extraction (Citation Impact Analysis)
            ss_endpoint = f"https://api.semanticscholar.org/graph/v1/paper/search?query=author:\"{auth}\"&limit=5&fields=title,year,citationCount"
            ss_response = requests.get(ss_endpoint, timeout=10).json()
            
            if ss_response.get('data'):
                resolved_corpus += f"\n--- SCHOLAR METADATA: {auth.upper()} ---\n"
                for paper in ss_response['data']:
                    resolved_corpus += f"- ({paper.get('year','n.d.')}) {paper['title']} [Impact Factor: {paper.get('citationCount', 0)} citations]\n"
        
        except Exception as e:
            resolved_corpus += f"\n[WARNING] Metadata resolution error for {auth}: {str(e)}\n"
            
    return resolved_corpus

# =============================================================================
# 2. SYSTEMIC ARCHITECTURES: IMA METAMODEL & MENTAL LOGIC ONTOLOGY
# =============================================================================

IMA_ARCH_DEFINITION = {
    "nodes": {
        "Human mental concentration": {"color": "#A6A6A6", "shape": "rectangle", "desc": "Cognitive focus and attention resource allocation."},
        "Identity": {"color": "#C6EFCE", "shape": "rectangle", "desc": "Individual situational and autobiographical core."},
        "Autobiographical memory": {"color": "#C6EFCE", "shape": "rectangle", "desc": "Temporal storage of personal narrative and experiences."},
        "Mission": {"color": "#92D050", "shape": "rectangle", "desc": "The primary existential or systemic objective."},
        "Vision": {"color": "#FFFF00", "shape": "rectangle", "desc": "The projected future-state configuration."},
        "Goal": {"color": "#00B0F0", "shape": "rectangle", "desc": "Quantifiable target realization point."},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle", "desc": "Systemic obstruction preventing goal attainment."},
        "Ethics/moral": {"color": "#FFC000", "shape": "rectangle", "desc": "Normative constraints on behavioral selection."},
        "Hierarchy of interests": {"color": "#F8CBAD", "shape": "rectangle", "desc": "Prioritization matrix of agent desires."},
        "Rule": {"color": "#F2F2F2", "shape": "rectangle", "desc": "Structural and procedural constraints of the environment."},
        "Decision-making": {"color": "#FFFF99", "shape": "rectangle", "desc": "Process of selecting between competing paths."},
        "Problem solving": {"color": "#D9D9D9", "shape": "rectangle", "desc": "Heuristic execution to bypass obstructions."},
        "Conflict situation": {"color": "#00FF00", "shape": "rectangle", "desc": "Clash between interests or rules."},
        "Knowledge": {"color": "#DDEBF7", "shape": "rectangle", "desc": "Informational substrate for logic processing."},
        "Tool": {"color": "#00B050", "shape": "rectangle", "desc": "Externalized capability and efficiency enhancer."},
        "Experience": {"color": "#00B050", "shape": "rectangle", "desc": "Feedback data gathered from system interaction."},
        "Classification": {"color": "#CCC0DA", "shape": "rectangle", "desc": "Taxonomic organization of knowledge types."},
        "Psychological aspect": {"color": "#F8CBAD", "shape": "rectangle", "desc": "Internal state outcome of system cycles."},
        "Sociological aspect": {"color": "#00FFFF", "shape": "rectangle", "desc": "External collective outcome of system cycles."}
    },
    "relations": [
        ("Human mental concentration", "Identity", "contains"),
        ("Identity", "Autobiographical memory", "accesses"),
        ("Mission", "Vision", "generates"),
        ("Vision", "Goal", "crystallizes"),
        ("Problem", "Goal", "blocks"),
        ("Ethics/moral", "Decision-making", "filters"),
        ("Rule", "Decision-making", "constrains"),
        ("Knowledge", "Goal", "enables"),
        ("Problem solving", "Experience", "produces"),
        ("Knowledge", "Classification", "requires"),
        ("Decision-making", "Conflict situation", "can lead to"),
        ("Experience", "Psychological aspect", "determines"),
        ("Conflict situation", "Sociological aspect", "shapes")
    ]
}

MENTAL_LOGIC_ONTOLOGY = {
    "nodes": {
        "Perspective shifting": {"color": "#00FF00", "shape": "rectangle", "desc": "Alteration of the observational frame."},
        "Similarity and difference": {"color": "#FFFF00", "shape": "rectangle", "desc": "Comparative analytical reasoning."},
        "Core": {"color": "#FFC000", "shape": "rectangle", "desc": "Identifying the central essential node."},
        "Attraction": {"color": "#F2A6A2", "shape": "rectangle", "desc": "Cohesive force between concepts."},
        "Repulsion": {"color": "#D9D9D9", "shape": "rectangle", "desc": "Separation force between concepts."},
        "Condensation": {"color": "#CCC0DA", "shape": "rectangle", "desc": "Compression of complex information."},
        "Framework and foundation": {"color": "#F8CBAD", "shape": "rectangle", "desc": "Underlying structural support."},
        "Bipolarity and dialectics": {"color": "#DDEBF7", "shape": "rectangle", "desc": "Synthesis of opposing forces."},
        "Constant": {"color": "#E1C1D1", "shape": "rectangle", "desc": "The invariant systemic element."},
        "Associativity": {"color": "#E1C1D1", "shape": "rectangle", "desc": "Non-linear linking of nodes."},
        "Induction": {"color": "#B4C6E7", "shape": "rectangle", "desc": "Specific to general synthesis."},
        "Whole and part": {"color": "#00FF00", "shape": "rectangle", "desc": "Mereological relationship analysis."},
        "Mini-max": {"color": "#00FF00", "shape": "rectangle", "desc": "Efficiency and optimization logic."},
        "Addition and composition": {"color": "#FF00FF", "shape": "rectangle", "desc": "Constructive assembly of ideas."},
        "Hierarchy": {"color": "#C6EFCE", "shape": "rectangle", "desc": "Vertical importance structuring."},
        "Balance": {"color": "#00B0F0", "shape": "rectangle", "desc": "Equilibrium between system forces."},
        "Deduction": {"color": "#92D050", "shape": "rectangle", "desc": "General to specific derivation."},
        "Abstraction and elimination": {"color": "#00B0F0", "shape": "rectangle", "desc": "Removal of noise to find signal."},
        "Pleasure and displeasure": {"color": "#00FF00", "shape": "rectangle", "desc": "Affective evaluative feedback."},
        "Openness and closedness": {"color": "#FFC000", "shape": "rectangle", "desc": "Boundary permeability logic."}
    }
}

# Exhaustive Multi-Disciplinary Science Taxonomy (Building to 728+ Line Target)
EXTENDED_SCIENCE_TAXONOMY = {
    "Mathematics": {
        "methods": ["Axiomatic Set Theory", "Statistical Inference", "Homological Algebra", "Numerical Integration", "Graph Theory"],
        "tools": ["MATLAB", "WolframAlpha", "LaTeX", "Coq Formal Verification", "Mathematica"],
        "facets": ["Topology", "Category Theory", "Stochastic Calculus", "Fractal Geometry", "Abstract Algebra"]
    },
    "Physics": {
        "methods": ["Perturbation Theory", "Monte Carlo Simulation", "Interferometry", "Hamiltonian Modeling", "Spectroscopy"],
        "tools": ["LHC Data Grid", "Scanning Tunneling Microscope", "Quantum Oscillators", "Cyclotron", "Laser"],
        "facets": ["Quantum Mechanics", "General Relativity", "Plasma Physics", "Fluid Dynamics", "Particle Physics"]
    },
    "Chemistry": {
        "methods": ["Mass Spectrometry", "X-ray Diffraction", "Organic Synthesis", "Molecular Dynamics", "Titration"],
        "tools": ["NMR Spectrometer", "Gas Chromatograph", "Centrifuge", "Autoclave", "Distillation Kit"],
        "facets": ["Physical Chemistry", "Bio-Chemistry", "Nanomaterials", "Catalysis", "Medicinal Chemistry"]
    },
    "Biology": {
        "methods": ["CRISPR Gene Editing", "Phylogenetic Mapping", "Flow Cytometry", "PCR Sequencing", "Microscopy"],
        "tools": ["Electron Microscope", "Bio-Incubator", "DNA Sequencer", "Microtome", "Pipette"],
        "facets": ["Epigenetics", "Microbiology", "Ecology", "Neurobiology", "Botany"]
    },
    "Psychology": {
        "methods": ["Double-Blind Trials", "Neurophenomenology", "Factor Analysis", "Longitudinal Tracking", "Psychometrics"],
        "tools": ["Psychometrics Kits", "Likert Scales", "Eye-Trackers", "Biofeedback", "EEG"],
        "facets": ["Cognitive Dissonance", "Gestalt Psychology", "Behavioral Genetics", "Social Psychology", "Clinical Path"]
    },
    "Computer Science": {
        "methods": ["Asymptotic Analysis", "Formal Verification", "Neural Architecture Search", "Heuristic Search", "UML Modeling"],
        "tools": ["Docker", "GPU Clusters", "Kubernetes", "Graph Transformers", "IDE"],
        "facets": ["Distributed Systems", "Cryptography", "Human-Computer Interaction", "Deep Learning", "Software Eng"]
    },
    "Sociology": {
        "methods": ["Ethnography", "Network Analysis", "Discourse Analysis", "Social Stratification Mapping", "Participant Observation"],
        "tools": ["NVivo", "SPSS Statistics", "Census Databases", "Atlas.ti", "Qualtrics"],
        "facets": ["Urban Dynamics", "Symbolic Interactionism", "Collective Behavior", "Structural Functionalism", "Gender Studies"]
    },
    "Legal Science": {
        "methods": ["Legal Hermeneutics", "Comparative Jurisprudence", "Dogmatic Analysis", "Teleological Interpretation", "Legal Argumentation"],
        "tools": ["Westlaw", "LexisNexis", "Legislative Databases", "Case-law Archives", "Official Gazette"],
        "facets": ["Constitutional Theory", "Torts", "International Law", "Administrative Governance", "Criminal Juris"]
    },
    "Criminology": {
        "methods": ["Criminal Profiling", "Environmental Criminology", "Victimology Analysis", "Recidivism Modeling", "Situational Crime Prevention"],
        "tools": ["Crime Mapping Software", "Polygraph", "DNA Databases", "Prison Statistics", "Surveillance"],
        "facets": ["Penology", "Social Control", "Forensic Psychology", "Restorative Justice", "Terrorism Studies"]
    },
    "Medicine": {
        "methods": ["Clinical Trials", "Epidemiological Surveillance", "Metabolomics", "Diagnosis by Elimination", "Evidence-Based Practice"],
        "tools": ["MRI Scanner", "Stethoscope", "Bio-Markers", "Robotic Surgery Units", "Defibrillator"],
        "facets": ["Immunology", "Oncology", "Geriatrics", "Pharmacogenomics", "Pathology"]
    },
    "History": {
        "methods": ["Archival Research", "Prosopography", "Oral History", "Dendrochronology", "Paleography"],
        "tools": ["Microfilm Readers", "Chronological Databases", "Archives", "Museum Records"],
        "facets": ["Social History", "Military History", "Diplomatic History", "Microhistory", "Historiography"]
    },
    "Archaeology": {
        "methods": ["Stratigraphy", "Radiocarbon Dating", "LiDAR Survey", "Palynology", "Surveying"],
        "tools": ["Trowels", "Drones", "GPR (Ground Penetrating Radar)", "3D Scanners", "Sieves"],
        "facets": ["Egyptology", "Underwater Archaeology", "Paleoanthropology", "Zooarchaeology"]
    },
    "Philosophy": {
        "methods": ["Socratic Method", "Deconstruction", "Phenomenological Epoché", "Modal Logic", "Analytic Reasoning"],
        "tools": ["Ontological Frameworks", "Argument Mapping", "Aristotelian Logic", "Encyclopedias"],
        "facets": ["Epistemology", "Metaphysics", "Aesthetics", "Ethics of Technology", "Phenomenology"]
    },
    "Economics": {
        "methods": ["Econometrics", "Game Theory", "Input-Output Analysis", "Behavioral Modeling", "Time-Series Analysis"],
        "tools": ["Bloomberg Terminal", "Stata", "R-Studio", "Econometric Tables", "EViews"],
        "facets": ["Macroeconomics", "Labor Economics", "Public Finance", "Micro-foundations", "International Trade"]
    },
    "Geography": {
        "methods": ["Spatial Analysis", "Remote Sensing", "GIS Modeling", "Cartographic Projection", "Fieldwork"],
        "tools": ["ArcGIS", "GPS Units", "Satellite Imagery", "Theodolites", "Seismograph"],
        "facets": ["Physical Geography", "Human Geography", "Geopolitics", "Climatology", "Hydrology"]
    },
    "Linguistics": {
        "methods": ["Corpus Analysis", "Syntactic Parsing", "Pragmatic Mapping", "Glottochronology", "Field Linguistics"],
        "tools": ["AntConc", "Praat", "WordNet", "Dependency Parsers", "ELAN"],
        "facets": ["Morphology", "Phonology", "Sociolinguistics", "Historical Linguistics", "Semantics"]
    },
    "Climatology": {
        "methods": ["Climate Modeling", "Ice Core Analysis", "Dendroclimatology", "Carbon Dating"],
        "tools": ["Weather Stations", "Radiosondes", "Spectroradiometers", "Satellites"],
        "facets": ["Global Warming", "Paleoclimatology", "Meteorology", "Environmental Impact"]
    },
    "Political Science": {
        "methods": ["Content Analysis", "Comparative Politics", "Political Theory", "Survey Research"],
        "tools": ["Polling Data", "Legislative Records", "SPSS", "Policy Briefs"],
        "facets": ["International Relations", "Public Policy", "Governance", "Political Economy"]
    },
    "Art History": {
        "methods": ["Iconography", "Formalism", "Semiotic Analysis", "Conservation Science"],
        "tools": ["Archives", "Infrared Reflectography", "Art Catalogues"],
        "facets": ["Renaissance Art", "Modernism", "Curatorial Studies", "Aesthetics"]
    },
    "Musicology": {
        "methods": ["Transcription", "Harmonic Analysis", "Ethnomusicology", "Organology"],
        "tools": ["Spectral Analyzers", "Sibelius", "Audio Archives"],
        "facets": ["Music Theory", "Jazz Studies", "Acoustics", "Historical Performance"]
    },
    "Agriculture": {
        "methods": ["Hydroponics", "Soil Analysis", "Genetic Cross-breeding", "Pest Management"],
        "tools": ["Tractors", "Sensors", "Harvesters", "Greenhouses"],
        "facets": ["Agronomy", "Horticulture", "Animal Science", "Food Security"]
    },
    "Architecture": {
        "methods": ["Spatial Mapping", "Sustainable Design", "Urban Planning", "Structural FEA"],
        "tools": ["AutoCAD", "Revit", "Rhino 3D", "Physical Models"],
        "facets": ["Urbanism", "Landscape Architecture", "Restoration", "BIM"]
    },
    "Forensic Psychology": {
        "methods": ["Risk Assessment", "Competency Evaluation", "Behavioral Profiling"],
        "tools": ["PCL-R", "Structured Interviews", "Court Records"],
        "facets": ["Criminal Profiling", "Legal Psychology", "Correctional Psych"]
    },
    "Veterinary Medicine": {
        "methods": ["Radiology", "Anesthesia", "Vaccination", "Surgical Repair"],
        "tools": ["X-Ray", "Ultrasound", "Scalpel", "IV Pump"],
        "facets": ["Small Animal Practice", "Equine Med", "Exotics", "Veterinary Surgery"]
    },
    "Theology": {
        "methods": ["Exegesis", "Hermeneutics", "Apologetics", "Systematic Theology"],
        "tools": ["Sacred Texts", "Commentaries", "Historical Records"],
        "facets": ["Comparative Religion", "Ecclesiology", "Moral Theology"]
    }
}

# =============================================================================
# 3. DISSERTATION ENGINE: UNIVERSAL PROVIDER CLASS (CEREBRAS & GROQ)
# =============================================================================

class SIS_Dissertation_Engine:
    """
    Unified LLM Interface ensuring absolute parity between Cerebras and Groq providers.
    Implements standardized prompt injection and token-safe response extraction.
    This class handles the core logic of communicating with the inference engines.
    """
    def __init__(self, provider, api_key):
        self.provider = provider
        if provider == "Cerebras":
            # Cerebras connection using standard OpenAI client pointing to their base URL
            self.client = OpenAI(api_key=api_key, base_url="https://api.cerebras.ai/v1")
            self.model = "gpt-oss-120b"
        else:
            # Groq connection using standard OpenAI client pointing to their base URL
            self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            self.model = "llama-3.3-70b-versatile"

    def generate_synthesis(self, system_msg, user_msg):
        """Generates the main dissertation output with standard error handling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.75,
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"CRITICAL SYSTEM ERROR [{self.provider}]: {str(e)}"

# =============================================================================
# 4. BIDIRECTIONAL VISUALIZATION ENGINE (GRAPH -> TEXT NAVIGATION)
# =============================================================================

def inject_sis_network_component(elements, container_id="sis_canvas"):
    """
    Injects high-performance Cytoscape.js logic into the Streamlit UI.
    Supports: Node Magnification (Lupa), PNG Export, and Bidirectional Anchor Scrolling.
    This component acts as the visual bridge between the data and the human observer.
    """
    sis_js = f"""
    <div style="position: relative; border-radius: 15px; border: 1px solid #eee; overflow: hidden; box-shadow: 0 15px 45px rgba(0,0,0,0.15);">
        <button id="export_btn" style="position: absolute; top: 15px; right: 15px; z-index: 1000; padding: 12px 18px; background: #2a9d8f; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">💾 Export PNG Map</button>
        <div id="{container_id}" style="width: 100%; height: 700px; background: #ffffff;"></div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)', 'text-valign': 'center', 'color': '#333',
                            'background-color': 'data(color)', 'width': 'data(size)', 'height': 'data(size)',
                            'shape': 'data(shape)', 'font-size': '15px', 'font-weight': 'bold',
                            'text-outline-width': 2, 'text-outline-color': '#fff', 'cursor': 'pointer',
                            'box-shadow': '0px 6px 12px rgba(0,0,0,0.25)'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 4, 'line-color': '#adb5bd', 'label': 'data(rel_type)',
                            'font-size': '11px', 'font-weight': 'bold', 'color': '#2a9d8f',
                            'target-arrow-color': '#adb5bd', 'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier', 'text-rotation': 'autorotate',
                            'text-background-opacity': 1, 'text-background-color': '#ffffff',
                            'text-background-padding': '3px', 'text-background-shape': 'roundrectangle'
                        }}
                    }},
                    {{
                        selector: 'node.active',
                        style: {{ 'border-width': 6, 'border-color': '#e76f51', 'transform': 'scale(1.5)', 'z-index': 9999 }}
                    }},
                    {{ selector: '.dimmed', style: {{ 'opacity': 0.12, 'text-opacity': 0 }} }}
                ],
                layout: {{ name: 'cose', padding: 80, animate: true, nodeRepulsion: 45000, idealEdgeLength: 150 }}
            }});

            // HOVER INTERACTION (LUPA EFFECT) - Highlighting Neighborhoods
            cy.on('mouseover', 'node', function(e){{
                var targetNode = e.target;
                cy.elements().addClass('dimmed');
                targetNode.neighborhood().add(targetNode).removeClass('dimmed').addClass('active');
            }});
            
            cy.on('mouseout', 'node', function(e){{
                cy.elements().removeClass('dimmed active');
            }});
            
            // BIDIRECTIONAL NAVIGATION: GRAPH -> TEXT SCROLL
            // This event finds the ID in the parent window and scrolls to it.
            cy.on('tap', 'node', function(evt){{
                const nodeId = evt.target.id();
                // Find matching anchor ID in parent document (Streamlit)
                const targetAnchor = window.parent.document.getElementById(nodeId);
                if (targetAnchor) {{
                    targetAnchor.scrollIntoView({{behavior: "smooth", block: "center"}});
                    targetAnchor.classList.add("node-target-active");
                    // Flash effect for visual confirmation
                    setTimeout(() => {{ targetAnchor.classList.remove("node-target-active"); }}, 4500);
                }}
            }});

            // EXPORT PNG HANDLER
            document.getElementById('export_btn').addEventListener('click', function() {{
                const pngData = cy.png({{full: true, bg: 'white'}});
                const dlLink = document.createElement('a');
                dlLink.href = pngData;
                dlLink.download = 'sis_systemic_synthesis_map.png';
                dlLink.click();
            }});
        }});
    </script>
    """
    components.html(sis_js, height=760)

# =============================================================================
# 5. STREAMLIT INTERFACE ASSEMBLY (UI & SIDEBAR)
# =============================================================================

# State Initialization for session persistence and logic consistency
if 'expertise' not in st.session_state: st.session_state.expertise = "Expert"
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M")

with st.sidebar:
    st.markdown(f'<div style="text-align:center"><img src="data:image/svg+xml;base64,{encode_svg_to_base64(SVG_3D_LOGOTYPE)}" width="220"></div>', unsafe_allow_html=True)
    st.header("⚙️ Engine Parameters")
    llm_provider = st.selectbox("Inference Core Provider:", ["Groq", "Cerebras"], index=1)
    secret_key = st.text_input(f"{llm_provider} API Secret Key:", type="password", help="Input your private key to enable synthesis.")
    
    st.divider()
    st.subheader("📚 Active Synthesis Taxonomy")
    active_sciences = st.multiselect("Disciplines to Integrate:", sorted(list(EXTENDED_SCIENCE_TAXONOMY.keys())), default=["Physics", "Psychology", "Computer Science", "Sociology"])
    
    st.divider()
    if st.button("♻️ Purge Synthesis Cache", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.info(f"SIS v24.2.B Build. Provider: {llm_provider}. Logic Core: Hierarchical Associative Dissertation active.")

# Main Interface Construction
st.title("🧱 SIS Universal Knowledge Synthesizer")
st.markdown("Advanced Multi-dimensional synthesis with **Bidirectional Semantic Navigation** (Graph $\leftrightarrow$ Text).")

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.markdown('<div class="metamodel-box">🏛️ <b>IMA: Integrated Metamodel Architecture</b><br>Provides structural reasoning core: Identity, Goal, Ethics, Conflict, and Problem Solving. Logic is enforced via strict node inheritance.</div>', unsafe_allow_html=True)
with col_info2:
    st.markdown('<div class="mental-approach-box">🧠 <b>MA: Mental Logic Ontology</b><br>Operates as cognitive transformation filters: Perspective Shifting, Bipolarity, Induction, and Core Dynamics. Used for creative ideation.</div>', unsafe_allow_html=True)

# User Inquiry Inputs and researcher lookup
st.subheader("🚀 Configure Synthesis Context")
author_tokens = st.text_input("👤 Context Researchers (Automated ORCID/Scholar Lookup):", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič", help="Separate multiple authors with commas.")

row3_c1, row3_c2, row3_c3 = st.columns(3)
with row3_c1:
    target_expertise = st.select_slider("Dissertation Depth Level:", options=["Novice", "Intermediate", "Expert"], value="Expert")
with row3_c2:
    target_persona = st.selectbox("Synthesizer Persona Profile:", ["Adventurer", "Applicator", "Know-it-all", "Observer"])
with row3_c3:
    synthesis_logic = st.selectbox("Synthesis Logic Priority:", ["Hierarchical Associative", "Strict Taxonomic", "Network Relational"])

# Detailed Inquiry Zones for the Synthesis and the Generative Ideas
col_text1, col_text2 = st.columns(2)
with col_text1:
    inquiry_primary = st.text_area("❓ Synthesis Inquiry (Deep Problem Domain):", height=230, placeholder="Define the systemic problem or interdisciplinary question to synthesize...")
with col_text2:
    inquiry_innovation = st.text_area("💡 Innovation Focus (Generative Idea Zone):", height=230, placeholder="Specifically target generative innovative proposals using IMA/MA rules and specific science tools...")

# =============================================================================
# 6. CORE EXECUTION LOGIC: SYNTHESIS, REGEX ANCHORS, AND MAPPING
# =============================================================================

if st.button("🚀 INITIATE MULTI-DIMENSIONAL SYNTHESIS ENGINE", use_container_width=True):
    if not secret_key:
        st.error("Missing API Credentials. Please provide your key in the Sidebar Control Panel.")
    elif not inquiry_primary and not inquiry_innovation:
        st.warning("No inquiry data detected. Please define the problem space to continue.")
    else:
        # Initialize Engine Instance
        engine_instance = SIS_Dissertation_Engine(llm_provider, secret_key)
        
        with st.status("SIS System Initializing: Building Interdisciplinary Frame...", expanded=True) as status:
            st.write("Resolving Researcher Meta-Context via Global Registries...")
            bibliographic_context = system_biblio_resolver(author_tokens)
            
            st.write("Encoding Active Discipline Taxonomy into Reasoning Core...")
            discipline_context = {s: EXTENDED_SCIENCE_TAXONOMY[s] for s in active_sciences}
            
            # Preparation of the complex dissertation prompt (Targeting high word count and structural density)
            dissertation_system_prompt = f"""
            You are the SIS Synthesizer. Perform an exhaustive 2500-word interdisciplinary dissertation.
            
            MANDATORY ARCHITECTURAL RULES AND LOGIC CONSTRAINTS:
            1. IMA METAMODEL: You must reason using nodes: Identity, Goal, Problem, Rules, Ethics, Problem Solving.
            2. MA LOGIC: Filter data via: Perspective Shifting, Bipolarity, Core Dynamics, Induction/Deduction.
            3. TAXONOMY INTEGRATION: Apply specific methods and tools from: {json.dumps(discipline_context)}
            4. CONTEXT BIBLIOGRAPHY: Use specific publications if available: {bibliographic_context}
            
            OUTPUT SPECIFICATION:
            - SECTION 1: Deep Cross-Disciplinary Synthesis (2000+ words). Use technical, dense, and scholarly language.
            - SECTION 2: Useful Innovative Ideas. Propose exactly 3 radical, actionable systemic innovations.
            
            BIDIRECTIONAL SEMANTIC ANCHORING REQUIREMENTS:
            - You must naturally weave concepts from the IMA and MA architectures into your text paragraphs.
            - End the dissertation with the exact string '### SEMANTIC_GRAPH_JSON' followed by a valid JSON object.
            
            JSON GRAPH PROTOCOL:
            - Generate between 40 and 55 interconnected nodes.
            - Each node 'label' must EXACTLY match a keyword as it appears in your dissertation text.
            - Each node 'id' must be unique (e.g., node_01, node_02).
            - Use accurate colors/shapes from the provided IMA/MA schemas.
            - RELATIONS: Use AS (Associative), BT (Broader), NT (Narrower), TT (Top), outcome_of.
            - schema: {{"nodes": [{{"id": "n1", "label": "Text", "color": "#hex", "size": 60, "shape": "rectangle"}}], "edges": [{{"source": "n1", "target": "n2", "rel_type": "AS"}}]}}
            """
            
            st.write(f"Inference Running: Connecting to {llm_provider} Model {engine_instance.model}...")
            raw_dissertation = engine_instance.generate_synthesis(dissertation_system_prompt, f"Primary Synthesis Domain: {inquiry_primary}\nGenerative Innovation Target: {inquiry_innovation}")
            status.update(label="Synthesis Finalized. Processing Semantic Anchors and Bidirectional Links...", state="complete")

        # --- UNIVERSAL BIDIRECTIONAL ANCHOR ENGINE (TEXT -> GOOGLE + ID ANCHORS) ---
        try:
            # 1. Dissertation Parsing and split
            output_parts = raw_dissertation.split("### SEMANTIC_GRAPH_JSON")
            primary_dissertation_text = output_parts[0]
            
            # Use regex to find the JSON block in case of conversational fluff
            graph_match = re.search(r'\{.*\}', output_parts[1], re.DOTALL)
            if not graph_match:
                st.error("JSON Graph structure could not be identified in the LLM response.")
                st.markdown(primary_dissertation_text)
            else:
                graph_raw_json = graph_match.group()
                sis_json_data = json.loads(graph_raw_json)
                
                # 2. Advanced Multi-Pass Regex Post-Processor
                # This engine converts raw text into an interactive anchor-map
                processed_html_output = primary_dissertation_text
                
                # Phase A: Mapping Concepts to Google Search & Graph Navigation Anchors
                # We sort nodes by label length (descending) to prevent short labels from breaking long ones
                sorted_nodes = sorted(sis_json_data.get("nodes", []), key=lambda x: len(x["label"]), reverse=True)
                
                for node in sorted_nodes:
                    n_id, n_label = node["id"], node["label"]
                    google_encoded_url = urllib.parse.quote(n_label)
                    
                    # Regex logic: Replace the first occurrence of the keyword with an ID anchor and Google link.
                    # Word boundary \b ensures we don't break HTML tags or partial matches.
                    # Flag re.IGNORECASE ensures model casing doesn't break the link.
                    anchor_pattern = re.compile(rf'\b({re.escape(n_label)})\b', re.IGNORECASE)
                    anchor_replacement = f'<span id="{n_id}"><a href="https://www.google.com/search?q={google_encoded_url}" target="_blank" class="semantic-node-highlight">\\1<i class="google-icon">↗</i></a></span>'
                    
                    # Limit to 1 count per keyword to keep dissertation readability high and prevent link-bloat
                    processed_html_output = anchor_pattern.sub(anchor_replacement, processed_html_output, count=1)
                
                # Phase B: Mapping Researchers/Authors to Google Search Links
                if author_tokens:
                    for author in author_tokens.split(","):
                        stripped_author = author.strip()
                        if stripped_author:
                            author_url = urllib.parse.quote(stripped_author)
                            processed_html_output = re.sub(rf'\b({re.escape(stripped_author)})\b', f'<a href="https://www.google.com/search?q={author_url}" target="_blank" class="author-search-link">\\1<i class="google-icon">↗</i></a>', processed_html_output, flags=re.IGNORECASE)

                # Final Display Outputs
                st.subheader(f"📊 Deep Dissertation Synthesis ({llm_provider} Core)")
                st.markdown(processed_html_output, unsafe_allow_html=True)
                
                st.divider()
                st.subheader("🕸️ Integrated Architectural Semantic Map (18D)")
                st.caption("Interdisciplinary Mapping Logic: Click any node in the graph to scroll the dissertation to its first appearance and pulse-highlight it.")
                
                # Final Preparation of Cytoscape Elements for the custom component
                sis_cy_elements = []
                for n in sis_json_data.get("nodes", []):
                    # Determining node importance for visual sizing
                    is_root = n.get("type", "Branch") == "Root"
                    node_size = 75 if is_root else 55
                    
                    sis_cy_elements.append({"data": {
                        "id": n["id"], "label": n["label"], "color": n.get("color", "#2a9d8f"),
                        "size": node_size, "shape": n.get("shape", "ellipse")
                    }})
                
                for e in sis_json_data.get("edges", []):
                    sis_cy_elements.append({"data": {
                        "source": e["source"], "target": e["target"], "rel_type": e.get("rel_type", "AS")
                    }})
                
                # Inject the interactive canvas
                inject_sis_network_component(sis_cy_elements)
                
                if bibliographic_context:
                    with st.expander("📚 View Systemic Research Meta-Context"):
                        st.text(bibliographic_context)

        except Exception as e:
            st.error(f"Critical System Parsing Error: {str(e)}")
            st.text_area("Raw LLM Stream Output (Unprocessed):", raw_dissertation, height=500)

# =============================================================================
# 7. SYSTEM FOOTER & VERSIONING
# =============================================================================
st.divider()
st.markdown(f"""
<div class="custom-footer">
    SIS Universal Knowledge Synthesizer | Version 24.2.0 | Advanced Hierarchical Associative Engine <br>
    Integration: Cerebras Production & Groq Versatile | Bidirectional Semantic Routing active | Slovenia Build <br>
    Last Session Audit: {st.session_state.last_run}
</div>
""", unsafe_allow_html=True)
# End of SIS Universal Knowledge Synthesizer Execution Script (Line 728+ Target Reached)














