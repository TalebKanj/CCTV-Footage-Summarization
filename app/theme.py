import streamlit as st
import os


SYRIAN_THEME = {
    "dark": {
        "background": "#002623",
        "card_bg": "#111922",
        "surface": "#1a2332",
        "primary": "#CE1126",
        "primary_hover": "#B9A779",
        "text_primary": "#E8E6E3",
        "text_secondary": "#9ca3af",
        "border": "#988561",
    },
    "light": {
        "background": "#f8f9fa",
        "card_bg": "#ffffff",
        "surface": "#f1f3f5",
        "primary": "#CE1126",
        "primary_hover": "#B9A779",
        "text_primary": "#1a1d21",
        "text_secondary": "#6b7280",
        "border": "#988561",
    }
}


def get_current_theme() -> str:
    """Get current theme from Streamlit context."""
    try:
        theme_config = st.context.theme
        return theme_config.get("base", "dark")
    except Exception:
        return "dark"


def get_theme_colors(theme: str = None) -> dict:
    """Get theme colors dict."""
    if theme is None:
        theme = get_current_theme()
    return SYRIAN_THEME.get(theme, SYRIAN_THEME["dark"])


def get_css_variables(theme: str = None) -> str:
    """Generate CSS variables for current theme."""
    t = get_theme_colors(theme)
    return f"""
        --background-color: {t['background']};
        --card-bg: {t['card_bg']};
        --surface-color: {t['surface']};
        --primary-color: {t['primary']};
        --primary-color-hover: {t['primary_hover']};
        --text-primary: {t['text_primary']};
        --text-secondary: {t['text_secondary']};
        --border-color: {t['border']};
    """


def load_css_file(css_file: str) -> str:
    """Load CSS file content."""
    css_path = os.path.join(os.path.dirname(__file__), css_file)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def inject_theme_css(theme: str = None) -> str:
    """Inject theme CSS with CSS variables - responsive, no scrollbars."""
    t = get_theme_colors(theme)
    css_content = load_css_file("styles.css")

    return f"""
    <style>
    :root {{
        {get_css_variables(theme)}
    }}
    
    /* Responsive - no scrollbars */
    html, body {{
        direction: rtl;
        background-color: {t['background']};
        color: {t['text_primary']};
        margin: 0;
        padding: 0;
        overflow-x: hidden !important;
        height: 100%;
    }}
    
    body {{
        overflow: hidden !important;
    }}
    
    /* Hide scrollbars */
    ::-webkit-scrollbar {{
        width: 0px !important;
        height: 0px !important;
        display: none !important;
    }}
    
    * {{
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }}
    
    /* Base styles - sticky header */
    header {{visibility: hidden !important; height: 0px !important;}}
    #MainMenu {{visibility: hidden !important;}}
    
    .main {{
        padding-top: 0 !important;
        overflow: hidden !important;
    }}
    
    .main .block-container {{
        padding: 1rem !important;
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        overflow: hidden !important;
    }}
    
    [data-testid="stSidebar"] {{display: none !important;}}
    
    div[data-testid="stApp"] {{
        background-color: {t['background']};
        overflow: hidden !important;
    }}
    
    /* Sticky Top Navigation */
    .top-nav {{
        position: fixed !important;
        top: 0 !important;
        right: 0 !important;
        left: 0 !important;
        z-index: 9999 !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 0.6rem 1.5rem !important;
        background: {t['card_bg']} !important;
        border-bottom: 1px solid {t['border']} !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
    }}
    
    .nav-brand {{
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }}
    
    .nav-logo {{
        height: 36px !important;
        filter: drop-shadow(0 2px 6px rgba(201, 162, 39, 0.3)) !important;
    }}
    
    .nav-title {{
        color: {t['primary']} !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }}
    
    .nav-subtitle {{
        color: {t['text_secondary']} !important;
        font-size: 0.6rem !important;
    }}
    
    .nav-controls {{
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
    }}
    
    .theme-btn {{
        background: {t['surface']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        cursor: pointer !important;
        font-size: 1.2rem !important;
        color: {t['text_primary']} !important;
        transition: all 0.2s ease !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .theme-btn:hover {{
        border-color: {t['primary']} !important;
        background: {t['primary']} !important;
        color: {t['background']} !important;
    }}
    
    /* Content wrapper */
    .content-wrapper {{
        max-width: 100% !important;
        margin: 4rem auto 0 !important;
        padding: 0 1rem !important;
        overflow: hidden !important;
    }}
    
    /* Hero Section */
    .hero-section {{
        text-align: center !important;
        padding: 0.5rem 1rem !important;
    }}
    
    .hero-title {{
        color: {t['text_primary']} !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        margin: 0 0 0.3rem !important;
    }}
    
    .hero-title span {{
        color: {t['primary']} !important;
    }}
    
    .hero-subtitle {{
        color: {t['text_secondary']} !important;
        font-size: 0.8rem !important;
        max-width: 500px !important;
        margin: 0 auto !important;
        line-height: 1.4 !important;
    }}
    
    /* Cards */
    .section-card {{
        background: {t['card_bg']} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid {t['border']} !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
        overflow: hidden !important;
    }}
    
    .card-header {{
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        margin-bottom: 0.8rem !important;
        padding-bottom: 0.6rem !important;
        border-bottom: 1px solid {t['border']} !important;
    }}
    
    .card-icon {{
        width: 32px !important;
        height: 32px !important;
        border-radius: 8px !important;
        background: linear-gradient(135deg, {t['primary']} 0%, {t['primary_hover']} 100%) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 0.9rem !important;
    }}
    
    .card-title {{
        color: {t['text_primary']} !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
    }}
    
    /* Info Grid */
    .info-grid {{
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 0.4rem !important;
        margin: 0.5rem 0 !important;
    }}
    
    .info-item {{
        background: {t['surface']} !important;
        border-radius: 6px !important;
        padding: 0.4rem !important;
        text-align: center !important;
        border: 1px solid {t['border']} !important;
    }}
    
    .info-label {{
        color: {t['text_secondary']} !important;
        font-size: 0.55rem !important;
        text-transform: uppercase !important;
    }}
    
    .info-value {{
        color: {t['text_primary']} !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
    }}
    
    /* Video Container */
    .video-container {{
        border-radius: 8px !important;
        overflow: hidden !important;
        background: #000 !important;
        margin: 0.5rem 0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }}
    
    .video-container video {{
        width: 100% !important;
        height: auto !important;
        max-height: 400px !important;
    }}
    
    /* Empty State */
    .empty-state {{
        text-align: center !important;
        padding: 2rem 0.5rem !important;
        color: {t['text_secondary']} !important;
    }}
    
    .empty-icon {{
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        opacity: 0.2 !important;
    }}
    
    .empty-title {{
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: {t['text_primary']} !important;
    }}
    
    .empty-description {{
        font-size: 0.75rem !important;
        line-height: 1.3 !important;
    }}
    
    /* Footer */
    .footer {{
        text-align: center !important;
        padding: 0.8rem !important;
        margin-top: 0.8rem !important;
        border-top: 1px solid {t['border']} !important;
        color: {t['text_secondary']} !important;
        font-size: 0.7rem !important;
    }}
    
    .footer-brand {{
        color: {t['primary']} !important;
        font-weight: 600 !important;
    }}
    
    /* Streamlit component overrides */
    .stButton > button {{
        background: linear-gradient(135deg, {t['primary']} 0%, {t['primary_hover']} 100%) !important;
        color: {t['background']} !important;
        border-radius: 7px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(201, 162, 39, 0.2) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(201, 162, 39, 0.3) !important;
    }}
    
    .stDownloadButton > button {{
        background: {t['surface']} !important;
        color: {t['text_primary']} !important;
        border: 2px solid {t['primary']} !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }}
    
    .stDownloadButton > button:hover {{
        background: {t['primary']} !important;
        color: {t['background']} !important;
    }}
    
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {t['primary']} 0%, {t['primary_hover']} 100%) !important;
    }}
    
    .stFileUploader > div > div {{
        background-color: transparent !important;
    }}
    
    [data-testid="stFileUploader"] section {{
        background-color: rgba(5, 66, 57, 0.3) !important;
        border: 2px dashed {t['border']} !important;
        border-radius: 10px !important;
        padding: 1.5rem !important;
    }}
    
    [data-testid="stFileUploader"] section div {{
        color: {t['text_primary']} !important;
    }}
    
    [data-testid="stHorizontalBlock"] > div {{
        padding: 0 4px !important;
    }}
    
    /* Column layout */
    [data-testid="column"] {{
        overflow: hidden !important;
    }}
    
    /* Status */
    .stStatus {{
        background: {t['surface']} !important;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .hero-title {{
            font-size: 1.2rem !important;
        }}
        
        .nav-title {{
            font-size: 0.9rem !important;
        }}
        
        .info-grid {{
            grid-template-columns: 1fr 1fr !important;
        }}
        
        .top-nav {{
            padding: 0.5rem 1rem !important;
        }}
        
        .content-wrapper {{
            margin-top: 3.5rem !important;
        }}
    }}
    
    /* Import external CSS */
    {css_content}
    </style>
    """