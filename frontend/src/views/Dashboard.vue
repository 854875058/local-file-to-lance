<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">领导看板</h1>
      <p class="page-subtitle">实时监控数据接入与系统运行状态</p>
    </div>

    <el-button type="primary" :icon="Refresh" @click="loadData" style="margin-bottom: 1rem;">刷新数据</el-button>

    <!-- 核心指标 -->
    <div class="section-title">核心指标</div>
    <el-row :gutter="16" style="margin-bottom: 2rem;">
      <el-col :span="4" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-sub" v-if="kpi.sub">{{ kpi.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 任务健康度 -->
    <div class="section-title">任务健康度</div>
    <el-row :gutter="16" style="margin-bottom: 2rem;">
      <el-col :span="8" v-for="health in healthKpis" :key="health.label">
        <div class="kpi-card">
          <div class="kpi-label">{{ health.label }}</div>
          <div class="kpi-value">{{ health.value }}</div>
          <div class="kpi-sub" v-if="health.sub">{{ health.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 近 7 天趋势 -->
    <div class="section-title">近 7 天接入趋势</div>
    <div class="glass-card" style="margin-bottom: 2rem;">
      <div v-if="trendData.length > 0">
        <div ref="trendChart" style="width: 100%; height: 300px;"></div>
      </div>
      <el-empty v-else description="暂无近 7 天任务数据" :image-size="100" />
    </div>

    <!-- 文件类型分布 -->
    <div class="section-title">存量文件类型分布</div>
    <div class="glass-card" style="margin-bottom: 2rem;">
      <div v-if="fileTypes.length > 0">
        <div ref="typeChart" style="width: 100%; height: 300px;"></div>
      </div>
      <el-empty v-else description="暂无文件类型分布数据" :image-size="100" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'

const kpis = ref([])
const healthKpis = ref([])
const trendData = ref([])
const fileTypes = ref([])
const trendChart = ref(null)
const typeChart = ref(null)

let trendChartInstance = null
let typeChartInstance = null

const loadData = async () => {
  try {
    // 加载统计数据
    const stats = await api.getDashboardStats()

    kpis.value = [
      { label: '文本/语音切片', value: stats.text_rows.toLocaleString(), sub: 'LanceDB 文本表' },
      { label: '视觉索引', value: stats.image_rows.toLocaleString(), sub: 'LanceDB 图像表' },
      { label: '文件总量', value: stats.total_files.toLocaleString(), sub: '已注册文件数' },
      { label: '今日接入', value: stats.today_files, sub: '当日新增' },
      { label: '本周接入', value: stats.week_files, sub: '近 7 天' }
    ]

    healthKpis.value = [
      { label: '本周任务成功率', value: `${stats.week_success_rate}%`, sub: '近 7 天统计' },
      { label: '本周处理条数', value: stats.week_tasks_success, sub: `共 ${stats.week_tasks_total} 个任务` },
      { label: '平均耗时', value: `${stats.week_avg_time_sec}s`, sub: '近 7 天任务' }
    ]

    // 加载趋势数据
    trendData.value = await api.getTrend(7)
    await nextTick()
    renderTrendChart()

    // 加载文件类型分布
    fileTypes.value = await api.getFileTypes()
    await nextTick()
    renderTypeChart()

  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const renderTrendChart = () => {
  if (!trendChart.value || trendData.value.length === 0) return

  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>成功处理: {c} 个文件'
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: trendData.value.map(d => d.date),
      boundaryGap: false,
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '文件数',
      minInterval: 1,
      axisLabel: { fontSize: 11 }
    },
    series: [{
      name: '成功处理',
      data: trendData.value.map(d => d.success_count),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      areaStyle: { color: 'rgba(37,99,235,0.10)' },
      lineStyle: { color: '#2563eb', width: 3 },
      itemStyle: { color: '#2563eb' }
    }]
  }

  trendChartInstance.setOption(option)
}

const renderTypeChart = () => {
  if (!typeChart.value || fileTypes.value.length === 0) return

  if (!typeChartInstance) {
    typeChartInstance = echarts.init(typeChart.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}<br/>文件数: {c}'
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: fileTypes.value.map(t => t.doc_type),
      axisLabel: { fontSize: 11, interval: 0 }
    },
    yAxis: {
      type: 'value',
      name: '文件数',
      minInterval: 1,
      axisLabel: { fontSize: 11 }
    },
    series: [{
      name: '文件数量',
      data: fileTypes.value.map(t => t.count),
      type: 'bar',
      barWidth: '50%',
      itemStyle: {
        color: '#3b82f6',
        borderRadius: [6, 6, 0, 0]
      },
      label: {
        show: true,
        position: 'top',
        fontSize: 12,
        fontWeight: 'bold',
        color: '#1e3a5f'
      }
    }]
  }

  typeChartInstance.setOption(option)
}

onMounted(() => {
  loadData()

  // 窗口大小变化时重绘图表
  window.addEventListener('resize', () => {
    trendChartInstance?.resize()
    typeChartInstance?.resize()
  })
})
</script>
