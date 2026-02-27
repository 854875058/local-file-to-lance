# -*- coding: utf-8 -*-
"""NiceGUI 蓝白透明卡片风格全局样式 — 增强版"""

GLOBAL_CSS = """
/* ========== 动态渐变背景 ========== */
body {
    background:
        radial-gradient(ellipse 80% 60% at 10% 0%, rgba(37,99,235,0.10) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 95% 15%, rgba(96,165,250,0.09) 0%, transparent 55%),
        radial-gradient(ellipse 70% 55% at 50% 100%, rgba(147,197,253,0.08) 0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 70% 60%, rgba(59,130,246,0.05) 0%, transparent 50%),
        linear-gradient(180deg, #eef4ff 0%, #f0f5ff 40%, #f8faff 100%) !important;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
}

/* ========== 毛玻璃卡片 ========== */
.glass-card {
    background: rgba(255, 255, 255, 0.68);
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.7);
    box-shadow:
        0 4px 24px rgba(37, 99, 235, 0.07),
        0 1px 4px rgba(0,0,0,0.03),
        inset 0 1px 0 rgba(255,255,255,0.6);
    padding: 1.25rem 1.5rem;
    transition: transform 0.25s cubic-bezier(.4,0,.2,1),
                box-shadow 0.25s cubic-bezier(.4,0,.2,1),
                border-color 0.25s ease;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow:
        0 8px 32px rgba(37, 99, 235, 0.12),
        0 2px 8px rgba(0,0,0,0.04),
        inset 0 1px 0 rgba(255,255,255,0.7);
    border-color: rgba(147, 197, 253, 0.5);
}

/* ========== KPI 指标卡片 ========== */
.kpi-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(14px) saturate(1.3);
    -webkit-backdrop-filter: blur(14px) saturate(1.3);
    border-radius: 16px;
    border: 1px solid rgba(37, 99, 235, 0.08);
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.06);
    padding: 1.3rem 1.1rem;
    text-align: center;
    transition: transform 0.25s cubic-bezier(.4,0,.2,1),
                box-shadow 0.25s cubic-bezier(.4,0,.2,1),
                border-color 0.25s ease;
    min-width: 140px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa, #93c5fd);
    opacity: 0;
    transition: opacity 0.25s ease;
}
.kpi-card:hover::before { opacity: 1; }
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 28px rgba(37, 99, 235, 0.14);
    border-color: rgba(59, 130, 246, 0.25);
}
.kpi-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #64748b;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.kpi-sub {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-top: 0.3rem;
}
.kpi-card.primary { border-left: 4px solid #2563eb; }
.kpi-card.primary .kpi-value {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.kpi-card.success { border-left: 4px solid #16a34a; }
.kpi-card.success .kpi-value {
    background: linear-gradient(135deg, #15803d, #22c55e);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* ========== 页面标题 ========== */
.page-header {
    background: linear-gradient(135deg, rgba(255,255,255,0.85), rgba(239,246,255,0.80));
    backdrop-filter: blur(16px) saturate(1.3);
    -webkit-backdrop-filter: blur(16px) saturate(1.3);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.25rem;
    border: 1px solid rgba(147,197,253,0.3);
    box-shadow: 0 2px 12px rgba(37,99,235,0.06);
    position: relative;
    overflow: hidden;
}
.page-header::after {
    content: '';
    position: absolute;
    bottom: 0; left: 2rem; right: 2rem;
    height: 2px;
    background: linear-gradient(90deg, transparent, #3b82f6, #60a5fa, transparent);
    opacity: 0.4;
}
.page-title {
    font-size: 1.85rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
}
.page-subtitle {
    font-size: 0.9rem;
    color: #64748b;
    margin: 0.3rem 0 0 0;
    letter-spacing: 0.02em;
}

/* ========== 分区标题 ========== */
.section-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1e3a5f;
    margin: 1.2rem 0 0.7rem 0;
    padding-bottom: 0.5rem;
    border-bottom: none;
    position: relative;
    display: inline-block;
}
.section-title::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #93c5fd, transparent);
    border-radius: 2px;
}

/* ========== 左侧抽屉 ========== */
.q-drawer {
    background: linear-gradient(180deg,
        rgba(239,246,255,0.95) 0%,
        rgba(255,255,255,0.90) 50%,
        rgba(239,246,255,0.92) 100%) !important;
    backdrop-filter: blur(18px) saturate(1.2) !important;
    -webkit-backdrop-filter: blur(18px) saturate(1.2) !important;
    border-right: 1px solid rgba(147,197,253,0.25) !important;
    box-shadow: 2px 0 16px rgba(37,99,235,0.04) !important;
}

/* 品牌装饰条 */
.drawer-brand {
    padding: 0.2rem 0 0.6rem 0;
    border-bottom: 2px solid transparent;
    border-image: linear-gradient(90deg, #3b82f6, #60a5fa, transparent) 1;
    margin-bottom: 0.5rem;
}

/* ========== Tab 栏 ========== */
.q-tabs {
    background: rgba(255,255,255,0.5) !important;
    border-radius: 14px;
    padding: 4px;
}
.q-tab {
    border-radius: 10px;
    transition: background 0.2s ease, color 0.2s ease;
    font-weight: 500;
    min-height: 40px;
}
.q-tab:hover {
    background: rgba(59,130,246,0.06);
}
.q-tab--active {
    color: #2563eb !important;
    background: rgba(59,130,246,0.10) !important;
    font-weight: 700;
}
.q-tab-panel {
    padding: 1.2rem 0 !important;
    background: transparent !important;
}

/* ========== 搜索结果卡片 ========== */
.result-card {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(12px) saturate(1.2);
    border-radius: 14px;
    border: 1px solid rgba(147,197,253,0.2);
    border-left: 4px solid #3b82f6;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.85rem;
    transition: transform 0.2s cubic-bezier(.4,0,.2,1),
                box-shadow 0.2s cubic-bezier(.4,0,.2,1);
}
.result-card:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 20px rgba(37,99,235,0.10);
}

/* ========== 高亮 ========== */
mark {
    background: linear-gradient(135deg, #bfdbfe, #dbeafe);
    padding: 2px 5px;
    border-radius: 4px;
    box-shadow: 0 1px 2px rgba(37,99,235,0.08);
}

/* ========== 按钮 ========== */
.nicegui-content .q-btn {
    border-radius: 12px;
    text-transform: none;
    font-weight: 600;
    letter-spacing: 0.01em;
    transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.nicegui-content .q-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(37,99,235,0.18);
}
.nicegui-content .q-btn--unelevated {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
}

/* ========== 进度条美化 ========== */
.q-linear-progress {
    border-radius: 6px;
    overflow: hidden;
    height: 6px !important;
}
.q-linear-progress__track {
    background: rgba(37,99,235,0.08) !important;
}

/* ========== 输入框美化 ========== */
.q-field--outlined .q-field__control {
    border-radius: 12px !important;
}
.q-field--outlined .q-field__control:hover::before {
    border-color: #60a5fa !important;
}
.q-field--outlined.q-field--focused .q-field__control::after {
    border-color: #3b82f6 !important;
    border-width: 2px !important;
}

/* ========== 上传区域 ========== */
.q-uploader {
    border-radius: 14px !important;
    border: 2px dashed rgba(59,130,246,0.25) !important;
    background: rgba(239,246,255,0.4) !important;
    transition: border-color 0.2s ease, background 0.2s ease;
}
.q-uploader:hover {
    border-color: rgba(59,130,246,0.45) !important;
    background: rgba(239,246,255,0.6) !important;
}

/* ========== 展开面板 ========== */
.q-expansion-item {
    border-radius: 12px;
    overflow: hidden;
    margin-top: 0.5rem;
}
.q-expansion-item .q-item {
    border-radius: 12px;
}

/* ========== 滚动条美化 ========== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(59,130,246,0.2);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.35); }

/* ========== 表格美化 ========== */
.q-table {
    border-radius: 14px !important;
    overflow: hidden;
}
.q-table thead th {
    background: rgba(239,246,255,0.8) !important;
    color: #1e3a5f !important;
    font-weight: 700;
}
.q-table tbody tr:hover td {
    background: rgba(59,130,246,0.04) !important;
}
"""


def render_kpi_html(label: str, value: str, sub: str = "", extra_class: str = "") -> str:
    cls = f"kpi-card {extra_class}".strip()
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="{cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )
