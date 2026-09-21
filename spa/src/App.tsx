import { useEffect, useState } from 'react'
import { beaconApi, type Dashboard, type NewsItem } from './api/client'

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function StoryCard({ story }: { story: NewsItem }) {
  return (
    <article className="story-card">
      <div className="story-meta"><span>{story.category}</span><time>{formatDate(story.published_at)}</time></div>
      <h3>{story.title}</h3>
      <p>{story.summary}</p>
      <a href={story.url ?? '#'}>Read from {story.source} <span aria-hidden="true">→</span></a>
    </article>
  )
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [news, setNews] = useState<NewsItem[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([beaconApi.dashboard(), beaconApi.news()])
      .then(([nextDashboard, nextNews]) => {
        setDashboard(nextDashboard)
        setNews(nextNews.items)
      })
      .catch(() => setError('Beacon could not reach the local API. Start it on port 8100 and refresh.'))
  }, [])

  return (
    <main>
      <nav><a className="brand" href="/">Beacon<span>.</span></a><span className="status"><i />Live local signal</span></nav>
      <section className="hero">
        <p className="eyebrow">Good morning, neighbor</p>
        <h1>{dashboard?.headline ?? 'Finding your local signal…'}</h1>
        <p className="intro">A calm, useful view of the stories shaping your community.</p>
      </section>
      {error ? <p className="error" role="alert">{error}</p> : <>
        <section className="metrics" aria-label="Dashboard metrics">
          {dashboard?.metrics.map((metric) => <div className="metric" key={metric.label}><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.change}</small></div>)}
        </section>
        <section className="stories-section">
          <div className="section-heading"><div><p className="eyebrow">Fresh perspectives</p><h2>On the radar</h2></div><button type="button">Explore all stories</button></div>
          <div className="stories">{news.map((story) => <StoryCard key={story.id} story={story} />)}</div>
        </section>
      </>}
    </main>
  )
}
