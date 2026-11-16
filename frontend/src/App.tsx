import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, AudioWaveform, CheckCircle2, CircleHelp, Clapperboard, Clock3, Film, FolderOpen, HardDrive, LayoutDashboard, Link2, LoaderCircle, LockKeyhole, Scissors, ShieldCheck, Sparkles, Upload, Video, XCircle } from 'lucide-react'

const API = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
type Project = {id:string;title:string;source_type:string;status:string;created_at:string;duration?:number;requested_clips:number;error?:string;message?:string}
type Clip = {id:string;start_time:number;end_time:number;score:number;transcript:string;status:string}
const fmt=(n?:number)=>n==null?'—':`${Math.floor(n/60)}:${String(Math.floor(n%60)).padStart(2,'0')}`
function App(){
 const [projects,setProjects]=useState<Project[]>([]),[clips,setClips]=useState<Clip[]>([])
 const [file,setFile]=useState<File|null>(null),[count,setCount]=useState(10),[rights,setRights]=useState(false),[basis,setBasis]=useState('')
 const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[selected,setSelected]=useState('')
 const [url,setUrl]=useState(''),[tab,setTab]=useState('Overview'),[apiOk,setApiOk]=useState(false)
 async function refresh(){
  try{const r=await fetch(`${API}/v1/projects`);if(!r.ok)throw Error();const data=await r.json();setProjects(data);setApiOk(true)
   const running=data.find((p:Project)=>['queued','downloading','analysing','rendering'].includes(p.status));if(running)setTimeout(()=>refresh(),5000)
  }catch{setApiOk(false)}
 }
 useEffect(()=>{refresh();fetch(`${API}/health`).then(r=>setApiOk(r.ok)).catch(()=>setApiOk(false))},[])
 async function upload(){
  if(!file){setNotice('Choose a video file first.');return}
  if(!rights||basis.trim().length<10){setNotice('Confirm your rights and explain the legal basis (at least 10 characters).');return}
  setBusy(true);setNotice('')
  const fd=new FormData();fd.append('file',file);fd.append('requested_clips',String(count));fd.append('rights_confirmed','true');fd.append('rights_basis',basis)
  try{const r=await fetch(`${API}/v1/projects/upload`,{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw Error(d.detail||'Upload failed');setNotice('Upload complete. Analysis and clip rendering have started.');setFile(null);await refresh();setSelected(d.id);setTimeout(()=>refresh(),2500)}
  catch(e){setNotice(e instanceof Error?e.message:'Could not connect to the API. Start the backend first.')}
  finally{setBusy(false)}
 }
 async function addUrl(){
  if(!url.trim())return setNotice('Paste a supported source URL.')
  if(!rights||basis.trim().length<10)return setNotice('Confirm your rights and explain the legal basis first.')
  try{const r=await fetch(`${API}/v1/projects/url`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source_url:url,requested_clips:count,rights_confirmed:true,rights_basis:basis})});const d=await r.json();if(!r.ok)throw Error(d.detail||'Could not register link');setNotice('Link accepted. Video fetching and clip analysis have started. Some private, login-only or restricted links may fail.');setSelected(d.id);setUrl('');refresh()}
  catch(e){setNotice(e instanceof Error?e.message:'API connection failed.')}
 }
 async function showClips(p:Project){setSelected(p.id);try{const r=await fetch(`${API}/v1/projects/${p.id}/clips`);setClips(await r.json())}catch{setClips([])}}
 const ready=projects.filter(p=>p.status==='completed').length,working=projects.filter(p=>['queued','downloading','analysing','rendering'].includes(p.status)).length
 return <><div className="mobile"><LockKeyhole/><h2>ClippingAI is built for desktop</h2><p>Open this workspace on a desktop or laptop.</p></div><div className="shell">
 <aside className="side"><div className="brand"><div className="mark"><AudioWaveform/></div><div><b>Clipping<span>AI</span></b><small>VIDEO WORKSPACE</small></div></div><div className="workspace"><div className="avatar">C</div><div><b>Creator workspace</b><small>Personal studio</small></div></div>
 <label>WORKSPACE</label>{[['Overview',LayoutDashboard],['Projects',FolderOpen],['Clip library',Film],['Editing studio',Scissors]].map(([n,I]:any)=><button className={tab===n?'nav active':'nav'} onClick={()=>setTab(n)} key={n}><I size={16}/>{n}</button>)}
 <label className="manage">MANAGE</label><button className="nav" onClick={()=>setTab('Processing queue')}><Activity size={16}/>Processing queue</button><button className="nav" onClick={()=>setTab('Rights & sources')}><ShieldCheck size={16}/>Rights & sources</button>
 <div className="bottom"><div className="storage"><HardDrive size={14}/> Local processing workspace<small>Files stay on your API server.</small></div><div className="user"><div className="avatar">M</div><div><b>Your workspace</b><small>Self-hosted MVP</small></div></div></div></aside>
 <main><header><div>Workspace <i>/</i> <b>{tab}</b></div><div className="api"><span className={apiOk?'green':'red'}/>{apiOk?'API connected':'API offline'} <CircleHelp size={15}/></div></header>
 <div className="content"><div className="intro"><div><small>YOUR CREATIVE WORKSPACE</small><h1>Make every moment <em>count.</em></h1><p>Turn authorized long-form footage into short-form stories.</p></div><button className="refresh" onClick={refresh}><Activity size={14}/> Refresh</button></div>
 <section className="grid"><div className="panel intake"><div className="kicker">NEW PROJECT <span>01</span></div><h2>Start with a source</h2><p>Choose one source: upload a video file or paste a supported public video link.</p>
 <div className="drop" onClick={()=>document.getElementById('video')?.click()}><Upload/><b>{file?file.name:'Choose a video file'}</b><small>MP4, MOV, MKV, WEBM or M4V · max configured size</small><input id="video" type="file" accept="video/mp4,video/quicktime,video/x-matroska,video/webm,.m4v" onChange={e=>setFile(e.target.files?.[0]||null)}/></div>
 <div className="urlrow"><input value={url} onChange={e=>setUrl(e.target.value)} placeholder="Or paste a public YouTube / Facebook / Instagram video link"/><button onClick={addUrl}><Link2 size={14}/> Fetch & analyse</button></div>
 <div className="options"><label>CLIPS TO FIND</label><select value={count} onChange={e=>setCount(Number(e.target.value))}><option value={5}>5 clips</option><option value={8}>8 clips</option><option value={10}>10 clips</option></select></div>
 <label className="rights"><input type="checkbox" checked={rights} onChange={e=>setRights(e.target.checked)}/>I own this content, have permission, a suitable license, or another valid legal basis to process it.</label>
 <textarea value={basis} onChange={e=>setBasis(e.target.value)} placeholder="Briefly describe your rights (e.g. I recorded this video and own the footage)." rows={2}/>
 <button className="primary" disabled={busy} onClick={upload}>{busy?<LoaderCircle className="spin" size={16}/>:<Sparkles size={16}/>} Upload & analyse <ArrowUpRight size={14}/></button>
 {notice&&<div className="notice"><span>{notice}</span><button onClick={()=>setNotice('')}><XCircle size={14}/></button></div>}
 <small className="footnote"><ShieldCheck size={12}/> Public links are fetched when supported. Private, DRM-protected or login-restricted videos may not work.</small></div>
 <div className="panel approach"><div className="kicker">THE WORKFLOW <span>02</span></div><div className="wave"><AudioWaveform size={34}/></div><h3>Original moments.<br/><em>Vertical exports.</em></h3><p>ClippingAI analyses your authorized source, proposes moments with timestamps, then renders 9:16 MP4 clips for review.</p><div className="check"><CheckCircle2/> Source timestamps retained</div><div className="check"><CheckCircle2/> Review before publishing</div><div className="check"><CheckCircle2/> No fabricated replacement footage</div></div></section>
 <section className="stats"><div><Clapperboard/><small>PROJECTS</small><b>{projects.length}</b></div><div><Video/><small>COMPLETED</small><b>{ready}</b></div><div><Clock3/><small>IN PROGRESS</small><b>{working}</b></div></section>
 <section className="recent"><div className="recenthead"><div><div className="kicker">YOUR WORK <span>03</span></div><h2>Recent projects</h2></div><button onClick={refresh}>Refresh list ↗</button></div>
 <div className="table"><div className="thead"><span>PROJECT</span><span>STATUS</span><span>DURATION</span><span>CLIPS</span><span>UPDATED</span></div>
 {projects.length===0?<div className="empty">No projects yet. Upload a video or paste a supported public link to begin.</div>:projects.map(p=><button className="project" key={p.id} onClick={()=>showClips(p)}><span><b>{p.title}</b><small>{p.id.slice(0,8)} · {p.source_type}</small></span><span className={'status '+p.status}>{p.status}</span><span>{fmt(p.duration)}</span><span>{p.requested_clips}</span><span>{new Date(p.created_at).toLocaleDateString()}</span></button>)}</div>
 {selected&&<div className="clips"><div className="cliphead"><b>Selected project clips</b><button onClick={()=>{setSelected('');setClips([])}}>Close</button></div>{clips.length===0?<p>Clips are not ready yet. Refresh after processing finishes.</p>:clips.map(c=><div className="clip" key={c.id}><div><b>{fmt(c.start_time)} – {fmt(c.end_time)}</b><small>Moment score: {c.score} · {c.status}</small><p>{c.transcript||'No transcript available for this moment.'}</p></div>{c.status==='ready'&&<a href={`${API}/v1/clips/${c.id}/download`}>Download MP4 ↓</a>}</div>)}</div>}
 </section><footer>CLIPPINGAI STUDIO · SELF-HOSTED MVP <span>Review all exports before publishing.</span></footer></div></main></div></>
}
export default App
