import hmac
import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()


def get_secret_password() -> str | None:
    """Safely retrieves the password from .env (locally) or Streamlit secrets (cloud)."""
    pwd = os.getenv("APP_ADMIN_PASSWORD")
    if pwd:
        return pwd

    try:
        if "APP_ADMIN_PASSWORD" in st.secrets:
            return st.secrets["APP_ADMIN_PASSWORD"]
    except Exception:
        pass

    return None


def check_password() -> bool:
    """Returns True if the user has authenticated."""
    if st.session_state.get("authenticated", False):
        return True

    # --- CLEANUP TRAP: Purge 3D background canvas if user is logged out ---
    components.html(
        """
        <script>
        const pDoc = window.parent.document;
        const canvas = pDoc.getElementById("canvas-3d-bg");
        if (canvas) canvas.remove();
        const styles = pDoc.getElementById("3d-bg-styles");
        if (styles) styles.remove();
        </script>
        """,
        height=0,
        width=0,
    )

    correct_password = get_secret_password()

    if not correct_password:
        st.error(
            "⚠️ `APP_ADMIN_PASSWORD` is not configured!\n\n"
            "Add `APP_ADMIN_PASSWORD=your_password_here` to your `.env` file (locally) "
            "or in Streamlit Cloud Secrets."
        )
        st.stop()

    # Center-aligned Login Card
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write(" ")
        st.write(" ")
        with st.container(border=True):
            st.subheader("🔒 Personal Access Gate")
            st.caption("This system is restricted for personal administrative use.")

            password_attempt = st.text_input("Enter Passcode", type="password", key="password_input")
            login_btn = st.button("Authenticate", type="primary", use_container_width=True)

            if login_btn:
                if hmac.compare_digest(password_attempt, correct_password):
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid passcode.")

    return False


def require_auth():
    """Halts execution if the user is not authenticated."""
    if not check_password():
        st.stop()


def render_logout():
    """Adds a logout action in the sidebar."""
    if st.session_state.get("authenticated", False):
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()