"use client"

import { useEffect, useState } from "react"
import Link from "next/link"

import PodcastPlayer from "@/components/PodcastPlayer"
import Transcript from "@/components/Transcript"
import { api, PodcastItem } from "@/lib/api"

type PageProps = {
  params: { id: string }
}

export default function PodcastPage({ params }: PageProps) {
  const [podcast, setPodcast] = useState<PodcastItem | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      const res = await api.getPodcast(Number(params.id))
      setPodcast(res.data || null)
      setLoading(false)
    }
    load()
  }, [params.id])

  if (loading) {
    return <div className="muted">加载中...</div>
  }

  if (!podcast) {
    return <div className="muted">未找到播客</div>
  }

  return (
    <div>
      <div className="actions">
        <Link className="link" href="/">
          返回
        </Link>
      </div>
      <div className="card">
        <div className="title">{podcast.title || "播客详情"}</div>
        <div className="muted">状态：{podcast.status}</div>
        <PodcastPlayer podcast={podcast} />
        <Transcript items={podcast.transcript || []} />
      </div>
    </div>
  )
}
