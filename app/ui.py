import streamlit as st
import os
import shutil
import base64
import hashlib
from core.summarizer import summarize_video
from app.theme import inject_theme_css, get_theme_colors
from core.gpu_memory import init_gpu_memory

st.set_page_config(
    page_title="نظام تلخيص فيديوهات المراقبة",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def get_base64_file(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def compute_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def clear_outputs_and_cache():
    """Clear results folder and cache database."""
    results_dir = "results"
    cache_path = "data/summary_cache.json"
    input_dir = "data/inputs"

    cleared = []

    if os.path.exists(results_dir):
        for item in os.listdir(results_dir):
            item_path = os.path.join(results_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                cleared.append(item_path)
            except Exception:
                pass

    if os.path.exists(input_dir):
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            try:
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.mp4', '.avi', '.mov', '.mkv']:
                        os.remove(item_path)
                        cleared.append(item_path)
            except Exception:
                pass

    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            cleared.append(cache_path)
        except Exception:
            pass

    return cleared

    if os.path.exists(results_dir):
        for item in os.listdir(results_dir):
            item_path = os.path.join(results_dir, item)
            if os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path, onerror=handle_remove_error)
                    cleared.append(item_path)
                except Exception as e:
                    errors.append((item_path, str(e)))
            elif os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                    cleared.append(item_path)
                except Exception as e:
                    errors.append((item_path, str(e)))

    if os.path.exists(input_dir):
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            if os.path.isfile(item_path) and item.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                try:
                    os.remove(item_path)
                    cleared.append(item_path)
                except Exception as e:
                    errors.append((item_path, str(e)))

    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            cleared.append(cache_path)
        except Exception as e:
            errors.append((cache_path, str(e)))

    return cleared


def main():
    init_gpu_memory()

    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if "result" not in st.session_state:
        st.session_state.result = None
    if "processing" not in st.session_state:
        st.session_state.processing = False

    theme = st.session_state.theme
    st.markdown(inject_theme_css(theme), unsafe_allow_html=True)

    new_theme = "light" if theme == "dark" else "dark"
    theme_icon = "☀️" if theme == "dark" else "🌙"

    st.markdown(f"""
    <div class="top-nav">
        <div class="nav-brand">
            <img src="data:image/svg+xml;base64,{get_base64_file('assets/logo.ai.svg') or ''}" class="nav-logo" onerror="this.style.display='none'">
            <div>
                <div class="nav-title">نظام تلخيص فيديوهات المراقبة</div>
                <div class="nav-subtitle">الجمهورية العربية السورية</div>
            </div>
        </div>
        <div class="nav-controls">
            <button class="theme-btn" onclick="document.getElementById('themeToggleBtn').click()">{theme_icon}</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.button("تبديل النمط", key="theme_toggle_btn", help="تبديل الوضع")

    if st.button("🗑️ مسح ذاكرة التخزين المؤقت", key="clear_cache_btn"):
        try:
            cleared = clear_outputs_and_cache()
            st.success(f"✓ تم مسح {len(cleared)} عنصر")
        except Exception as e:
            st.error(f"خطأ: {e}")

    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">تحليل ذكي لـ <span>فيديوهات المراقبة</span></h1>
        <p class="hero-subtitle">تقنية متقدمة لاستخراج اللحظات المهمة من ساعات التسجيل</p>
    </div>
    """, unsafe_allow_html=True)

    col_upload, col_result = st.columns([1, 1.3], gap="large")

    with col_upload:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="card-header">
            <div class="card-icon">📤</div>
            <div class="card-title">رفع الفيديو للتحليل</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "اختر فيديو للمراقبة",
            type=["mp4", "avi", "mov", "mkv"],
            help="MP4, AVI, MOV, MKV",
            key="video_uploader"
        )

        if uploaded_file:
            save_path = os.path.join("data/inputs", uploaded_file.name)
            os.makedirs("data/inputs", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            file_hash = compute_file_hash(save_path)
            file_size_mb = uploaded_file.size / (1024 * 1024)

            st.markdown(f"""
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">الاسم</div>
                    <div class="info-value">{uploaded_file.name[:20]}{'...' if len(uploaded_file.name) > 20 else ''}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">الحجم</div>
                    <div class="info-value">{file_size_mb:.1f} MB</div>
                </div>
                <div class="info-item">
                    <div class="info-label">البصمة</div>
                    <div class="info-value">{file_hash[:8]}...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="video-container">', unsafe_allow_html=True)
            st.video(uploaded_file)
            st.markdown('</div>', unsafe_allow_html=True)

            btn = st.button("🚀 بدء التحليل الذكي", use_container_width=True, key="process_btn")
            if btn:
                try:
                    st.session_state.processing = True
                    with st.status("جاري التحليل...", expanded=True) as status:
                        status.update(label="جاري تحميل الفيديو...", state="running")
                        st.progress(10, text="تحميل الفيديو")
                        
                        status.update(label="جاري استخراج الإطارات...", state="running")
                        st.progress(30, text="استخراج الإطارات")
                        
                        status.update(label="جاري الكشف عن الحركة...", state="running")
                        st.progress(50, text="الكشف عن الحركة")
                        
                        status.update(label="جاري بناء المقاطع...", state="running")
                        st.progress(70, text="بناء المقاطع")
                        
                        status.update(label="جاري إنشاء الفيديو...", state="running")
                        st.progress(90, text="إنشاء الفيديو")
                        
                        result = summarize_video(save_path)
                        
                        status.update(label="اكتمل التحليل!", state="complete")
                        st.progress(100, text="اكتمل")
                        
                        st.session_state["result"] = result
                        st.session_state.processing = False
                except Exception as e:
                    st.session_state.processing = False
                    st.error(f"❌ خطأ: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="card-header">
            <div class="card-icon">🎬</div>
            <div class="card-title">نتائج الملخص</div>
        </div>
        """, unsafe_allow_html=True)

        result = st.session_state.get("result")

        if result and os.path.exists(result.get("segments_video", "")):
            st.markdown('<div class="video-container" style="width: 100%;">', unsafe_allow_html=True)
            st.video(result["segments_video"])
            st.markdown('</div>', unsafe_allow_html=True)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                with open(result["segments_video"], "rb") as f:
                    st.download_button(
                        label="📥 تحميل الفيديو",
                        data=f,
                        file_name="Summary.mp4",
                        use_container_width=True
                    )
            with col_dl2:
                frames_path = result.get("frames_video", "")
                if os.path.exists(frames_path):
                    with open(frames_path, "rb") as f:
                        st.download_button(
                            label="🖼️ تحميل الإطارات",
                            data=f,
                            file_name="Frames.mp4",
                            use_container_width=True
                        )
                else:
                    st.info("لا توجد إطارات")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">📁</div>
                <div class="empty-title">في انتظار الفيديو</div>
                <div class="empty-description">قم برفع فيديو المراقبة ليظهر الملخص هنا</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown('<div class="footer-brand">🇸🇾 الجمهورية العربية السورية</div>', unsafe_allow_html=True)
    st.markdown('<div style="opacity: 0.7;">جميع الحقوق محفوظة © 2025</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()