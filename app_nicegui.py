# -*- coding: utf-8 -*-
"""
DataVerse Pro - 多模态数据中台 (NiceGUI 版)
蓝白透明卡片风格
"""

import os
import sys
import time
import logging
import shutil
import html
import asyncio
import uuid
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nicegui import ui, app, events
import pandas as pd
import psutil
import numpy as np

from config import TEMP_DIR, EXTRACT_DIR, LOG_PATH, S3_CONFIG
from database import init_db, get_task_stats, get_file_entities
from models_loader import load_models_cached, get_lancedb_tables
from etl import batch_process_local_files, sftp_task, get_s3_client, delete_file_by_hash
from stats_service import get_dashboard_stats, get_task_trend
from ui.styles import GLOBAL_CSS, render_kpi_html

# ---------- 初始化 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

for d in [TEMP_DIR, EXTRACT_DIR]:
    os.makedirs(d, exist_ok=True)

init_db()

# 全局懒加载（模型 / LanceDB 分开，互不阻塞）
_models = None
_tables = None
_models_error = None
_tables_error = None


def _ensure_models():
    """懒加载 AI 模型，失败允许重试"""
    global _models, _models_error
    if _models is not None:
        return _models
    try:
        _models = load_models_cached()
        _models_error = None
        return _models
    except Exception as e:
        _models_error = f'AI 模型加载失败: {e}'
        logger.error(_models_error)
        raise RuntimeError(_models_error)


def _ensure_tables():
    """懒加载 LanceDB 表，失败允许重试"""
    global _tables, _tables_error
    if _tables is not None:
        return _tables
    try:
        _tables = get_lancedb_tables()
        _tables_error = None
        return _tables
    except Exception as e:
        _tables_error = f'LanceDB 连接失败（SeaweedFS 可能不可达）: {e}'
        logger.error(_tables_error)
        raise RuntimeError(_tables_error)


def _get_all():
    """同时获取模型和表，任一失败抛异常"""
    models = _ensure_models()
    tbl_text, tbl_image, tbl_files = _ensure_tables()
    return models, tbl_text, tbl_image, tbl_files


def build_highlight_html(full_text: str, snippet: str, max_len: int = 100000) -> str:
    if not full_text:
        return ""
    text = str(full_text)[:max_len]
    if snippet is None:
        return html.escape(text)
    snippet_clean = str(snippet).strip()
    if not snippet_clean:
        return html.escape(text)
    try:
        idx = text.lower().find(snippet_clean.lower())
    except Exception:
        idx = -1
    if idx == -1:
        return html.escape(text)
    before = html.escape(text[:idx])
    match = html.escape(text[idx:idx + len(snippet_clean)])
    after = html.escape(text[idx + len(snippet_clean):])
    return (
        f"<pre style='white-space:pre-wrap;font-family:inherit;font-size:0.9rem;'>"
        f"{before}<mark>{match}</mark>{after}</pre>"
    )


# ========== 页面构建 ==========
@ui.page('/')
def main_page():
    # 注入全局 CSS
    ui.add_head_html(f'<style>{GLOBAL_CSS}</style>')

    # ---------- 左侧抽屉 ----------
    with ui.left_drawer(value=True).classes('q-pa-md').style('width: 260px'):
        with ui.element('div').classes('drawer-brand'):
            with ui.row().classes('items-center q-gutter-sm'):
                ui.icon('hub', size='1.6rem').style('color: #2563eb')
                ui.label('DataVerse Pro').classes('text-h6 text-weight-bold').style(
                    'color: #1e40af; background: linear-gradient(135deg, #1e3a5f, #2563eb);'
                    '-webkit-background-clip: text; -webkit-text-fill-color: transparent;'
                )
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        ui.label('系统资源').classes('text-caption text-grey-7')
        with ui.row().classes('w-full items-center q-gutter-xs'):
            ui.label(f'CPU {cpu}%').classes('text-caption')
            ui.linear_progress(value=cpu / 100, color='blue').classes('flex-grow')
        with ui.row().classes('w-full items-center q-gutter-xs'):
            ui.label(f'内存 {mem}%').classes('text-caption')
            ui.linear_progress(value=mem / 100, color='blue').classes('flex-grow')
        ui.separator().classes('q-my-sm')

        # 连接状态指示
        status_label = ui.label('').classes('text-caption')
        _update_status_indicator(status_label)

        ui.separator().classes('q-my-sm')
        ui.label('能力说明').classes('text-caption text-grey-7')
        capabilities = [
            ('cloud_download', '多模态数据入湖：文本/图片/音视频/压缩包'),
            ('storage', 'SeaweedFS + LanceDB 一体化数据湖'),
            ('manage_search', '向量语义检索 + 整篇高亮预览'),
            ('monitoring', '任务监控与数据资产看板'),
            ('auto_fix_high', '自动去重、并发接入与批量任务'),
        ]
        for icon, text in capabilities:
            with ui.row().classes('items-center q-gutter-xs'):
                ui.icon(icon, size='0.9rem').style('color: #3b82f6')
                ui.label(text).classes('text-caption text-grey-8')

    # ---------- 顶部标题 ----------
    with ui.column().classes('w-full q-px-lg q-pt-md'):
        with ui.element('div').classes('page-header'):
            with ui.row().classes('items-center q-gutter-sm'):
                ui.icon('hub', size='2rem').style('color: #2563eb')
                ui.html('<p class="page-title">DataVerse Pro 多模态数据中台</p>')
            ui.html('<p class="page-subtitle">数据资产统一接入 · 向量检索 · 运营看板</p>')

    # ---------- Tab 面板（各 Tab 延迟加载，不阻塞页面渲染） ----------
    with ui.column().classes('w-full q-px-lg'):
        with ui.tabs().classes('w-full').props('align="left" dense active-color="blue" no-caps indicator-color="blue"') as tabs:
            tab_dashboard = ui.tab('数据资产看板', icon='dashboard')
            tab_ingest = ui.tab('数据接入', icon='cloud_upload')
            tab_search = ui.tab('智能检索', icon='search')
            tab_s3 = ui.tab('对象存储浏览', icon='folder_open')
            tab_monitor = ui.tab('任务监控', icon='monitor_heart')
            tab_diag = ui.tab('数据诊断', icon='build')

        with ui.tab_panels(tabs, value=tab_dashboard).classes('w-full'):
            with ui.tab_panel(tab_dashboard):
                _deferred_panel(_build_dashboard)

            with ui.tab_panel(tab_ingest):
                _deferred_panel(_build_ingest)

            with ui.tab_panel(tab_search):
                _deferred_panel(_build_search)

            # S3 浏览和任务监控不依赖模型/LanceDB
            with ui.tab_panel(tab_s3):
                _build_s3_browser()

            with ui.tab_panel(tab_monitor):
                _build_monitor()

            with ui.tab_panel(tab_diag):
                _deferred_panel(_build_diagnose_wrapper)


def _update_status_indicator(label):
    """显示后端连接状态"""
    parts = []
    if _models is not None:
        parts.append('AI 模型: 已加载')
    elif _models_error:
        parts.append(f'AI 模型: 异常')
    else:
        parts.append('AI 模型: 待加载')

    if _tables is not None:
        parts.append('LanceDB: 已连接')
    elif _tables_error:
        parts.append('LanceDB: 不可达')
    else:
        parts.append('LanceDB: 待连接')

    label.text = ' | '.join(parts)
    if _models_error or _tables_error:
        label.classes('text-orange-7', remove='text-green-7 text-grey-7')
    elif _models is not None and _tables is not None:
        label.classes('text-green-7', remove='text-orange-7 text-grey-7')
    else:
        label.classes('text-grey-7', remove='text-green-7 text-orange-7')


def _deferred_panel(build_fn):
    """自动加载面板：页面打开后自动连接后端并渲染内容"""
    container = ui.column().classes('w-full')
    with container:
        with ui.element('div').classes('glass-card w-full'):
            with ui.row().classes('items-center q-gutter-sm'):
                spinner = ui.spinner('dots', size='1.5rem', color='blue')
                status_msg = ui.label('正在连接后端服务...').classes('text-caption text-grey-7')

    async def do_load():
        loop = asyncio.get_event_loop()
        try:
            models, tbl_text, tbl_image, tbl_files = await loop.run_in_executor(None, _get_all)
        except Exception as e:
            container.clear()
            with container:
                _render_connection_error(str(e))
            return
        container.clear()
        with container:
            build_fn(models, tbl_text, tbl_image, tbl_files)

    ui.timer(0.1, do_load, once=True)


def _render_connection_error(msg: str):
    """渲染连接失败的友好提示卡片"""
    with ui.element('div').classes('glass-card w-full'):
        with ui.row().classes('items-center q-gutter-sm'):
            ui.icon('cloud_off', size='2rem').classes('text-orange-6')
            ui.label('后端服务未就绪').classes('text-h6 text-orange-8')
        ui.label(msg).classes('text-caption text-grey-7 q-mt-sm')
        ui.label('请检查 SeaweedFS / S3 连接或 AI 模型配置后刷新页面。').classes('text-caption text-grey-6 q-mt-xs')
        ui.button('重试连接', icon='refresh', on_click=lambda: ui.navigate.reload(), color='blue').props('outline').classes('q-mt-md')


def _build_diagnose_wrapper(models, tbl_text, tbl_image, tbl_files):
    """诊断页的包装，适配 _safe_build 的签名"""
    _build_diagnose(tbl_text, tbl_image, tbl_files)


def _build_dashboard(models, tbl_text, tbl_image, tbl_files):
    dash_container = ui.column().classes('w-full')

    def _render_dashboard():
        dash_container.clear()
        with dash_container:
            try:
                text_rows = tbl_text.count_rows()
                image_rows = tbl_image.count_rows()
            except Exception:
                text_rows = image_rows = 0

            stats = get_dashboard_stats()

            # 刷新按钮
            ui.button('刷新数据', icon='refresh', on_click=_render_dashboard, color='blue').props('outline dense')

            # 核心指标
            ui.html('<div class="section-title">核心指标</div>')
            with ui.row().classes('w-full q-gutter-md'):
                ui.html(render_kpi_html('文本/语音切片', f'{text_rows:,}', 'LanceDB 文本表'))
                ui.html(render_kpi_html('视觉索引', f'{image_rows:,}', 'LanceDB 图像表'))
                ui.html(render_kpi_html('文件总量', f"{stats['total_files']:,}", '已注册文件数'))
                ui.html(render_kpi_html('今日接入', f"{stats['today_files']}", '当日新增', 'primary'))
                ui.html(render_kpi_html('本周接入', f"{stats['week_files']}", '近 7 天'))

            # 任务健康度
            ui.html('<div class="section-title">任务健康度</div>')
            with ui.row().classes('w-full q-gutter-md'):
                ui.html(render_kpi_html('本周任务成功率', f"{stats['week_success_rate']}%", '近 7 天统计', 'success'))
                ui.html(render_kpi_html('本周处理条数', f"{stats['week_tasks_success']}", f"共 {stats['week_tasks_total']} 个任务"))
                ui.html(render_kpi_html('平均耗时', f"{stats['week_avg_time_sec']}s", '近 7 天任务'))

            # 近 7 天趋势
            ui.html('<div class="section-title">近 7 天接入趋势</div>')
            trend = get_task_trend(7)
            if trend:
                df_trend = pd.DataFrame(trend)
                chart_data = {
                    'tooltip': {'trigger': 'axis'},
                    'xAxis': {'type': 'category', 'data': df_trend['date'].tolist()},
                    'yAxis': {'type': 'value'},
                    'series': [{'data': df_trend['success_count'].tolist(), 'type': 'line',
                                'smooth': True, 'areaStyle': {'color': 'rgba(37,99,235,0.10)'},
                                'lineStyle': {'color': '#2563eb'}, 'itemStyle': {'color': '#2563eb'}}],
                }
                with ui.element('div').classes('glass-card'):
                    ui.echart(chart_data).classes('w-full').style('height: 280px')
            else:
                with ui.element('div').classes('glass-card'):
                    ui.label('暂无近 7 天任务数据，接入数据后将显示趋势图。').classes('text-grey-6')

            # 文件类型分布
            ui.html('<div class="section-title">存量文件类型分布</div>')
            try:
                files_df_dash = tbl_files.to_pandas()
            except Exception:
                files_df_dash = pd.DataFrame()
            if not files_df_dash.empty and 'doc_type' in files_df_dash.columns:
                type_counts = files_df_dash['doc_type'].fillna('未知').value_counts()
                chart_bar = {
                    'tooltip': {'trigger': 'axis'},
                    'xAxis': {'type': 'category', 'data': type_counts.index.tolist()},
                    'yAxis': {'type': 'value'},
                    'series': [{'data': type_counts.values.tolist(), 'type': 'bar',
                                'itemStyle': {'color': '#3b82f6', 'borderRadius': [6, 6, 0, 0]}}],
                }
                with ui.element('div').classes('glass-card'):
                    ui.echart(chart_bar).classes('w-full').style('height: 260px')
            else:
                with ui.element('div').classes('glass-card'):
                    ui.label('暂无文件类型分布数据。').classes('text-grey-6')

            # 知识图谱
            _build_knowledge_graph(models, tbl_files)

    _render_dashboard()


def _build_knowledge_graph(models, tbl_files):
    ui.html('<div class="section-title">文件知识图谱</div>')
    try:
        files_df_kg = tbl_files.to_pandas()
    except Exception:
        files_df_kg = pd.DataFrame()

    if files_df_kg.empty or 'file_hash' not in files_df_kg.columns:
        with ui.element('div').classes('glass-card'):
            ui.label('暂无可用于构建文件知识图谱的文件数据。').classes('text-grey-6')
        return

    # 尝试从 file_entities 表读取实体数据
    all_entities = get_file_entities()
    if all_entities:
        _build_entity_graph(files_df_kg, all_entities)
    else:
        _build_similarity_graph(models, files_df_kg)


def _build_entity_graph(files_df_kg, all_entities):
    """基于 LLM 抽取的实体构建知识图谱"""
    # 构建 file_hash -> doc_name 映射
    hash_to_name = {}
    for _, row in files_df_kg.iterrows():
        h = row.get('file_hash', '')
        name = str(row.get('doc_name') or '')[:30]
        if h:
            hash_to_name[h] = name

    # 构建节点和边
    nodes = []
    node_set = set()
    links = []

    # 文件节点
    for h, name in hash_to_name.items():
        if name and name not in node_set:
            nodes.append({'name': name, 'symbolSize': 30,
                          'itemStyle': {'color': '#3b82f6'}, 'category': 0})
            node_set.add(name)

    # 实体节点 + 文件-实体边
    entity_colors = {'人名': '#ef4444', '地名': '#f59e0b', '组织': '#10b981', '技术术语': '#8b5cf6'}
    for ent in all_entities:
        fh = ent['file_hash']
        ename = (ent['entity_name'] or '')[:20]
        etype = ent['entity_type'] or ''
        doc_name = hash_to_name.get(fh)
        if not doc_name or not ename:
            continue
        if ename not in node_set:
            color = entity_colors.get(etype, '#6b7280')
            nodes.append({'name': ename, 'symbolSize': 18,
                          'itemStyle': {'color': color}, 'category': 1})
            node_set.add(ename)
        links.append({'source': doc_name, 'target': ename,
                      'lineStyle': {'width': 1.5}})

    if not links:
        with ui.element('div').classes('glass-card'):
            ui.label('实体数据为空，暂无法构建知识图谱。').classes('text-grey-6')
        return

    # 限制节点数量
    if len(nodes) > 100:
        nodes = nodes[:100]
        valid_names = {n['name'] for n in nodes}
        links = [l for l in links if l['source'] in valid_names and l['target'] in valid_names]

    chart_kg = {
        'tooltip': {},
        'legend': [{'data': ['文件', '实体']}],
        'series': [{
            'type': 'graph', 'layout': 'force', 'roam': True,
            'label': {'show': True, 'fontSize': 10},
            'force': {'repulsion': 200, 'edgeLength': [60, 140]},
            'categories': [{'name': '文件'}, {'name': '实体'}],
            'data': nodes, 'links': links,
            'lineStyle': {'color': '#93c5fd', 'curveness': 0.1},
        }],
    }
    with ui.element('div').classes('glass-card'):
        ui.echart(chart_kg).classes('w-full').style('height: 420px')


def _build_similarity_graph(models, files_df_kg):
    """基于向量相似度的 fallback 知识图谱（异步编码，不阻塞 UI）"""
    if 'text_full' not in files_df_kg.columns:
        with ui.element('div').classes('glass-card'):
            ui.label('暂无文本内容，无法构建相似度图谱。').classes('text-grey-6')
        return

    max_nodes = 20
    subset = files_df_kg.head(max_nodes).reset_index(drop=True)
    texts = subset['text_full'].fillna('').astype(str).str.slice(0, 2000).tolist()
    has_text = any(t.strip() for t in texts)
    if not has_text:
        with ui.element('div').classes('glass-card'):
            ui.label('当前文件缺少可用文本内容，无法构建知识图谱。').classes('text-grey-6')
        return

    # 占位容器，异步完成后填充
    graph_container = ui.column().classes('w-full')
    with graph_container:
        with ui.element('div').classes('glass-card'):
            with ui.row().classes('items-center q-gutter-sm'):
                ui.spinner('dots', size='1.2rem', color='blue')
                ui.label('正在计算文件相似度...').classes('text-caption text-grey-7')

    async def _compute_and_render():
        loop = asyncio.get_event_loop()
        try:
            vecs = await loop.run_in_executor(
                None, lambda: np.array(models['text'].encode(texts))
            )
        except Exception as e:
            graph_container.clear()
            with graph_container:
                with ui.element('div').classes('glass-card'):
                    ui.label(f'向量编码失败: {e}').classes('text-red-6')
            return

        if vecs.ndim != 2 or vecs.shape[0] <= 1:
            graph_container.clear()
            with graph_container:
                with ui.element('div').classes('glass-card'):
                    ui.label('文件数量不足以构建知识图谱。').classes('text-grey-6')
            return

        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        vecs_norm = vecs / norms
        sim = np.matmul(vecs_norm, vecs_norm.T)
        sim_threshold = 0.6

        nodes = []
        for i, row in subset.iterrows():
            label = str(row.get('doc_name') or f'文件{i+1}')[:30]
            nodes.append({'name': label, 'symbolSize': 28,
                          'itemStyle': {'color': '#3b82f6'}})
        links = []
        n = len(subset)
        for i in range(n):
            for j in range(i + 1, n):
                w = float(sim[i, j])
                if w >= sim_threshold:
                    links.append({'source': nodes[i]['name'], 'target': nodes[j]['name'],
                                  'lineStyle': {'width': 1 + 3 * (w - sim_threshold)}})

        graph_container.clear()
        with graph_container:
            if not links:
                with ui.element('div').classes('glass-card'):
                    ui.label('当前文件之间相似度较低，暂未生成连边（无实体数据可用）。').classes('text-grey-6')
                return

            chart_kg = {
                'tooltip': {},
                'series': [{
                    'type': 'graph', 'layout': 'force', 'roam': True,
                    'label': {'show': True, 'fontSize': 10},
                    'force': {'repulsion': 200, 'edgeLength': [80, 160]},
                    'data': nodes, 'links': links,
                    'lineStyle': {'color': '#93c5fd', 'curveness': 0.1},
                }],
            }
            with ui.element('div').classes('glass-card'):
                ui.echart(chart_kg).classes('w-full').style('height: 360px')

    ui.timer(0.1, _compute_and_render, once=True)


def _build_ingest(models, tbl_text, tbl_image, tbl_files):
    mode = ui.toggle(['本地上传', 'SFTP 采集'], value='本地上传').classes('q-mb-md')

    # --- 本地上传区 ---
    local_container = ui.column().classes('w-full')
    # --- SFTP 区 ---
    sftp_container = ui.column().classes('w-full')

    upload_holder = {'files': []}  # 存放已上传的临时文件路径

    def on_mode_change():
        is_local = mode.value == '本地上传'
        local_container.set_visibility(is_local)
        sftp_container.set_visibility(not is_local)

    mode.on_value_change(on_mode_change)

    # 本地上传
    with local_container:
        with ui.element('div').classes('glass-card w-full'):
            ui.label('支持：音视频 (mp3/mp4/wav)、Office、PDF、代码、压缩包等').classes('text-caption text-grey-7 q-mb-sm')

            upload = ui.upload(
                label='拖拽或点击选择文件',
                multiple=True,
                auto_upload=True,
                on_upload=lambda e: _handle_upload(e, upload_holder),
            ).classes('w-full').props('color="blue" flat bordered')

            progress_label = ui.label('').classes('text-caption text-grey-7 q-mt-sm')
            progress_bar = ui.linear_progress(value=0, color='blue').classes('w-full q-mt-xs')
            progress_bar.set_visibility(False)
            result_label = ui.label('').classes('q-mt-sm')
            skipped_label = ui.label('').classes('text-caption text-orange-7 q-mt-xs')

            async def do_process():
                if not upload_holder['files']:
                    ui.notify('请先上传文件', type='warning')
                    return
                progress_bar.set_visibility(True)
                result_label.text = ''
                skipped_label.text = ''
                total = len(upload_holder['files'])

                prog_state = {'i': 0, 't': 1, 'msg': '', 'done': False}

                def progress_cb(i, t, msg):
                    prog_state['i'] = i
                    prog_state['t'] = t
                    prog_state['msg'] = msg

                def poll_progress():
                    if prog_state['done']:
                        poll_timer.deactivate()
                        return
                    t = prog_state['t'] or 1
                    progress_bar.value = prog_state['i'] / t
                    progress_label.text = f"处理中 {prog_state['i']}/{t} — {prog_state['msg']}"

                poll_timer = ui.timer(0.3, poll_progress)

                loop = asyncio.get_event_loop()
                succ, skip, dur, skipped_names = await loop.run_in_executor(
                    None,
                    lambda: batch_process_local_files(
                        upload_holder['files'], models, tbl_text, tbl_image, tbl_files,
                        progress_callback=progress_cb,
                    ),
                )
                prog_state['done'] = True
                poll_timer.deactivate()
                progress_bar.value = 1.0
                progress_label.text = ''
                result_label.text = f'完成 — 耗时 {dur:.2f}s | 成功: {succ} | 跳过: {skip}'
                if skipped_names:
                    skipped_label.text = f'跳过的文件: {", ".join(skipped_names)}'
                ui.notify(f'处理完成: 成功 {succ}, 跳过 {skip}', type='positive')
                # 清理临时文件
                for p, _ in upload_holder['files']:
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass
                upload_holder['files'] = []

            ui.button('开始处理', on_click=do_process, color='blue').props('unelevated')

    # SFTP 采集
    with sftp_container:
        sftp_container.set_visibility(False)
        with ui.element('div').classes('glass-card w-full'):
            with ui.row().classes('w-full q-gutter-md'):
                sftp_host = ui.input('IP').classes('flex-grow')
                sftp_port = ui.input('端口', value='22').style('width: 80px')
                sftp_user = ui.input('用户名').classes('flex-grow')
            with ui.row().classes('w-full q-gutter-md'):
                sftp_pw = ui.input('密码', password=True).classes('flex-grow')
                sftp_path = ui.input('远程路径', value='/tmp').classes('flex-grow')

            sftp_log = ui.log(max_lines=50).classes('w-full q-mt-sm').style('height: 200px')
            sftp_progress_label = ui.label('').classes('text-caption text-grey-7 q-mt-sm')
            sftp_progress_bar = ui.linear_progress(value=0, color='blue').classes('w-full q-mt-xs')
            sftp_progress_bar.set_visibility(False)
            sftp_skipped_label = ui.label('').classes('text-caption text-orange-7 q-mt-xs')

            async def do_sftp():
                sftp_log.clear()
                sftp_skipped_label.text = ''
                sftp_progress_bar.set_visibility(True)
                sftp_progress_bar.value = 0

                sftp_prog_state = {'i': 0, 't': 1, 'msg': '', 'done': False}

                def sftp_progress_cb(i, t, msg):
                    sftp_prog_state['i'] = i
                    sftp_prog_state['t'] = t
                    sftp_prog_state['msg'] = msg

                def sftp_poll():
                    if sftp_prog_state['done']:
                        sftp_poll_timer.deactivate()
                        return
                    t = sftp_prog_state['t'] or 1
                    sftp_progress_bar.value = sftp_prog_state['i'] / t if t > 0 else 0
                    sftp_progress_label.text = f"{sftp_prog_state['i']}/{t} — {sftp_prog_state['msg']}"

                sftp_poll_timer = ui.timer(0.3, sftp_poll)

                loop = asyncio.get_event_loop()
                logs, skipped_names = await loop.run_in_executor(
                    None,
                    lambda: sftp_task(
                        sftp_host.value, sftp_port.value, sftp_user.value,
                        sftp_pw.value, sftp_path.value,
                        models, tbl_text, tbl_image, tbl_files,
                        progress_callback=sftp_progress_cb,
                    ),
                )
                sftp_prog_state['done'] = True
                sftp_poll_timer.deactivate()
                sftp_progress_bar.value = 1.0
                sftp_progress_label.text = ''
                for line in logs:
                    sftp_log.push(line)
                if skipped_names:
                    sftp_skipped_label.text = f'跳过的文件: {", ".join(skipped_names)}'

            ui.button('开始采集', on_click=do_sftp, color='blue').props('unelevated')


def _handle_upload(e: events.UploadEventArguments, holder: dict):
    """将 NiceGUI 上传的文件保存到临时目录"""
    name = e.name
    tp = os.path.join(TEMP_DIR, f'{uuid.uuid4().hex[:8]}_{name}')
    with open(tp, 'wb') as f:
        f.write(e.content.read())
    holder['files'].append((tp, name))


def _build_search(models, tbl_text, tbl_image, tbl_files):
    with ui.element('div').classes('glass-card w-full'):
        ui.label('按语义检索文本/语音片段或图片内容，支持结果预览与下载').classes('text-caption text-grey-7 q-mb-sm')
        with ui.row().classes('w-full q-gutter-md items-end'):
            search_mode = ui.select(
                ['文本/语音内容', '视觉搜图'], value='文本/语音内容', label='检索模式',
            ).style('min-width: 160px')
            doc_types = ui.select(
                ['mp4', 'mp3', 'pdf', 'docx', 'xlsx', 'csv'],
                label='类型过滤', multiple=True, value=[],
            ).style('min-width: 200px').props('use-chips')
            query_input = ui.input('查询', placeholder='输入关键词：会议录音、视频内容、文档片段…').classes('flex-grow')
            page_size_select = ui.select([10, 20, 50], value=10, label='每页条数').style('min-width: 100px')

    results_container = ui.column().classes('w-full q-mt-md')
    # 分页状态
    search_state = {'all_results': None, 'files_df': None, 'page': 0}

    def _render_page():
        results_container.clear()
        res = search_state['all_results']
        files_df = search_state['files_df']
        if res is None or res.empty:
            with results_container:
                ui.label('无匹配结果').classes('text-grey-6')
            return

        total = len(res)
        ps = int(page_size_select.value)
        page = search_state['page']
        start = page * ps
        end = min(start + ps, total)
        page_df = res.iloc[start:end]

        with results_container:
            with ui.row().classes('w-full items-center q-gutter-md'):
                ui.label(f'第 {start+1}-{end} 条，共 {total} 条').classes('text-caption text-grey-7')

                def go_prev():
                    if search_state['page'] > 0:
                        search_state['page'] -= 1
                        _render_page()

                def go_next():
                    if end < total:
                        search_state['page'] += 1
                        _render_page()

                ui.button('上一页', on_click=go_prev, color='blue').props('flat dense').set_enabled(page > 0)
                ui.button('下一页', on_click=go_next, color='blue').props('flat dense').set_enabled(end < total)

                def export_csv():
                    csv_buf = io.BytesIO()
                    export_cols = [c for c in res.columns if c not in ('vector',)]
                    res[export_cols].to_csv(csv_buf, index=False, encoding='utf-8-sig')
                    ui.download(csv_buf.getvalue(), 'search_results.csv')

                ui.button('导出 CSV', icon='download', on_click=export_csv, color='blue').props('outline dense')

            for idx, r in page_df.iterrows():
                doc_name = r.get('doc_name', '') or ''
                doc_type = r.get('doc_type', '') or ''
                if not doc_type and doc_name:
                    doc_type = doc_name.rsplit('.', 1)[-1].lower() if '.' in doc_name else ''
                file_hash = r.get('file_hash') if 'file_hash' in r.index else None

                with ui.element('div').classes('result-card'):
                    ui.label(f'{doc_name} ({doc_type or "—"})').classes('text-weight-bold text-blue-9')
                    snippet = (r.get('text') or r.get('meta_info', '') or '')[:200]
                    if snippet:
                        full_text_len = len(str(r.get('text') or r.get('meta_info', '')))
                        ui.label(snippet + ('...' if full_text_len > 200 else '')).classes('text-caption text-grey-7')

                    if not file_hash:
                        ui.label('缺少 file_hash，无法定位原始文件，请重新接入。').classes('text-caption text-orange-7')
                        continue

                    if files_df.empty or 'file_hash' not in files_df.columns:
                        df_file = None
                    else:
                        df_file = files_df[files_df['file_hash'] == file_hash]
                    if df_file is None or df_file.empty:
                        ui.label('files 表未找到原始文件（可重新接入）。').classes('text-caption text-orange-7')
                        continue

                    file_bytes = df_file.iloc[0].get('file_bytes')
                    text_full = df_file.iloc[0].get('text_full') or ''
                    ext = (doc_type or '').strip().lower()

                    _render_preview(ext, file_bytes, text_full, r, idx, file_hash, doc_name,
                                    tbl_text, tbl_image, tbl_files, _render_page)

    async def do_search():
        q = query_input.value
        if not q:
            ui.notify('请输入查询内容', type='warning')
            return
        results_container.clear()

        loop = asyncio.get_event_loop()

        def _search():
            if '文本' in search_mode.value:
                vec = models['text'].encode([q])[0]
                query = tbl_text.search(vec)
                if doc_types.value:
                    wh = f"doc_type IN ({', '.join(repr(t) for t in doc_types.value)})"
                    query = query.where(wh)
                return query.limit(200).to_pandas()
            else:
                vec = models['clip_text'].encode([q])[0]
                return tbl_image.search(vec).limit(200).to_pandas()

        res = await loop.run_in_executor(None, _search)

        try:
            files_df = tbl_files.to_pandas()
        except Exception:
            files_df = pd.DataFrame()

        search_state['all_results'] = res
        search_state['files_df'] = files_df
        search_state['page'] = 0
        _render_page()

    with ui.element('div').classes('w-full q-mt-sm'):
        ui.button('检索', on_click=do_search, color='blue').props('unelevated')


def _render_preview(ext, file_bytes, text_full, r, idx, file_hash, doc_name,
                    tbl_text=None, tbl_image=None, tbl_files=None, refresh_fn=None):
    """渲染单条检索结果的预览、下载和删除"""
    IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    AUDIO_EXTS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}
    VIDEO_EXTS = {'mp4', 'webm', 'mov'}

    if ext in IMAGE_EXTS and file_bytes:
        import base64
        b64 = base64.b64encode(file_bytes).decode()
        ui.html(f'<img src="data:image/{ext};base64,{b64}" style="max-width:100%;max-height:400px;border-radius:8px;" />')
    elif ext in AUDIO_EXTS and file_bytes:
        import base64
        b64 = base64.b64encode(file_bytes).decode()
        ui.html(f'<audio controls src="data:audio/{ext};base64,{b64}" style="width:100%"></audio>')
    elif ext in VIDEO_EXTS and file_bytes:
        import base64
        b64 = base64.b64encode(file_bytes).decode()
        ui.html(f'<video controls src="data:video/{ext};base64,{b64}" style="max-width:100%;max-height:400px;border-radius:8px;"></video>')
    elif text_full:
        hit_text = r.get('text') if 'text' in r.index else None
        html_content = build_highlight_html(text_full, hit_text) if hit_text else None
        if html_content:
            with ui.expansion('全文预览（高亮）', icon='description').classes('w-full'):
                ui.html(html_content)
        else:
            with ui.expansion('全文预览', icon='description').classes('w-full'):
                ui.html(f"<pre style='white-space:pre-wrap;font-size:0.85rem;max-height:300px;overflow:auto;'>{html.escape(text_full[:100000])}</pre>")
    else:
        ui.label('该格式暂不支持内嵌预览（可下载原件）。').classes('text-caption text-grey-6')

    # 下载按钮
    if file_bytes:
        ui.button(
            '下载原始文件', icon='download',
            on_click=lambda fb=file_bytes, dn=doc_name: ui.download(fb, dn),
            color='blue',
        ).props('flat dense')

    # 删除按钮
    if file_hash and tbl_text is not None and tbl_image is not None and tbl_files is not None:
        async def do_delete(fh=file_hash, dn=doc_name):
            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(
                None, lambda: delete_file_by_hash(fh, tbl_text, tbl_image, tbl_files))
            if ok:
                ui.notify(f'已删除: {dn}', type='positive')
            else:
                ui.notify(f'删除部分失败: {dn}', type='warning')
            if refresh_fn:
                refresh_fn()

        ui.button(
            '删除', icon='delete',
            on_click=do_delete,
            color='red',
        ).props('flat dense')


def _build_s3_browser():
    bucket = S3_CONFIG.get('raw_bucket', '')
    endpoint = S3_CONFIG.get('endpoint_url', '')

    with ui.element('div').classes('glass-card w-full'):
        ui.label(f'Endpoint: {endpoint}  ·  Bucket: {bucket}').classes('text-caption text-grey-7 q-mb-sm')
        with ui.row().classes('w-full q-gutter-md items-end'):
            prefix_input = ui.input('路径前缀（Prefix）', value='raw/').classes('flex-grow')
            max_keys_input = ui.number('最多返回条数', value=200, min=10, max=500, step=10).style('width: 140px')

    s3_results = ui.column().classes('w-full q-mt-md')

    async def refresh_s3():
        s3_results.clear()
        s3 = get_s3_client()
        if not s3:
            with s3_results:
                ui.label('S3 客户端未配置或连接失败。').classes('text-red-6')
            return
        try:
            resp = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix_input.value or '',
                Delimiter='/',
                MaxKeys=int(max_keys_input.value),
            )
            prefixes = [p.get('Prefix') for p in resp.get('CommonPrefixes', [])]
            contents = resp.get('Contents', []) or []

            with s3_results:
                # 返回上一级
                norm = (prefix_input.value or '').rstrip('/')
                if norm and norm != 'raw':
                    parent = norm.rsplit('/', 1)[0] + '/' if '/' in norm else ''

                    async def go_parent(p=parent):
                        prefix_input.value = p
                        await refresh_s3()

                    ui.button('返回上一级', icon='arrow_back', on_click=go_parent, color='blue').props('flat dense')

                if prefixes:
                    ui.label('子目录').classes('text-weight-bold text-blue-9 q-mt-sm')
                    for p in prefixes:
                        name = p[len(prefix_input.value):] if p.startswith(prefix_input.value) else p

                        async def go_dir(target=p):
                            prefix_input.value = target
                            await refresh_s3()

                        ui.button(name or p, icon='folder', on_click=go_dir, color='blue').props('flat dense')

                if contents:
                    ui.label('对象列表').classes('text-weight-bold text-blue-9 q-mt-sm')
                    rows = [
                        {
                            'Key': obj.get('Key', ''),
                            'Size(MB)': round((obj.get('Size', 0) or 0) / 1024 / 1024, 2),
                            'LastModified': str(obj.get('LastModified', '')),
                        }
                        for obj in contents
                    ]
                    columns = [
                        {'name': 'Key', 'label': 'Key', 'field': 'Key', 'align': 'left'},
                        {'name': 'Size(MB)', 'label': 'Size(MB)', 'field': 'Size(MB)'},
                        {'name': 'LastModified', 'label': 'LastModified', 'field': 'LastModified'},
                    ]
                    ui.table(columns=columns, rows=rows).classes('w-full')
                    ui.label(f'共 {len(rows)} 个对象（当前页）').classes('text-caption text-grey-6')

                if not prefixes and not contents:
                    ui.label('当前前缀下未找到对象。').classes('text-grey-6')
        except Exception as e:
            with s3_results:
                ui.label(f'列举对象失败: {e}').classes('text-red-6')

    ui.button('刷新对象列表', icon='refresh', on_click=refresh_s3, color='blue').props('unelevated').classes('q-mt-sm')


def _build_monitor():
    with ui.element('div').classes('glass-card w-full'):
        ui.label('最近 50 条任务执行记录').classes('text-caption text-grey-7 q-mb-sm')
        rows = get_task_stats(50)
        if rows:
            table_rows = [
                {
                    '创建时间': r[6],
                    '文件数': r[3],
                    '成功数': r[4],
                    '耗时(s)': round(r[5], 2) if r[5] else 0,
                }
                for r in rows
            ]
            columns = [
                {'name': '创建时间', 'label': '创建时间', 'field': '创建时间', 'align': 'left'},
                {'name': '文件数', 'label': '文件数', 'field': '文件数'},
                {'name': '成功数', 'label': '成功数', 'field': '成功数'},
                {'name': '耗时(s)', 'label': '耗时(s)', 'field': '耗时(s)'},
            ]
            ui.table(columns=columns, rows=table_rows).classes('w-full')
        else:
            ui.label('暂无任务记录').classes('text-grey-6')


def _build_diagnose(tbl_text, tbl_image, tbl_files):
    diag_container = ui.column().classes('w-full')

    async def do_diagnose():
        diag_container.clear()
        with diag_container:
            try:
                text_df = tbl_text.to_pandas()
                image_df = tbl_image.to_pandas()
                files_df = tbl_files.to_pandas()

                ui.html('<div class="section-title">数据统计</div>')
                with ui.row().classes('w-full q-gutter-md'):
                    text_hashes = set(text_df['file_hash'].unique()) if 'file_hash' in text_df.columns else set()
                    image_hashes = set(image_df['file_hash'].unique()) if 'file_hash' in image_df.columns else set()
                    files_hashes = set(files_df['file_hash'].unique()) if 'file_hash' in files_df.columns else set()
                    ui.html(render_kpi_html('文本表记录', str(len(text_df)), f'唯一 hash: {len(text_hashes)}'))
                    ui.html(render_kpi_html('图像表记录', str(len(image_df)), f'唯一 hash: {len(image_hashes)}'))
                    ui.html(render_kpi_html('文件表记录', str(len(files_df)), f'唯一 hash: {len(files_hashes)}'))

                ui.html('<div class="section-title">一致性检查</div>')
                missing_text = text_hashes - files_hashes
                missing_image = image_hashes - files_hashes

                if missing_text:
                    ui.label(f'文本表中有 {len(missing_text)} 个 file_hash 在文件表中不存在').classes('text-red-6')
                else:
                    ui.label('文本表所有记录都能在文件表中找到').classes('text-green-7')

                if missing_image:
                    ui.label(f'图像表中有 {len(missing_image)} 个 file_hash 在文件表中不存在').classes('text-red-6')
                else:
                    ui.label('图像表所有记录都能在文件表中找到').classes('text-green-7')

                if missing_text or missing_image:
                    ui.html('<div class="section-title">修复建议</div>')
                    ui.label('检测到数据不一致。建议重新接入文件或清理孤立记录。').classes('text-orange-7')

                    async def do_clean():
                        cleaned = 0
                        try:
                            for h in missing_text:
                                safe_hash = h.replace("'", "''")
                                tbl_text.delete(f"file_hash = '{safe_hash}'")
                                cleaned += 1
                            for h in missing_image:
                                safe_hash = h.replace("'", "''")
                                tbl_image.delete(f"file_hash = '{safe_hash}'")
                                cleaned += 1
                            ui.notify(f'已清理 {cleaned} 个孤立的 file_hash', type='positive')
                        except Exception as e:
                            ui.notify(f'清理失败: {e}', type='negative')

                    ui.button('清理孤立记录（谨慎操作）', on_click=do_clean, color='red').props('outline')
                else:
                    ui.label('数据一致性良好，无需修复').classes('text-green-7')

            except Exception as e:
                ui.label(f'诊断失败: {e}').classes('text-red-6')

    with ui.element('div').classes('glass-card w-full'):
        ui.label('检查数据一致性，修复 file_hash 不匹配问题').classes('text-caption text-grey-7 q-mb-sm')
        ui.button('诊断数据一致性', icon='search', on_click=do_diagnose, color='blue').props('unelevated')


# ========== 启动 ==========
ui.run(title='DataVerse Pro - 多模态数据中台', port=8088, reload=False, show=False)
