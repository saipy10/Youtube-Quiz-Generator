"""
UI styles, theme settings, and helper components for YouTube Quiz Generator.
"""

CUSTOM_CSS = """
/* Modern Dark Glassmorphism Theme */
body, .gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

.main-header {
    text-align: center;
    padding: 1.5rem 1rem;
    background: linear-gradient(135deg, #1e1e2f 0%, #161622 100%);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(90deg, #ff4b4b, #ff8533, #ff4b4b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

.main-header p {
    color: #9ca3af;
    font-size: 0.95rem;
    margin-top: 0.5rem;
    margin-bottom: 0;
}

.step-card {
    background: #1e1e28;
    border: 1px solid #2d2d3d;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.step-card h3 {
    margin-top: 0;
    font-size: 1.15rem;
    color: #f3f4f6;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-success {
    background-color: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-error {
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.btn-primary-action {
    background: linear-gradient(135deg, #e50914 0%, #b81d24 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(229, 9, 20, 0.4) !important;
    transition: transform 0.15s ease !important;
}

.btn-primary-action:hover {
    transform: translateY(-1px) !important;
}

.btn-secondary-action {
    background: #374151 !important;
    color: #f9fafb !important;
    border: 1px solid #4b5563 !important;
}

.btn-publish {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4) !important;
}

.validation-box {
    border-radius: 8px;
    padding: 1rem;
    background: #181822;
    border: 1px solid #2e2e40;
    font-size: 0.95rem;
}
"""


def format_video_markdown(video_info: dict | None) -> str:
    """Formats selected video info for rich display."""
    if not video_info or not video_info.get("id"):
        return "*No video selected. Click 'Fetch Latest 10 Videos' to begin.*"

    title = video_info.get("title", "Unknown Title")
    vid = video_info.get("id", "")
    url = video_info.get("url", f"https://www.youtube.com/watch?v={vid}")
    pub_date = video_info.get("published_at", "")[:10]
    thumb = video_info.get("thumbnail_url", "")

    thumb_html = f'<img src="{thumb}" style="width: 140px; border-radius: 6px; float: left; margin-right: 15px; margin-bottom: 10px;" />' if thumb else ""

    return f"""
<div style="overflow: hidden; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
    {thumb_html}
    <div style="overflow: hidden;">
        <h4 style="margin: 0 0 6px 0; color: #fff;">{title}</h4>
        <p style="margin: 0; font-size: 0.85rem; color: #9ca3af;">
            <b>ID:</b> <code>{vid}</code> | <b>Published:</b> {pub_date or 'N/A'}<br>
            <a href="{url}" target="_blank" style="color: #60a5fa; text-decoration: underline;">Watch on YouTube ↗</a>
        </p>
    </div>
</div>
"""


def format_approved_quiz_card(quiz_dict: dict, channel_url: str) -> str:
    """Formats the approved quiz into a ready-to-copy card with direct link to community posts."""
    q = quiz_dict.get("question", "")
    opts = quiz_dict.get("options", ["", "", "", ""])
    correct = quiz_dict.get("correct_answer", 0)
    exp = quiz_dict.get("explanation", "")
    labels = ["A", "B", "C", "D"]

    options_html = ""
    for i, opt in enumerate(opts):
        is_corr = (i == correct)
        badge = '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-left: 8px;">✓ CORRECT</span>' if is_corr else ""
        border_style = "border: 1px solid #10b981; background: rgba(16, 185, 129, 0.08);" if is_corr else "border: 1px solid #374151; background: #1e1e28;"
        options_html += f"""
        <div style="padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; {border_style}">
            <b>Option {labels[i]}:</b> {opt} {badge}
        </div>
        """

    return f"""
<div style="background: #161622; border: 1px solid #10b981; border-radius: 10px; padding: 16px; margin-top: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
        <span style="color: #10b981; font-weight: 700; font-size: 1.1rem;">✓ Quiz Approved & Ready for YouTube Community!</span>
        <a href="{channel_url}" target="_blank" style="background: #e50914; color: white; text-decoration: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 0.9rem;">Open Your Community Tab ↗</a>
    </div>
    
    <div style="margin-bottom: 12px;">
        <div style="color: #9ca3af; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;">QUESTION:</div>
        <div style="background: #1e1e28; padding: 10px; border-radius: 6px; font-size: 1rem; color: #fff; border: 1px solid #374151;">{q}</div>
    </div>

    <div style="margin-bottom: 12px;">
        <div style="color: #9ca3af; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;">OPTIONS:</div>
        {options_html}
    </div>

    <div>
        <div style="color: #9ca3af; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;">EXPLANATION:</div>
        <div style="background: #1e1e28; padding: 10px; border-radius: 6px; font-size: 0.95rem; color: #e5e7eb; border: 1px solid #374151;">{exp}</div>
    </div>
</div>
"""

