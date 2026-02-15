"use client"

import { useEffect, useState } from "react"
import Link from "next/link"

import { api } from "@/lib/api"

type PageProps = {
  params: { fundCode: string; reportPeriod: string }
}

type ReportData = {
  fund_code: string
  report_period: string
  viewpoint: string
  fund_info: {
    name?: string
    manager?: string
  }
}

export default function ReportPage({ params }: PageProps) {
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getReportViewpoint(params.fundCode, params.reportPeriod)
        setReport(res.data || null)
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [params.fundCode, params.reportPeriod])

  if (loading) {
    return <div className="muted">加载中...</div>
  }

  if (error) {
    return (
      <div>
        <div className="actions">
          <Link className="link" href="/">
            返回
          </Link>
        </div>
        <div className="card">
          <div className="title">加载失败</div>
          <div className="muted">{error}</div>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div>
        <div className="actions">
          <Link className="link" href="/">
            返回
          </Link>
        </div>
        <div className="muted">未找到报告</div>
      </div>
    )
  }

  return (
    <div>
      <div className="actions">
        <Link className="link" href="/">
          返回
        </Link>
      </div>
      <div className="card">
        <div className="title">
          {report.fund_info?.name || report.fund_code} {report.report_period} 季报观点
        </div>
        {report.fund_info?.manager && (
          <div className="muted" style={{ marginBottom: "12px" }}>
            基金经理：{report.fund_info.manager}
          </div>
        )}
        <div style={{ whiteSpace: "pre-wrap", lineHeight: "1.8" }}>
          {report.viewpoint || "暂无观点"}
        </div>
      </div>
    </div>
  )
}
