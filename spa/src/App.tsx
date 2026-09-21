import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { beaconApi, type Dashboard } from './api/client'

type NavItem = { id: string; label: string; icon: ReactNode; badge?: string }
type SampleStory = { id: string; category: string; title: string; summary: string; source: string; time: string; tone: 'cool' | 'blue' | 'warm'; featured?: boolean }

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: <GridIcon /> },
  { id: 'local', label: 'Local pulse', icon: <PulseIcon />, badge: '8' },
  { id: 'topics', label: 'Topics', icon: <LayersIcon /> },
  { id: 'briefing', label: 'Daily briefing', icon: <BriefingIcon /> },
  { id: 'saved', label: 'Saved', icon: <BookmarkIcon /> },
]

const sampleStories: SampleStory[] = [
  { id: 'night-market', category: 'Community', title: 'A neighborhood night market is taking shape for next month', summary: 'Organizers are collecting vendor ideas and inviting residents to help shape the first evening edition.', source: 'Beacon sample desk', time: 'Demo · 18 min', tone: 'blue', featured: true },
  { id: 'library', category: 'Civic life', title: 'Library hours are being reimagined with community input', summary: 'A short survey is collecting ideas for quieter mornings and later study sessions.', source: 'Beacon sample desk', time: 'Demo · 42 min', tone: 'cool' },
  { id: 'crosswalk', category: 'Getting around', title: 'A safer crossing is proposed near the school entrance', summary: 'The early concept adds better visibility and a slower approach for morning arrivals.', source: 'Beacon sample desk', time: 'Demo · 1 hr', tone: 'warm' },
  { id: 'artists', category: 'Culture', title: 'Open studios will put emerging artists on the neighborhood map', summary: 'The weekend route connects workspaces, makers and a handful of temporary exhibits.', source: 'Beacon sample desk', time: 'Demo · 2 hr', tone: 'blue' },
]

const fallbackMetrics = [
  { label: 'Stories in view', value: '08', change: 'Sample selection' },
  { label: 'Topics followed', value: '12', change: 'Across your neighborhood' },
  { label: 'Saved for later', value: '03', change: 'Ready when you are' },
]

function IconFrame({ children }: { children: ReactNode }) { return <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">{children}</svg> }
function GridIcon() { return <IconFrame><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></IconFrame> }
function PulseIcon() { return <IconFrame><path d="M3 12h4l2.1-5 4 10 2-5H21" /></IconFrame> }
function LayersIcon() { return <IconFrame><path d="m12 3 8 4.5-8 4.5-8-4.5L12 3Z" /><path d="m4 12 8 4.5 8-4.5" /><path d="m4 16.5 8 4.5 8-4.5" /></IconFrame> }
function BriefingIcon() { return <IconFrame><path d="M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /><path d="M8 8h8M8 12h8M8 16h5" /></IconFrame> }
function BookmarkIcon() { return <IconFrame><path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.7L6 21V4.5Z" /></IconFrame> }
function SearchIcon() { return <IconFrame><circle cx="10.8" cy="10.8" r="5.8" /><path d="m16 16 4 4" /></IconFrame> }
function BellIcon() { return <IconFrame><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></IconFrame> }
function ArrowIcon() { return <IconFrame><path d="M5 12h13M13 6l6 6-6 6" /></IconFrame> }

function StoryCard({ story }: { story: SampleStory }) {
  return <article className={`story-card ${story.featured ? 'story-card--featured' : ''}`}>
    <div className={`story-visual story-visual--${story.tone}`} aria-hidden="true"><span className="visual-orb" /><span className="visual-line visual-line--one" /><span className="visual-line visual-line--two" /><span className="visual-square" /></div>
    <div className="story-copy"><div className="story-meta"><span>{story.category}</span><time>{story.time}</time></div><h3>{story.title}</h3><p>{story.summary}</p><div className="story-footer"><span>{story.source}</span><button className="icon-button story-action" type="button" aria-label={`Open ${story.title}`}><ArrowIcon /></button></div></div>
  </article>
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [activeNav, setActiveNav] = useState('overview')
  const [activeFilter, setActiveFilter] = useState('All')
  useEffect(() => { beaconApi.dashboard().then(setDashboard).catch(() => undefined) }, [])
  const metrics = dashboard?.metrics ?? fallbackMetrics
  const visibleStories = useMemo(() => activeFilter === 'All' ? sampleStories : sampleStories.filter((story) => story.category === activeFilter), [activeFilter])
  const greeting = activeNav === 'overview' ? 'Your neighborhood, in focus.' : navItems.find((item) => item.id === activeNav)?.label ?? 'Your neighborhood, in focus.'

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Beacon home"><span className="brand-mark">b</span><span>Beacon</span></a>
      <div className="workspace-label"><span className="workspace-dot" />YOUR SPACE</div>
      <nav className="side-nav" aria-label="Dashboard navigation">{navItems.map((item) => <button key={item.id} type="button" className={activeNav === item.id ? 'nav-item active' : 'nav-item'} onClick={() => setActiveNav(item.id)}><span className="nav-icon">{item.icon}</span><span>{item.label}</span>{item.badge && <span className="nav-badge">{item.badge}</span>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-callout"><span className="callout-icon">✦</span><div><strong>Make it yours</strong><p>Choose the places and topics you care about.</p></div><button type="button" aria-label="Set up your dashboard">→</button></div><button className="profile" type="button"><span className="avatar">JD</span><span><strong>Jamie Doe</strong><small>Personal space</small></span><span className="more">•••</span></button></div>
    </aside>
    <main className="dashboard-main">
      <header className="topbar"><button className="location-button" type="button"><span className="location-pin">⌖</span>Northside <span>⌄</span></button><div className="topbar-actions"><button className="search-control" type="button"><SearchIcon /><span>Search your feed</span><kbd>⌘ K</kbd></button><button className="icon-button" type="button" aria-label="Notifications"><BellIcon /><i className="notification-dot" /></button><button className="mobile-avatar" type="button" aria-label="Account">JD</button></div></header>
      <section className="welcome" aria-labelledby="page-title"><div><p className="eyebrow"><span />MONDAY, SEPTEMBER 21</p><h1 id="page-title">{greeting}</h1><p className="welcome-copy">A thoughtful starting point for what’s being imagined, discussed, and built around you.</p></div><div className="demo-note"><span>◌</span><div><strong>Demo workspace</strong><p>Everything below is sample content.</p></div></div></section>
      <section className="metrics" aria-label="Neighborhood summary">{metrics.map((metric, index) => <article className="metric" key={metric.label}><div className={`metric-icon metric-icon--${index}`}><span>{index === 0 ? '◒' : index === 1 ? '◫' : '♡'}</span></div><div><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.change}</small></div></article>)}</section>
      <section className="feed-section" aria-labelledby="radar-heading"><div className="section-heading"><div><p className="eyebrow"><span />CURATED FOR YOU</p><h2 id="radar-heading">On your radar</h2></div><button className="view-all" type="button">View sample archive <ArrowIcon /></button></div><div className="filters" aria-label="Filter sample stories">{['All', 'Community', 'Civic life', 'Getting around', 'Culture'].map((filter) => <button key={filter} type="button" className={activeFilter === filter ? 'filter active' : 'filter'} onClick={() => setActiveFilter(filter)}>{filter}</button>)}</div><div className="stories">{visibleStories.map((story) => <StoryCard key={story.id} story={story} />)}</div></section>
      <footer>Beacon concept dashboard <span>•</span> Sample content only</footer>
    </main>
  </div>
}
