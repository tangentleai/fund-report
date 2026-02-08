import { PodcastItem } from "@/lib/api"

type PodcastPlayerProps = {
  podcast: PodcastItem
}

export default function PodcastPlayer({ podcast }: PodcastPlayerProps) {
  if (!podcast.audio_url) {
    return <div className="muted">音频暂不可用</div>
  }
  const src = podcast.audio_url.startsWith("http")
    ? podcast.audio_url
    : `http://localhost:8000${podcast.audio_url}`
  return (
    <div className="player">
      <audio controls src={src} />
      <div className="muted">
        时长：{podcast.duration ? `${podcast.duration}s` : "未知"}
      </div>
    </div>
  )
}
