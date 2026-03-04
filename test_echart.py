# -*- coding: utf-8 -*-
"""测试 ECharts 是否能正常显示"""

from nicegui import ui

@ui.page('/')
def index():
    ui.label('ECharts 测试页面').classes('text-h4')

    # 测试 1: 简单折线图
    ui.label('测试 1: 简单折线图').classes('text-h6 q-mt-md')
    chart1 = {
        'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', 'Wed']},
        'yAxis': {'type': 'value'},
        'series': [{'data': [120, 200, 150], 'type': 'line'}]
    }
    ui.echart(chart1).style('height: 300px; width: 100%; border: 1px solid red;')

    # 测试 2: 实际数据的折线图
    ui.label('测试 2: 实际趋势数据').classes('text-h6 q-mt-md')
    chart2 = {
        'tooltip': {
            'trigger': 'axis',
            'formatter': '{b}<br/>成功处理: {c} 个文件'
        },
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'data': ['2026-03-04'],
            'boundaryGap': False,
            'axisLabel': {'rotate': 30, 'fontSize': 11}
        },
        'yAxis': {
            'type': 'value',
            'name': '文件数',
            'minInterval': 1,
            'axisLabel': {'fontSize': 11}
        },
        'series': [{
            'name': '成功处理',
            'data': [1],
            'type': 'line',
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 8,
            'areaStyle': {'color': 'rgba(37,99,235,0.10)'},
            'lineStyle': {'color': '#2563eb', 'width': 3},
            'itemStyle': {'color': '#2563eb'}
        }],
    }
    ui.echart(chart2).style('height: 300px; width: 100%; border: 1px solid blue;')

    # 测试 3: 柱状图
    ui.label('测试 3: 文件类型分布').classes('text-h6 q-mt-md')
    chart3 = {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'formatter': '{b}<br/>文件数: {c}'
        },
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'data': ['txt'],
            'axisLabel': {'fontSize': 11, 'interval': 0}
        },
        'yAxis': {
            'type': 'value',
            'name': '文件数',
            'minInterval': 1,
            'axisLabel': {'fontSize': 11}
        },
        'series': [{
            'name': '文件数量',
            'data': [1],
            'type': 'bar',
            'barWidth': '50%',
            'itemStyle': {
                'color': '#3b82f6',
                'borderRadius': [6, 6, 0, 0]
            },
            'label': {
                'show': True,
                'position': 'top',
                'fontSize': 12,
                'fontWeight': 'bold',
                'color': '#1e3a5f'
            }
        }],
    }
    ui.echart(chart3).style('height: 300px; width: 100%; border: 1px solid green;')

ui.run(port=8765, title='ECharts 测试')
