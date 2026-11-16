import { useMemo, useState } from 'react'
import {
  Activity, ArrowDownToLine, ArrowUpRight, AudioWaveform, Bell, Check,
  ChevronDown, CircleHelp, Clapperboard, Clock3, Command, Film, FolderOpen,
  Gauge, HardDrive, LayoutDashboard, Link2, ListVideo, LockKeyhole,
  MoreHorizontal, Play, Plus, Scissors, Search, Settings2, ShieldCheck,
  Sparkles, Upload, WandSparkles, X
} from 'lucide-react'

type Platform = 'YouTube' | 'Facebook' | 'Instagram' | 'Unknown'
type Project = { title: string; platform: Platform; duration: string; clips: number; status: string; date: string }

const initialProjects: Project[] = [
  { title: 'Founder interview — episode 08', platform: 'YouTube', duration: '48:32', clips: 8, status: 'Ready for review', date: 'Today' },
  { title: 'Studio conversation / live', platform: 'Facebook', duration: '1:12:09', clips: 10, status: 'Analysing source', date: 'Yesterday' },
  { title: 'Creative process breakdown', platform: 'Instagram', duration: '26:14', clips: 5, status: 'Exported', date: 'Nov 12' },
]

function detectPlatform(value: string): Platform {
  try {
    const host = new URL(value).hostname.toLowerCase().replace(/^www\./, '')
    if (host === 'youtube.com' || host === 'youtu.be' || host.endsWith('.youtube.com')) return 'YouTube'
    if (host === 'facebook.com' || host.endsWith('.facebook.com') || host === 'fb.watch') return 'Facebook'
    if (host === 'instagram.com' || host.endsWith('.instagram.com')) return 'Instagram'
  } catch { /* invalid / incomplete URL */ }
  return 'Unknown'
}

function App() {
  const [url, setUrl] = useState('')
  const [projects, setProjects] = useState(initialProjects)
  const [notice, setNotice] = useState('')
  const [active, setActive] = useState('Overview')
  const [clipCount, setClipCount] = useState('10')
  const [rights, setRights] = useState(false)
  const platform = useMemo(() => detectPlatform(url.trim()), [url])

  const submit = () => {
    if (!url.trim()) return setNotice('Add a video URL to create a project.')
    if (platform === 'Unknown') return setNotice('Enter a valid YouTube, Facebook or Instagram URL.')
    if (!rights) return setNotice('Please confirm that you own, licensed, or are otherwise authorized to process this content.')
    setNotice('Project intake UI is ready. Connect an approved platform adapter or upload an authorized source file to enable processing.')
  }

  const nav = [
    { label: 'Overview', icon: LayoutDashboard },
    { label: 'Projects', icon: FolderOpen },
    { label: 'Clip library', icon: ListVideo },
    { label: 'Editing studio', icon: Scissors },
  ]
  const tools = [
    { label: 'Processing queue', icon: Activity },
    { label: 'Rights & sources', icon: ShieldCheck },
    { label: 'Settings', icon: Settings2 },
  ]

  return (
    <><div className="desktop-warning"><div><LockKeyhole size={28}/><h1>ClippingAI is built for desktop.</h1><p>Open this workspace on a desktop computer or laptop for the full editing experience.</p></div></div><div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><span /></div>
          <div><div className="brand-name">Clipping<span>AI</span></div><div className="brand-caption">VIDEO WORKSPACE</div></div>
        </div>
        <button className="workspace-switch"><div className="workspace-avatar">C</div><span><b>Creator workspace</b><small>Personal studio</small></span><ChevronDown size={15}/></button>
        <div className="nav-label">WORKSPACE</div>
        <nav>{nav.map(({label, icon: Icon}) => <button key={label} onClick={() => setActive(label)} className={`nav-item ${active === label ? 'active' : ''}`}><Icon size={17}/>{label}{label === 'Clip library' && <span className="nav-count">23</span>}</button>)}</nav>
        <div className="nav-label tools-label">MANAGE</div>
        <nav>{tools.map(({label, icon: Icon}) => <button key={label} onClick={() => setActive(label)} className={`nav-item ${active === label ? 'active' : ''}`}><Icon size={17}/>{label}</button>)}</nav>
        <div className="sidebar-bottom">
          <div className="storage-card">
            <div className="storage-heading"><HardDrive size={14}/> Storage <span>2.4 / 20 GB</span></div>
            <div className="storage-track"><i /></div>
            <small>Optimized proxy storage</small>
          </div>
          <button className="profile"><div className="profile-avatar">M</div><span><b>Your workspace</b><small>Local preview</small></span><MoreHorizontal size={17}/></button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><i>/</i><b>{active}</b></div>
          <div className="top-actions"><div className="command-search"><Search size={15}/><span>Search anything</span><kbd><Command size={11}/> K</kbd></div><button className="icon-button" aria-label="Help"><CircleHelp size={17}/></button><button className="icon-button" aria-label="Notifications"><Bell size={17}/><i className="notification-dot"/></button><div className="top-avatar">M</div></div>
        </header>

        <div className="content">
          <section className="welcome-row">
            <div><div className="eyebrow"><span className="live-dot"/> YOUR CREATIVE WORKSPACE</div><h1>Make every moment <em>count.</em></h1><p>Turn long-form footage into short-form stories worth watching.</p></div>
            <button className="quiet-button"><Clock3 size={15}/> Activity <ArrowUpRight size={14}/></button>
          </section>

          <section className="hero-grid">
            <div className="intake-panel panel">
              <div className="panel-top"><div><div className="section-kicker">NEW PROJECT <span>01</span></div><h2>Start with a source</h2><p>Paste a supported video link or upload an authorized file.</p></div><div className="panel-icon"><WandSparkles size={19}/></div></div>
              <div className="url-label">VIDEO URL</div>
              <div className="url-input-wrap"><Link2 size={17}/><input value={url} onChange={e => {setUrl(e.target.value); setNotice('')}} placeholder="Paste a YouTube, Facebook or Instagram link…" /><button className="paste-button" onClick={() => navigator.clipboard?.readText().then(setUrl).catch(() => setNotice('Clipboard access is unavailable. Paste your URL into the field.'))}>Paste</button></div>
              <div className="source-meta"><div className="platforms"><span className="platform-chip yt">YT</span><span className="platform-chip fb">f</span><span className="platform-chip ig">◎</span><span>Supported sources</span></div><span className="source-detected">{platform !== 'Unknown' ? `${platform} detected` : 'URL detection'}</span></div>
              <div className="intake-divider"/>
              <div className="options-row"><div><span className="field-label">CLIPS TO FIND</span><small>Top-ranked moments, no duplicates</small></div><div className="select-wrap"><select value={clipCount} onChange={e => setClipCount(e.target.value)}><option value="5">5 clips</option><option value="8">8 clips</option><option value="10">10 clips</option></select><ChevronDown size={13}/></div></div>
              <div className="rights-check"><input type="checkbox" checked={rights} onChange={e => setRights(e.target.checked)}/><span>I own this content, have permission / a suitable license, or have another valid legal basis to process it.</span><ShieldCheck size={15}/></div>
              <div className="intake-footer"><button className="upload-button" onClick={() => setNotice('Authorized file upload will be enabled with the media-ingestion service.')}><Upload size={15}/> Upload file</button><button className="primary-button" onClick={submit}><Sparkles size={15}/> Analyse source <ArrowUpRight size={14}/></button></div>
              {notice && <div className="notice"><i/><span>{notice}</span><button onClick={() => setNotice('')}><X size={14}/></button></div>}
              <div className="intake-footnote"><LockKeyhole size={12}/> Processing only through authorized access paths. Platform access varies.</div>
            </div>

            <div className="insight-panel panel">
              <div className="section-kicker">THE CLIPPINGAI APPROACH <span>02</span></div>
              <div className="insight-visual">
                <div className="visual-orbit orbit-one"/><div className="visual-orbit orbit-two"/>
                <div className="visual-core"><AudioWaveform size={29}/></div>
                <div className="visual-tag tag-a"><span className="tag-dot"/> MOMENT DETECTED <b>00:42</b></div>
                <div className="visual-tag tag-b"><span className="tag-dot sage"/> STRONG HOOK <b>92/100</b></div>
                <div className="visual-line line-a"/><div className="visual-line line-b"/>
              </div>
              <div className="insight-copy"><h3>Real moments.<br/><em>Thoughtful edits.</em></h3><p>AI finds the strongest parts of your original footage. You stay in control of every cut.</p></div>
              <div className="insight-footer"><span><Check size={13}/> Original source footage</span><span><Check size={13}/> You approve every clip</span></div>
            </div>
          </section>

          <section className="stats-row">
            <div className="stat-card"><div className="stat-icon"><Clapperboard size={16}/></div><div><small>PROJECTS CREATED</small><strong>24</strong><span className="stat-note">Across your workspace</span></div><ArrowUpRight className="stat-arrow" size={15}/></div>
            <div className="stat-card"><div className="stat-icon"><Scissors size={16}/></div><div><small>CLIPS GENERATED</small><strong>186</strong><span className="stat-note">Original moments extracted</span></div><ArrowUpRight className="stat-arrow" size={15}/></div>
            <div className="stat-card"><div className="stat-icon"><Gauge size={16}/></div><div><small>EXPORT FORMAT</small><strong>9:16</strong><span className="stat-note">Vertical · Full HD target</span></div><ArrowUpRight className="stat-arrow" size={15}/></div>
          </section>

          <section className="projects-section">
            <div className="projects-heading"><div><div className="section-kicker">YOUR WORK <span>03</span></div><h2>Recent projects</h2></div><button className="view-all" onClick={() => setActive('Projects')}>View all projects <ArrowUpRight size={14}/></button></div>
            <div className="project-table panel">
              <div className="table-head"><span>PROJECT</span><span>SOURCE</span><span>DURATION</span><span>CLIPS</span><span>STATUS</span><span>UPDATED</span><span/></div>
              {projects.map((p, i) => <div className="project-row" key={p.title}><div className="project-name"><div className={`project-thumb thumb-${i}`}><Film size={18}/><span>{String(i+1).padStart(2,'0')}</span></div><div><b>{p.title}</b><small>Project ID · CLP-00{8-i}</small></div></div><div className="source-cell"><span className={`source-badge ${p.platform.toLowerCase()}`}>{p.platform === 'YouTube' ? 'YT' : p.platform === 'Facebook' ? 'f' : '◎'}</span>{p.platform}</div><span className="table-muted">{p.duration}</span><span className="clip-number">{p.clips.toString().padStart(2,'0')} <small>clips</small></span><span><i className={`status-dot ${i === 1 ? 'processing' : i === 2 ? 'done' : ''}`}/>{p.status}</span><span className="table-muted">{p.date}</span><button className="row-more" aria-label="Project options"><MoreHorizontal size={17}/></button></div>)}
              <div className="table-bottom"><span>Showing {projects.length} of 24 projects</span><button onClick={() => setProjects([...projects, {title:'New workspace project', platform:'Unknown', duration:'—', clips:Number(clipCount), status:'Draft', date:'Just now'}])}><Plus size={13}/> Add sample row</button></div>
            </div>
          </section>

          <footer><span>CLIPPINGAI STUDIO <i>·</i> FOUNDATION PREVIEW</span><span>Built for creators who care about the craft.</span></footer>
        </div>
      </main>
    </div></>
  )
}

export default App
