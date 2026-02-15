"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api, FundItem, BatchImportResult } from "@/lib/api"

const getRecentQuarters = (): string[] => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  
  let currentQuarter
  if (month <= 3) currentQuarter = 1
  else if (month <= 6) currentQuarter = 2
  else if (month <= 9) currentQuarter = 3
  else currentQuarter = 4
  
  let q = currentQuarter - 1
  let y = year
  
  if (q < 1) {
    q = 4
    y--
  }
  
  const quarters: string[] = []
  
  for (let i = 0; i < 3; i++) {
    quarters.push(`${y}Q${q}`)
    q--
    if (q < 1) {
      q = 4
      y--
    }
  }
  
  return quarters
}

const RECENT_QUARTERS = getRecentQuarters()

type ReportModalData = {
  fund_code: string
  report_period: string
  viewpoint: string
  fund_info: {
    name?: string
    manager?: string
  }
}

export default function HomePage() {
  const router = useRouter()
  const [funds, setFunds] = useState<FundItem[]>([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<BatchImportResult | null>(null)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importCodes, setImportCodes] = useState("")
  const [selectedFund, setSelectedFund] = useState<FundItem | null>(null)
  const [deleteConfirmFund, setDeleteConfirmFund] = useState<FundItem | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null)
  const [reportModal, setReportModal] = useState<{
    fund: FundItem;
    quarter: string;
  } | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportData, setReportData] = useState<ReportModalData | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)
  const [showQuarterSelectModal, setShowQuarterSelectModal] = useState(false)
  const [batchProgress, setBatchProgress] = useState<{
    show: boolean
    quarter: string
    current: number
    total: number
    currentFund: string
    results: Array<{
      fund_code: string
      fund_name: string
      success: boolean
      viewpoint?: string
      manager?: string
      error?: string
    }>
    cancelled: boolean
  } | null>(null)

  const refreshFunds = useCallback(async () => {
    setLoading(true)
    const res = await api.getAllFunds()
    setFunds(res.data || [])
    setLoading(false)
  }, [])

  useEffect(() => {
    refreshFunds()
  }, [refreshFunds])

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type })
  }

  const handleBatchImport = async () => {
    const codes = importCodes
      .split(/[\n,]/)
      .map((c) => c.trim())
      .filter((c) => c.length > 0)

    if (codes.length === 0) {
      alert("请输入基金代码")
      return
    }

    setImporting(true)
    const res = await api.batchImportFunds(codes)
    setImportResult(res.data)
    setImporting(false)

    if (res.data?.success?.length > 0) {
      setImportCodes("")
      await refreshFunds()
    }
  }

  const handleDeleteFund = async (fund: FundItem) => {
    setDeleting(true)
    try {
      const res = await api.deleteFundFromDb(fund.code)
      if (res.data?.success) {
        showToast("基金删除成功", "success")
        setFunds((prev) => prev.filter((f) => f.code !== fund.code))
        if (selectedFund?.code === fund.code) {
          setSelectedFund(null)
        }
      } else {
        showToast(res.detail || "删除失败", "error")
      }
    } catch (err: any) {
      showToast(err?.detail || "删除失败，请稍后重试", "error")
    } finally {
      setDeleting(false)
      setDeleteConfirmFund(null)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "-"
    return dateStr.split(" ")[0]
  }

  const handleViewReport = async (fund: FundItem, quarter: string) => {
    setReportModal({ fund, quarter })
    setReportLoading(true)
    setReportData(null)
    setReportError(null)

    try {
      const res = await api.getReportViewpoint(fund.code, quarter)
      setReportData(res.data || null)
    } catch (e) {
      setReportError(e instanceof Error ? e.message : "加载失败")
    } finally {
      setReportLoading(false)
    }
  }

  const startBatchFetch = async (quarter: string) => {
    const MAX_BATCH_SIZE = 3
    const INTERVAL_MS = 2000
    const TIMEOUT_MS = 120000

    const results: Array<{
      fund_code: string
      fund_name: string
      success: boolean
      viewpoint?: string
      manager?: string
      error?: string
    }> = []

    const batchQueue = [...funds]
    let currentIndex = 0
    let cancelled = false

    setBatchProgress({
      show: true,
      quarter,
      current: 0,
      total: funds.length,
      currentFund: "",
      results: [],
      cancelled: false
    })

    const checkCancelled = () => cancelled

    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

    const updateProgress = (index: number, fundName: string, newResults: typeof results) => {
      setBatchProgress(prev => prev ? {
        ...prev,
        current: index,
        currentFund: fundName,
        results: newResults
      } : null)
    }

    while (currentIndex < batchQueue.length && !checkCancelled()) {
      const batch = batchQueue.slice(currentIndex, currentIndex + MAX_BATCH_SIZE)
      
      const batchPromises = batch.map(async (fund) => {
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS)
          const res = await fetch(
            `http://localhost:8000/api/funds/${fund.code}/report/${quarter}`,
            { signal: controller.signal }
          )
          clearTimeout(timeoutId)

          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`)
          }

          const data = await res.json()
          return {
            fund_code: fund.code,
            fund_name: fund.name,
            success: true,
            viewpoint: data.data?.viewpoint || "",
            manager: data.data?.fund_info?.manager || ""
          }
        } catch (e: any) {
          return {
            fund_code: fund.code,
            fund_name: fund.name,
            success: false,
            error: e.message || "获取失败"
          }
        }
      })

      const batchResults = await Promise.all(batchPromises)
      results.push(...batchResults)

      currentIndex += MAX_BATCH_SIZE
      updateProgress(Math.min(currentIndex, batchQueue.length), batch[batch.length - 1]?.name || "", results)

      if (currentIndex < batchQueue.length && !checkCancelled()) {
        await delay(INTERVAL_MS)
      }
    }

    if (!cancelled) {
      setBatchProgress(prev => prev ? { ...prev, show: false } : null)
      sessionStorage.setItem('batchReports_quarter', quarter)
      sessionStorage.setItem('batchReports_data', JSON.stringify(results))
      router.push(`/reports`)
    } else {
      setBatchProgress(prev => prev ? { ...prev, show: false } : null)
    }
  }

  const cancelBatchFetch = () => {
    if (batchProgress) {
      setBatchProgress(prev => prev ? { ...prev, cancelled: true } : null)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="title">我的基金</div>
          <div className="muted">共 {funds.length} 只基金</div>
        </div>
        <div className="actions">
          <button className="button secondary" onClick={refreshFunds} disabled={loading}>
            {loading ? "刷新中..." : "刷新"}
          </button>
          <button className="button secondary" onClick={() => setShowQuarterSelectModal(true)} disabled={funds.length === 0}>
            批量获取报告观点
          </button>
          <button className="button" onClick={() => setShowImportModal(true)}>
            批量导入
          </button>
        </div>
      </div>

      {loading && funds.length === 0 && (
        <div className="card">
          <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
            加载中...
          </div>
        </div>
      )}

      {!loading && funds.length === 0 && (
        <div className="card">
          <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
            暂无基金数据，点击「批量导入」添加基金
          </div>
        </div>
      )}

      <div className="funds-grid">
        {funds.map((fund) => (
          <div
            key={fund.code}
            className="fund-card"
          >
            <div className="fund-card-content" onClick={() => setSelectedFund(fund)}>
              <div className="fund-header">
                <div className="fund-code">{fund.code}</div>
                <div className="fund-type">{fund.fund_type || "-"}</div>
              </div>
              <div className="fund-name">{fund.name}</div>
              <div className="fund-info">
                <span className="info-label">基金经理:</span>
                <span>{fund.manager || "-"}</span>
              </div>
              <div className="fund-info">
                <span className="info-label">基金公司:</span>
                <span>{fund.fund_company || "-"}</span>
              </div>
              <div className="fund-info">
                <span className="info-label">最新规模:</span>
                <span>{fund.latest_scale || "-"}</span>
              </div>
            </div>
            <button
              className="fund-delete-btn"
              onClick={(e) => {
                e.stopPropagation()
                setDeleteConfirmFund(fund)
              }}
              title="删除基金"
            >
              🗑️
            </button>
            <div className="quarter-buttons">
              {RECENT_QUARTERS.map((quarter) => (
                <button
                  key={quarter}
                  className="quarter-button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleViewReport(fund, quarter)
                  }}
                >
                  {quarter}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">批量导入基金</div>
              <button className="modal-close" onClick={() => setShowImportModal(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="muted" style={{ marginBottom: "12px" }}>
                请输入基金代码，每行一个或用逗号分隔
              </div>
              <textarea
                className="import-textarea"
                value={importCodes}
                onChange={(e) => setImportCodes(e.target.value)}
                placeholder={"例如:\n022755\n010409\n006780\n或: 022755, 010409, 006780"}
                rows={10}
              />
              {importResult && (
                <div className="import-result">
                  <div className="result-success">
                    成功: {importResult.success.length} 个
                  </div>
                  {importResult.success.length > 0 && (
                    <div className="result-list">
                      {importResult.success.map((s, i) => (
                        <div key={i} className="result-item success">
                          {s.code} {s.name || s.reason || ""}
                        </div>
                      ))}
                    </div>
                  )}
                  {importResult.failed.length > 0 && (
                    <>
                      <div className="result-failed">
                        失败: {importResult.failed.length} 个
                      </div>
                      <div className="result-list">
                        {importResult.failed.map((f, i) => (
                          <div key={i} className="result-item failed">
                            {f.code}: {f.reason}
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="button secondary" onClick={() => setShowImportModal(false)}>
                取消
              </button>
              <button className="button" onClick={handleBatchImport} disabled={importing}>
                {importing ? "导入中..." : "开始导入"}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedFund && (
        <div className="modal-overlay" onClick={() => setSelectedFund(null)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">{selectedFund.name}</div>
              <button className="modal-close" onClick={() => setSelectedFund(null)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <div className="detail-label">基金代码</div>
                  <div className="detail-value">{selectedFund.code}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">基金简称</div>
                  <div className="detail-value">{selectedFund.name}</div>
                </div>
                <div className="detail-item full-width">
                  <div className="detail-label">基金全称</div>
                  <div className="detail-value">{selectedFund.full_name || "-"}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">基金类型</div>
                  <div className="detail-value">{selectedFund.fund_type || "-"}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">基金经理</div>
                  <div className="detail-value">{selectedFund.manager || "-"}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">基金公司</div>
                  <div className="detail-value">{selectedFund.fund_company || "-"}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">托管银行</div>
                  <div className="detail-value">{selectedFund.custodian_bank || "-"}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">成立时间</div>
                  <div className="detail-value">{formatDate(selectedFund.establish_date)}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">最新规模</div>
                  <div className="detail-value">{selectedFund.latest_scale || "-"}</div>
                </div>
                <div className="detail-item full-width">
                  <div className="detail-label">业绩比较基准</div>
                  <div className="detail-value small">{selectedFund.benchmark || "-"}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmFund && (
        <div className="modal-overlay" onClick={() => setDeleteConfirmFund(null)}>
          <div className="modal modal-confirm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">确认删除</div>
              <button className="modal-close" onClick={() => setDeleteConfirmFund(null)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="confirm-message">
                确定要删除该基金吗？此操作不可撤销
              </div>
              <div className="confirm-fund-info">
                <strong>{deleteConfirmFund.code}</strong> - {deleteConfirmFund.name}
              </div>
            </div>
            <div className="modal-footer">
              <button className="button secondary" onClick={() => setDeleteConfirmFund(null)}>
                取消
              </button>
              <button
                className="button danger"
                onClick={() => handleDeleteFund(deleteConfirmFund)}
                disabled={deleting}
              >
                {deleting ? "删除中..." : "确认删除"}
              </button>
            </div>
          </div>
        </div>
      )}

      {reportModal && (
        <div className="modal-overlay" onClick={() => setReportModal(null)}>
          <div className="modal modal-report" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                {reportModal.fund.name} {reportModal.quarter} 季报观点
              </div>
              <button className="modal-close" onClick={() => setReportModal(null)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              {reportLoading && (
                <div className="report-loading">
                  <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
                    加载中...
                  </div>
                </div>
              )}
              {reportError && (
                <div className="report-error">
                  <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
                    {reportError}
                  </div>
                </div>
              )}
              {!reportLoading && !reportError && reportData && (
                <div className="report-content">
                  {reportData.fund_info?.manager && (
                    <div className="report-manager">
                      基金经理：{reportData.fund_info.manager}
                    </div>
                  )}
                  <div className="report-viewpoint">
                    {reportData.viewpoint || "暂无观点"}
                  </div>
                </div>
              )}
              {!reportLoading && !reportError && !reportData && (
                <div className="report-empty">
                  <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
                    未找到报告
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}

      {showQuarterSelectModal && (
        <div className="modal-overlay" onClick={() => setShowQuarterSelectModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">选择报告期</div>
              <button className="modal-close" onClick={() => setShowQuarterSelectModal(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="muted" style={{ marginBottom: "16px" }}>
                请选择要批量获取的报告期（共 {funds.length} 只基金）
              </div>
              <div className="quarter-select-grid">
                {RECENT_QUARTERS.map((quarter) => (
                  <button
                    key={quarter}
                    className="quarter-select-button"
                    onClick={() => {
                      setShowQuarterSelectModal(false)
                      startBatchFetch(quarter)
                    }}
                  >
                    {quarter}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {batchProgress && batchProgress.show && (
        <div className="modal-overlay">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">批量获取进度</div>
            </div>
            <div className="modal-body">
              <div className="batch-progress-container">
                <div className="batch-progress-info">
                  <div className="batch-progress-quarter">
                    报告期: {batchProgress.quarter}
                  </div>
                  <div className="batch-progress-stats">
                    {batchProgress.current} / {batchProgress.total} 只基金
                  </div>
                </div>
                
                <div className="batch-progress-bar-wrapper">
                  <div 
                    className="batch-progress-bar"
                    style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
                  />
                </div>
                
                <div className="batch-progress-current">
                  正在获取: {batchProgress.currentFund || "准备中..."}
                </div>
                
                {batchProgress.results.length > 0 && (
                  <div className="batch-progress-summary">
                    <span className="success-count">
                      ✓ 成功: {batchProgress.results.filter(r => r.success).length}
                    </span>
                    <span className="failed-count">
                      ✗ 失败: {batchProgress.results.filter(r => !r.success).length}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="button danger" onClick={cancelBatchFetch}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
