import { TranscriptItem } from "@/lib/api"

type TranscriptProps = {
  items: TranscriptItem[]
}

export default function Transcript({ items }: TranscriptProps) {
  if (!items?.length) {
    return <div className="muted">暂无文字稿</div>
  }

  return (
    <div className="transcript">
      {items.map((item) => (
        <div key={`${item.time}-${item.speaker}`} className="transcript-item">
          <strong>[{item.time}s]</strong> {item.speaker}：{item.text}
        </div>
      ))}
    </div>
  )
}
