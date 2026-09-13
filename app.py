import asyncio
import json
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.auth import require_auth, render_logout  # <--- Import auth functions
from src.graph import build_lead_graph
from src.models import AgentState

load_dotenv()

# Page Setup must remain the first Streamlit command
st.set_page_config(
    page_title="LeadScope AI | Autonomous Intelligence Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# 🔒 ENFORCE AUTHENTICATION (Halts here if not logged in)
# -------------------------------------------------------------
require_auth()
# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚡ LeadScope AI")
    st.write("Autonomous account research engine...")
    
    # Existing sidebar items ...
    st.divider()
    render_logout()  # <--- Renders the logout button
# --- 1. Three.js 3D Interactive WebGL Background ---
THREE_JS_BACKGROUND = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {
    const pDoc = window.parent.document;
    if (pDoc.getElementById("canvas-3d-bg")) return; // Prevent duplicate canvas on reruns

    // Create fixed background canvas
    const canvas = pDoc.createElement("canvas");
    canvas.id = "canvas-3d-bg";
    canvas.style.position = "fixed";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.width = "100vw";
    canvas.style.height = "100vh";
    canvas.style.zIndex = "0";
    canvas.style.pointerEvents = "none";
    canvas.style.opacity = "0.55";
    pDoc.body.prepend(canvas);

    // Apply dark glassmorphism to Streamlit parent DOM
    const style = pDoc.createElement("style");
    style.id = "3d-bg-styles";
    style.innerHTML = `
        .stApp {
            background: transparent !important;
        }
        .main .block-container {
            position: relative;
            z-index: 1;
        }
        section[data-testid="stSidebar"] {
            background-color: rgba(10, 14, 23, 0.85) !important;
            backdrop-filter: blur(14px);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
    `;
    pDoc.head.appendChild(style);

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.parent.innerWidth / window.parent.innerHeight, 0.1, 1000);
    camera.position.z = 240;

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(window.parent.innerWidth, window.parent.innerHeight);
    renderer.setPixelRatio(Math.min(window.parent.devicePixelRatio, 2));

    // Outer Particle Globe
    const count = 650;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const radius = 150;

    for (let i = 0; i < count; i++) {
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        const r = radius * (0.85 + 0.3 * Math.random());

        positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = r * Math.cos(phi);
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
        size: 2.6,
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending
    });
    const particleMesh = new THREE.Points(geometry, material);
    scene.add(particleMesh);

    // Inner Geometric Wireframe (Autonomous Core)
    const icoGeo = new THREE.IcosahedronGeometry(85, 2);
    const icoMat = new THREE.MeshBasicMaterial({
        color: 0x0284c7,
        wireframe: true,
        transparent: true,
        opacity: 0.18
    });
    const icoMesh = new THREE.Mesh(icoGeo, icoMat);
    scene.add(icoMesh);

    // Mouse Parallax
    let mouseX = 0, mouseY = 0;
    pDoc.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX - window.parent.innerWidth / 2) * 0.04;
        mouseY = (e.clientY - window.parent.innerHeight / 2) * 0.04;
    });

    window.parent.addEventListener('resize', () => {
        camera.aspect = window.parent.innerWidth / window.parent.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.parent.innerWidth, window.parent.innerHeight);
    });

    function renderLoop() {
        requestAnimationFrame(renderLoop);
        particleMesh.rotation.y += 0.0016;
        particleMesh.rotation.x += 0.0006;
        icoMesh.rotation.y -= 0.0012;
        icoMesh.rotation.x -= 0.0005;

        camera.position.x += (mouseX - camera.position.x) * 0.03;
        camera.position.y += (-mouseY - camera.position.y) * 0.03;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }
    renderLoop();
})();
</script>
"""

components.html(THREE_JS_BACKGROUND, height=0, width=0)

# --- 2. Custom Glassmorphic Styling & Mobile Responsiveness ---
st.markdown(
    """
    <style>
    /* Metric Cards with Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
        padding: 14px 20px;
    }
    
    /* Leadership Card */
    .leader-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .leader-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    
    .linkedin-btn {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #0284c7, #0369a1);
        color: white !important;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 8px;
    }
    
    .badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
    }

    /* --- MOBILE RESPONSIVENESS MEDIA QUERY --- */
    @media (max-width: 768px) {
        /* Stack all columns vertically on mobile */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            min-width: 100% !important;
            margin-bottom: 12px;
        }
        /* Make buttons full width for easy tapping */
        .stButton button {
            width: 100% !important;
        }
        /* Reduce padding on mobile containers */
        .leader-card {
            padding: 12px;
        }
        /* Fix text input sizing */
        .stTextInput input {
            width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_agent_pipeline(domain: str) -> dict:
    """Executes the stateful LangGraph pipeline inside an isolated event loop."""
    clean_domain = domain.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    graph = build_lead_graph()

    initial_state: AgentState = {
        "domain": clean_domain,
        "crawled_urls": [],
        "raw_pages": {},
        "cleaned_context": "",
        "intelligence": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "status": "pending",
        "error_message": None,
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(graph.ainvoke(initial_state))
    finally:
        loop.close()


# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚡ LeadScope AI")
    st.write(
        "Autonomous account research engine. Transforms raw web footprints into verified "
        "B2B intelligence dossiers with zero manual prospecting."
    )

    st.markdown(
        """
        <span class="badge">Playwright</span>
        <span class="badge">LangGraph</span>
        <span class="badge">GPT-4o Mini</span>
        <span class="badge">Serper Google</span>
        <span class="badge">Pydantic v2</span>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 🔄 Graph Execution Stages")
    with st.expander("1. Headless Subpage Crawler", expanded=False):
        st.caption("Renders JS SPAs via Playwright and identifies paths like `/about`, `/team`, `/company`, `/pricing`.")

    with st.expander("2. Token Sanitization", expanded=False):
        st.caption("Strips boilerplate, scripts, SVGs, and cookie modals, cutting token consumption by ~85%.")

    with st.expander("3. OpenAI Structured Output", expanded=False):
        st.caption("Enforces strict Pydantic parsing for ICP, company summaries, and contact channels.")

    with st.expander("4. External Search Agent", expanded=False):
        st.caption("Conditionally queries Google via Serper to surface verified founder LinkedIn profiles if absent on-site.")

    st.divider()
    st.caption("Autonomous Agent Engine | Python 3.13")


# --- Main Dashboard Hero ---
st.title("Autonomous Lead & Account Intelligence")
st.markdown(
    "Synthesize any company domain into an actionable intelligence dossier with automated "
    "**ICP extraction**, **public contact discovery**, and **verified executive resolution**."
)

st.write("##### 🚀 Click an enterprise to inspect live:")

# Quick Showcase Row
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    if st.button("📦 **Postman**\n\n*Enterprise API Platform*", use_container_width=True):
        st.session_state["active_domain"] = "postman.com"
        st.session_state["trigger_search"] = True

with col_s2:
    if st.button("⚡ **Supabase**\n\n*Open Source Firebase Alternative*", use_container_width=True):
        st.session_state["active_domain"] = "supabase.com"
        st.session_state["trigger_search"] = True

with col_s3:
    if st.button("🎙️ **Vapi**\n\n*Voice AI Platform for Developers*", use_container_width=True):
        st.session_state["active_domain"] = "vapi.ai"
        st.session_state["trigger_search"] = True

st.write(" ")

# Custom Input Bar
col_in, col_action = st.columns([4, 1])
current_domain = st.session_state.get("active_domain", "postman.com")

with col_in:
    target_input = st.text_input(
        "Or enter any custom company domain:",
        value=current_domain,
        placeholder="e.g. stripe.com, vercel.com, linear.app",
    )

with col_action:
    st.write(" ")
    st.write(" ")
    run_btn = st.button("Enrich Domain", type="primary", use_container_width=True)

# Trigger Condition
should_run = run_btn or st.session_state.get("trigger_search", False)

if should_run and target_input:
    st.session_state["trigger_search"] = False
    domain_to_enrich = target_input.strip()

    st.divider()

    with st.status(f"🤖 Agent executing state machine on `{domain_to_enrich}`...", expanded=True) as status_box:
        st.write("🌐 Launching headless browser & traversing discovered subpages...")
        state_result = run_agent_pipeline(domain_to_enrich)

        if state_result.get("status") == "failed":
            status_box.update(label=f"❌ Enrichment failed for {domain_to_enrich}", state="error", expanded=True)
            st.error(f"Execution Error: {state_result.get('error_message')}")
        else:
            status_box.update(label=f"✅ Intelligence dossier compiled for {domain_to_enrich}", state="complete", expanded=False)

            intel = state_result.get("intelligence") or {}

            # --- Telemetry Metric Strip ---
            st.markdown("### 📊 Pipeline Telemetry & Cost Accounting")
            m1, m2, m3, m4 = st.columns(4)

            confidence = intel.get("data_confidence_score", 0.0)
            m1.metric("Data Confidence", f"{confidence * 100:.0f}%")
            m2.metric("Subpages Crawled", len(state_result.get("crawled_urls", [])))
            m3.metric("Tokens Consumed", f"{state_result.get('total_tokens', 0):,}")
            m4.metric("Pipeline Cost", f"${state_result.get('estimated_cost_usd', 0.0):.5f}")

            st.write(" ")

            # --- Dossier Tabs ---
            tab_dossier, tab_team, tab_sources = st.tabs([
                "📋 Executive Dossier & ICP",
                "👥 Leadership & Contact Channels",
                "🔍 Audit Trail & JSON"
            ])

            with tab_dossier:
                col_sum, col_icp = st.columns(2)
                with col_sum:
                    st.markdown("#### 🏢 Company Overview")
                    st.info(intel.get("company_overview", "No summary available."))
                with col_icp:
                    st.markdown("#### 🎯 Target Audience / ICP")
                    st.success(intel.get("target_audience", "No ICP available."))

            with tab_team:
                col_execs, col_comms = st.columns([3, 2])

                with col_execs:
                    st.markdown("#### 👔 Executive Leadership")
                    leadership = intel.get("key_leadership", [])
                    if leadership:
                        for member in leadership:
                            name = member.get("name", "Unknown")
                            role = member.get("role", "Executive")
                            url = member.get("linkedin_url")

                            st.markdown(
                                f"""
                                <div class="leader-card">
                                    <h4 style="margin: 0 0 4px 0; color: #f8fafc;">{name}</h4>
                                    <p style="margin: 0 0 8px 0; color: #94a3b8; font-size: 0.9rem;">{role}</p>
                                    {f'<a href="{url}" target="_blank" class="linkedin-btn">🔗 Verified LinkedIn Profile</a>' if url else '<span style="font-size:0.8rem; color:#64748b;">No LinkedIn profile matched</span>'}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No key leadership team profiles detected.")

                with col_comms:
                    st.markdown("#### 📬 Public Contact Points")
                    emails = intel.get("contact_points", [])
                    if emails:
                        for email in emails:
                            st.code(email, language="text")
                    else:
                        st.caption("No public contact emails found.")

            with tab_sources:
                st.markdown("#### 🌐 Crawled Source URLs")
                for u in state_result.get("crawled_urls", []):
                    st.markdown(f"- [{u}]({u})")

                st.markdown("#### 📄 Complete Intelligence JSON")
                json_data = json.dumps(state_result, indent=2, ensure_ascii=False)
                st.code(json_data, language="json")

                st.download_button(
                    label="💾 Download Dossier (.JSON)",
                    data=json_data,
                    file_name=f"{domain_to_enrich}_intelligence.json",
                    mime="application/json",
                    use_container_width=True,
                )