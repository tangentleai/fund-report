"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

type ReportResult = {
  fund_code: string
  fund_name: string
  success: boolean
  viewpoint?: string
  manager?: string
  error?: string
}

export default function ReportsPage() {
  const router = useRouter()
  const [quarter, setQuarter] = useState("")
  const [results, setResults] = useState<ReportResult[]>([])
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)

  useEffect(() => {
    const savedQuarter = sessionStorage.getItem('batchReports_quarter')
    const savedData = sessionStorage.getItem('batchReports_data')
    
    if (savedQuarter && savedData) {
      try {
        setQuarter(savedQuarter)
        const parsed = JSON.parse(savedData)
        setResults(parsed)
      } catch (e) {
        console.error("解析数据失败", e)
      }
    } else {
      router.push('/my-funds')
    }
    setLoading(false)
  }, [router])

  const handleRetry = useCallback(async (fundCodes?: string[]) => {
    setRetrying(true)
    const fundsToRetry = fundCodes || results.filter(r => !r.success).map(r => r.fund_code)
    
    const newResults = [...results]
    
    for (const fundCode of fundsToRetry) {
      try {
        const res = await fetch(
          `http://localhost:8000/api/funds/${fundCode}/report/${quarter}`,
          { signal: AbortSignal.timeout(120000) }
        )
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        
        const data = await res.json()
        const index = newResults.findIndex(r => r.fund_code === fundCode)
        if (index !== -1) {
          newResults[index] = {
            ...newResults[index],
            success: true,
            viewpoint: data.data?.viewpoint || "",
            manager: data.data?.fund_info?.manager || "",
            error: undefined
          }
        }
      } catch (e: any) {
        const index = newResults.findIndex(r => r.fund_code === fundCode)
        if (index !== -1) {
          newResults[index] = {
            ...newResults[index],
            success: false,
            error: e.message || "获取失败"
          }
        }
      }
    }
    
    setResults(newResults)
    sessionStorage.setItem('batchReports_data', JSON.stringify(newResults))
    setRetrying(false)
  }, [results, quarter])

  const handleExportMarkdown = () => {
    const successful = results.filter(r => r.success)
    const failed = results.filter(r => !r.success)
    
    let markdown = `# 基金季度报告观点汇总\n\n`
    markdown += `**报告期**: ${quarter}\n`
    markdown += `**生成时间**: ${new Date().toLocaleString()}\n\n`
    markdown += `---\n\n`
    markdown += `## 汇总统计\n\n`
    markdown += `- 总基金数: ${results.length}\n`
    markdown += `- 成功获取: ${successful.length}\n`
    markdown += `- 获取失败: ${failed.length}\n\n`
    markdown += `---\n\n`
    
    if (successful.length > 0) {
      markdown += `## 成功获取的观点\n\n`
      for (const r of successful) {
        markdown += `### ${r.fund_name} (${r.fund_code})\n\n`
        if (r.manager) {
          markdown += `**基金经理**: ${r.manager}\n\n`
        }
        markdown += `${r.viewpoint || "暂无观点"}\n\n`
        markdown += `---\n\n`
      }
    }
    
    if (failed.length > 0) {
      markdown += `## 获取失败的基金\n\n`
      for (const r of failed) {
        markdown += `- ${r.fund_name} (${r.fund_code}): ${r.error}\n`
      }
    }
    
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `基金报告观点汇总_${quarter}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="container">
        <div className="header">
          <div>
            <div className="title">报告观点汇总</div>
          </div>
        </div>
        <div className="card">
          <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
            加载中...
          </div>
        </div>
      </div>
    )
  }

  const successful = results.filter(r => r.success)
  const failed = results.filter(r => !r.success)

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="title">报告观点汇总</div>
          <div className="muted">
            报告期: {quarter} | 成功: {successful.length} / {results.length}
          </div>
        </div>
        <div className="actions">
          <button className="button secondary" onClick={() => router.push("/my-funds")}>
            返回
          </button>
          {failed.length > 0 && (
            <button className="button secondary" onClick={() => handleRetry()} disabled={retrying}>
              {retrying ? "重试中..." : `重试失败 (${failed.length})`}
            </button>
          )}
          <button className="button" onClick={handleExportMarkdown}>
            导出 Markdown
          </button>
        </div>
      </div>

      {failed.length > 0 && (
        <div className="card" style={{ marginBottom: "16px", borderLeft: "4px solid #dc2626" }}>
          <div style={{ padding: "12px" }}>
            <div className="muted" style={{ marginBottom: "12px" }}>
              以下基金获取失败，可点击重试:
            </div>
            <div className="failed-list">
              {failed.map((r) => (
                <div key={r.fund_code} className="failed-item">
                  <span className="failed-name">{r.fund_name} ({r.fund_code})</span>
                  <span className="failed-error">{r.error}</span>
                  <button 
                    className="retry-btn"
                    onClick={() => handleRetry([r.fund_code])}
                    disabled={retrying}
                  >
                    重试
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="reports-list">
        {successful.map((r) => (
          <div key={r.fund_code} className="report-card">
            <div className="report-header">
              <div className="report-title">
                {r.fund_name} ({r.fund_code})
              </div>
              {r.manager && (
                <div className="report-manager">
                  基金经理: {r.manager}
                </div>
              )}
            </div>
            <div className="report-body">
              {r.viewpoint || "暂无观点"}
            </div>
          </div>
        ))}
      </div>

      {successful.length === 0 && failed.length > 0 && (
        <div className="card">
          <div className="muted" style={{ textAlign: "center", padding: "40px" }}>
            所有基金获取失败，请检查网络后重试
          </div>
        </div>
      )}
    </div>
  )
}
