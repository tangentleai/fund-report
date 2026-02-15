import Link from "next/link"
import { useState } from "react"

import { FundItem, PodcastItem } from "@/lib/api"

const AVAILABLE_QUARTERS = ["2025Q4", "2025Q3", "2025Q2", "2025Q1", "2024Q4", "2024Q3"]

type FundCardProps = {
  fund: FundItem
  onGenerate: (fundCode: string, reportPeriod: string) => void
  onDelete: (fundCode: string) => void
  onDeletePodcast: (podcastId: number) => void
  pollPodcast: (fundCode: string, podcastId: number) => void
}

export default function FundCard({
  fund,
  onGenerate,
  onDelete,
  onDeletePodcast,
  pollPodcast
}: FundCardProps) {
  const [selectedQuarter, setSelectedQuarter] = useState<string>("")
  const [showQuarterSelector, setShowQuarterSelector] = useState(false)
  const [quarterSelectorMode, setQuarterSelectorMode] = useState<"generate" | "view">("generate")

  const getPodcastForQuarter = (quarter: string): PodcastItem | undefined => {
    return fund.podcasts.find(p => p.report_period === quarter)
  }

  const getLatestPodcast = (): PodcastItem | undefined => {
    return fund.podcasts[0]
  }

  const handleGenerate = (quarter: string) => {
    onGenerate(fund.code, quarter)
    setShowQuarterSelector(false)
  }

  const handleViewReport = (quarter: string) => {
    setShowQuarterSelector(false)
  }

  const latestPodcast = getLatestPodcast()

  return (
    <div className="card">
      <div className="header">
        <div>
          <div className="title">{fund.name}</div>
          <div className="muted">
            {fund.manager} · {fund.fund_type || "基金"}
          </div>
        </div>
        <button className="button danger" onClick={() => onDelete(fund.code)}>
          删除
        </button>
      </div>

      {/* 已生成的播客列表 */}
      {fund.podcasts.length > 0 && (
        <div className="list">
          {fund.podcasts.map((podcast) => (
            <div key={podcast.id} className="card" style={{ margin: "8px 0", padding: "12px" }}>
              <div className="actions">
                <div className="podcast-meta muted">
                  <span>{podcast.report_period}</span>
                  <span>{podcast.status}</span>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <Link 
                    className="link" 
                    href={`/report/${fund.code}/${podcast.report_period}`}
                  >
                    查看报告
                  </Link>
                  {podcast.status === "completed" ? (
                    <Link className="link" href={`/podcast/${podcast.id}`}>
                      播放
                    </Link>
                  ) : (
                    <button
                      className="button secondary"
                      onClick={() => handleGenerate(podcast.report_period)}
                      style={{ fontSize: "14px" }}
                    >
                      重新生成
                    </button>
                  )}
                  <button
                    className="button danger"
                    onClick={() => onDeletePodcast(podcast.id)}
                    style={{ fontSize: "14px", padding: "4px 8px" }}
                  >
                    ×
                  </button>
                </div>
              </div>
              {podcast.status === "failed" && (
                <div className="muted" style={{ marginTop: "8px" }}>
                  失败原因：{podcast.error_msg || "未知错误"}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 生成新播客 */}
      <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
        {!showQuarterSelector ? (
          <>
            <button 
              className="button secondary" 
              onClick={() => {
                setQuarterSelectorMode("view")
                setShowQuarterSelector(true)
              }}
            >
              获取定期报告观点
            </button>
            <button 
              className="button" 
              onClick={() => {
                setQuarterSelectorMode("generate")
                setShowQuarterSelector(true)
              }}
            >
              生成新播客
            </button>
          </>
        ) : (
          <div className="card" style={{ padding: "12px", width: "100%" }}>
            <div className="muted" style={{ marginBottom: "8px" }}>
              {quarterSelectorMode === "view" ? "选择季度查看报告：" : "选择季度生成播客："}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {AVAILABLE_QUARTERS.map((quarter) => {
                const existing = getPodcastForQuarter(quarter)
                const linkHref = quarterSelectorMode === "view" 
                  ? `/report/${fund.code}/${quarter}`
                  : "#"
                return (
                  <Link
                    key={quarter}
                    href={linkHref}
                    style={{ textDecoration: "none" }}
                  >
                    <button
                      className={`button ${existing ? "secondary" : ""}`}
                      onClick={(e) => {
                        if (quarterSelectorMode === "generate") {
                          e.preventDefault()
                          handleGenerate(quarter)
                        } else {
                          setShowQuarterSelector(false)
                        }
                      }}
                      style={{ fontSize: "14px" }}
                    >
                      {quarter}
                      {existing && " (已生成)"}
                    </button>
                  </Link>
                )
              })}
            </div>
            <button
              className="button secondary"
              onClick={() => setShowQuarterSelector(false)}
              style={{ marginTop: "12px" }}
            >
              取消
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
