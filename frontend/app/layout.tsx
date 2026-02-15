import type { ReactNode } from "react"
import Link from "next/link"

import "./globals.css"

export const metadata = {
  title: "基金播客 MVP",
  description: "基金季报观点播客解读"
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <nav className="nav">
          <div className="nav-container">
            <Link href="/" className="nav-brand">
              基金播客
            </Link>
            <div className="nav-links">
              <Link href="/" className="nav-link">
                首页
              </Link>
              <Link href="/my-funds" className="nav-link">
                我的基金
              </Link>
            </div>
          </div>
        </nav>
        <div className="container">{children}</div>
      </body>
    </html>
  )
}
