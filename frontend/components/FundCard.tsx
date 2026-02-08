import Link from "next/link"

import { FundItem } from "@/lib/api"

type FundCardProps = {
  fund: FundItem
  onGenerate: (fundCode: string) => void
  onDelete: (fundCode: string) => void
}

export default function FundCard({
  fund,
  onGenerate,
  onDelete
}: FundCardProps) {
  const podcast = fund.podcast

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
      {podcast ? (
        <div className="actions">
          <div className="podcast-meta muted">
            <span>{podcast.report_period}</span>
            <span>{podcast.status}</span>
          </div>
          {podcast.status === "completed" ? (
            <Link className="link" href={`/podcast/${podcast.id}`}>
              播放
            </Link>
          ) : (
            <button
              className="button secondary"
              onClick={() => onGenerate(fund.code)}
            >
              重新生成
            </button>
          )}
        </div>
      ) : (
        <button className="button" onClick={() => onGenerate(fund.code)}>
          生成播客
        </button>
      )}
      {podcast?.status === "failed" && (
        <div className="muted">失败原因：{podcast.error_msg || "未知错误"}</div>
      )}
    </div>
  )
}
