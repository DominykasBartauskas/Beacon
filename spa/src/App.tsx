import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { beaconApi, type Dashboard, type NewsItem } from './api/client'

type NavItem = { id: string; label: string; icon: ReactNode; badge?: string }
type Story = { id: string; category: string; title: string; summary: string; source: string; time: string; tone: 'cool' | 'blue' | 'warm'; featured?: boolean; url?: string | null; published?: string }

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: <GridIcon /> },
  { id: 'ai-research', label: 'AI Research', icon: <PulseIcon />, badge: '8' },
  { id: 'models-releases', label: 'Models & Releases', icon: <LayersIcon /> },
  { id: 'ai-engineering', label: 'AI Engineering', icon: <BriefingIcon /> },
  { id: 'software-development', label: 'Software Development', icon: <GridIcon /> },
  { id: 'tools-platforms', label: 'Tools & Platforms', icon: <LayersIcon /> },
  { id: 'ai-products-applications', label: 'AI Products & Applications', icon: <PulseIcon /> },
  { id: 'safety-security', label: 'Safety & Security', icon: <BriefingIcon /> },
  { id: 'saved-stories', label: 'Saved Stories', icon: <BookmarkIcon /> },
]

const sampleStories: Story[] = [
  { id: 'multimodal-benchmarks', category: 'AI Research', title: 'A new multimodal benchmark focuses on reasoning through ambiguous scenes', summary: 'The fictional study compares how systems handle incomplete visual evidence and conflicting instructions.', source: 'Beacon sample desk', time: 'Demo · 18 min', tone: 'blue', featured: true },
  { id: 'context-model', category: 'Models & Releases', title: 'A sample long-context model release puts traceability at the center', summary: 'Its imagined release notes highlight source references, predictable retrieval, and cleaner handoffs.', source: 'Beacon sample desk', time: 'Demo · 42 min', tone: 'cool' },
  { id: 'evaluation-loop', category: 'AI Engineering', title: 'Teams are sketching a lighter evaluation loop for fast-moving prompts', summary: 'The demo workflow pairs representative tasks with a small, repeatable human review checkpoint.', source: 'Beacon sample desk', time: 'Demo · 1 hr', tone: 'warm' },
  { id: 'review-assistant', category: 'Software Development', title: 'A code review assistant concept is designed around small, explainable diffs', summary: 'The prototype imagines concise context, clear uncertainty, and a deliberate approval step.', source: 'Beacon sample desk', time: 'Demo · 2 hr', tone: 'blue' },
  { id: 'workflow-platform', category: 'Tools & Platforms', title: 'A workspace platform prototype connects experiments without hiding the seams', summary: 'The sample design keeps runs, prompts, and feedback visible in one calm working surface.', source: 'Beacon sample desk', time: 'Demo · 3 hr', tone: 'cool' },
  { id: 'research-companion', category: 'AI Products & Applications', title: 'A research companion concept helps turn reading lists into useful questions', summary: 'The fictional product clusters notes and drafts follow-ups without presenting them as conclusions.', source: 'Beacon sample desk', time: 'Demo · 4 hr', tone: 'blue' },
  { id: 'red-team', category: 'Safety & Security', title: 'A red-team exercise explores safer defaults for tool-using assistants', summary: 'The sample scenario uses permission boundaries and clear escalation paths for sensitive actions.', source: 'Beacon sample desk', time: 'Demo · 5 hr', tone: 'warm' },
]

type SampleNotification = { id: string; kind: 'digest' | 'topic' | 'source'; title: string; detail: string; time: string; unread: boolean }

const sampleNotifications: SampleNotification[] = [
  { id: 'daily-digest', kind: 'digest', title: 'Your morning digest is ready', detail: '6 sample stories across AI Research and Tools & Platforms.', time: '12 min ago', unread: true },
  { id: 'topic-spike', kind: 'topic', title: 'Evaluation tooling is picking up', detail: 'A topic you follow appeared in 3 demo stories today.', time: '1 hr ago', unread: true },
  { id: 'new-source', kind: 'source', title: 'A new sample source was added', detail: 'Beacon sample desk is now part of your Local sources.', time: 'Yesterday', unread: false },
  { id: 'saved-reminder', kind: 'digest', title: 'Two saved stories are waiting', detail: 'They have been in Saved Stories since last week.', time: '2 days ago', unread: false },
]

const categoryTones: Record<string, Story['tone']> = {
  'AI Research': 'blue',
  'Models & Releases': 'cool',
  'AI Engineering': 'warm',
  'Software Development': 'blue',
  'Tools & Platforms': 'cool',
  'AI Products & Applications': 'blue',
  'Safety & Security': 'warm',
}

function relativeTime(iso: string): string {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (!Number.isFinite(minutes) || minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  const days = Math.round(hours / 24)
  return days === 1 ? 'yesterday' : `${days} d ago`
}

function toStory(item: NewsItem, index: number): Story {
  return {
    id: item.id,
    category: item.category,
    title: item.title,
    summary: item.summary,
    source: item.source,
    time: relativeTime(item.published_at),
    tone: categoryTones[item.category] ?? 'blue',
    featured: index === 0,
    url: item.url,
    published: item.published_at,
  }
}

const notificationGlyphs: Record<SampleNotification['kind'], string> = { digest: '◒', topic: '◫', source: '✦' }

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

function StoryCard({ story }: { story: Story }) {
  return <article className={`story-card ${story.featured ? 'story-card--featured' : ''}`}>
    <div className={`story-visual story-visual--${story.tone}`} aria-hidden="true"><span className="visual-orb" /><span className="visual-line visual-line--one" /><span className="visual-line visual-line--two" /><span className="visual-square" /></div>
    <div className="story-copy"><div className="story-meta"><span>{story.category}</span><time dateTime={story.published}>{story.time}</time></div><h3>{story.title}</h3><p>{story.summary}</p><div className="story-footer"><span>{story.source}</span>{story.url ? <a className="icon-button story-action" href={story.url} target="_blank" rel="noreferrer" aria-label={`Open ${story.title}`}><ArrowIcon /></a> : <button className="icon-button story-action" type="button" aria-label={`Open ${story.title}`}><ArrowIcon /></button>}</div></div>
  </article>
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [stories, setStories] = useState<Story[]>(sampleStories)
  const [activeNav, setActiveNav] = useState('overview')
  const [activeFilter, setActiveFilter] = useState('All')
  const [query, setQuery] = useState('')
  const [notifications, setNotifications] = useState(sampleNotifications)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const notificationsRef = useRef<HTMLDivElement>(null)
  useEffect(() => { beaconApi.dashboard().then(setDashboard).catch(() => undefined) }, [])
  useEffect(() => {
    beaconApi.news()
      .then((list) => { if (list.items.length > 0) setStories(list.items.map(toStory)) })
      .catch(() => undefined)
  }, [])
  useEffect(() => {
    if (!notificationsOpen) return
    const onPointerDown = (event: MouseEvent) => { if (!notificationsRef.current?.contains(event.target as Node)) setNotificationsOpen(false) }
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') setNotificationsOpen(false) }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => { document.removeEventListener('mousedown', onPointerDown); document.removeEventListener('keydown', onKeyDown) }
  }, [notificationsOpen])
  const metrics = dashboard?.metrics ?? fallbackMetrics
  const unreadCount = notifications.filter((item) => item.unread).length
  const markAllRead = () => setNotifications((items) => items.map((item) => ({ ...item, unread: false })))
  const markRead = (id: string) => setNotifications((items) => items.map((item) => item.id === id ? { ...item, unread: false } : item))
  const visibleStories = useMemo(() => activeFilter === 'All' ? stories : stories.filter((story) => story.category === activeFilter), [activeFilter, stories])
  const greeting = activeNav === 'overview' ? 'Your AI signal, in focus.' : navItems.find((item) => item.id === activeNav)?.label ?? 'Your AI signal, in focus.'

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Beacon home"><span className="brand-mark">b</span><span>Beacon</span></a>
      <div className="workspace-label"><span className="workspace-dot" />YOUR SPACE</div>
      <nav className="side-nav" aria-label="Dashboard navigation">{navItems.map((item) => <button key={item.id} type="button" className={activeNav === item.id ? 'nav-item active' : 'nav-item'} onClick={() => setActiveNav(item.id)}><span className="nav-icon">{item.icon}</span><span>{item.label}</span>{item.badge && <span className="nav-badge">{item.badge}</span>}</button>)}</nav>
      </aside>
    <main className="dashboard-main">
      <header className="topbar"><div className="topbar-metrics" aria-label="AI dashboard summary">{metrics.map((metric) => <div className="topbar-metric" key={metric.label}><p>{metric.label}</p><span><strong>{metric.value}</strong><small>{metric.change}</small></span></div>)}</div><div className="topbar-actions"><div className="search-field"><div className="search-control"><SearchIcon /><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your feed" aria-label="Search your feed" /></div></div><div className="notifications" ref={notificationsRef}><button className="icon-button" type="button" aria-haspopup="dialog" aria-expanded={notificationsOpen} aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'} onClick={() => setNotificationsOpen((open) => !open)}><BellIcon />{unreadCount > 0 && <i className="notification-dot" />}</button>{notificationsOpen && <div className="notifications-panel" role="dialog" aria-label="Notifications"><header><h2>Notifications</h2>{unreadCount > 0 && <button type="button" onClick={markAllRead}>Mark all read</button>}</header><ul>{notifications.map((item) => <li key={item.id}><button type="button" className={item.unread ? 'notification unread' : 'notification'} onClick={() => markRead(item.id)}><span className="notification-glyph" aria-hidden="true">{notificationGlyphs[item.kind]}</span><span className="notification-body"><strong>{item.title}</strong><small>{item.detail}</small><em>{item.time}</em></span>{item.unread && <span className="notification-unread" aria-label="Unread" />}</button></li>)}</ul><footer>Sample notifications · the API does not serve these yet</footer></div>}</div><button className="mobile-avatar" type="button" aria-label="Account">JD</button></div></header>
      <div className="dashboard-scroll">
      <section className="welcome" aria-labelledby="page-title"><div><p className="eyebrow"><span />MONDAY, SEPTEMBER 21</p><h1 id="page-title">{greeting}</h1><p className="welcome-copy">A thoughtful starting point for the ideas, releases, and working practices shaping AI.</p></div></section>
      <section className="feed-section" aria-labelledby="radar-heading"><div className="section-heading"><div><p className="eyebrow"><span />CURATED FOR YOU</p><h2 id="radar-heading">On your radar</h2></div><button className="view-all" type="button">View sample archive <ArrowIcon /></button></div><div className="filters" aria-label="Filter sample stories">{['All', 'AI Research', 'Models & Releases', 'AI Engineering', 'Software Development', 'Tools & Platforms', 'AI Products & Applications', 'Safety & Security'].map((filter) => <button key={filter} type="button" className={activeFilter === filter ? 'filter active' : 'filter'} onClick={() => setActiveFilter(filter)}>{filter}</button>)}</div>{visibleStories.length > 0 ? <div className="stories">{visibleStories.map((story) => <StoryCard key={story.id} story={story} />)}</div> : <p className="feed-empty">Nothing in {activeFilter} yet. Other categories arrive as more sources are added.</p>}</section>
      <footer>Beacon concept dashboard <span>•</span> Sample content only</footer>
      </div>
    </main>
  </div>
}
