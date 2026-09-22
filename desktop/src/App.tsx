import {useEffect, useMemo, useState} from 'react'
import type {AppState, OperationEvent} from './types'

const sampleTree=`workspace/
├── assets/
│   └── brand.svg
├── data/
│   ├── customers.csv
│   └── orders.csv
└── src/
    └── app.py`

function Icon({name}:{name:'tree'|'spark'|'history'|'settings'|'folder'|'play'|'copy'|'check'|'alert'}) {
 const paths={tree:'M4 4h6v5H7v4h10V9h-3V4h6M7 13v5m10-5v5',spark:'m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z',history:'M4 12a8 8 0 1 0 2.3-5.7L4 8m0-4v4h4m4-1v5l3 2',settings:'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm8 3 2-1-2-3-2 .2-1.2-1.4.2-2-3-1-1 1.7-1.8.3L9 3 6 4l.2 2-1.4 1.2L3 7l-1 3 1.8 1-.1 2L2 14l1 3 2-.2 1.2 1.4L6 20l3 1 1-1.8 2 .1 1 1.7 3-1 .2-2 1.4-1.2 2 .2 1-3-1.7-1 .1-2Z',folder:'M3 6h7l2 2h9v11H3V6Z',play:'m9 7 8 5-8 5V7Z',copy:'M8 8h11v11H8V8Zm-3 8H4V4h12v1',check:'m5 12 4 4L19 6',alert:'M12 4 3 20h18L12 4Zm0 6v4m0 3v.1'}
 return <svg viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name]}/></svg>
}

function App(){
 const query=new URLSearchParams(location.search)
 const initial=(query.get('state') as AppState)||'idle'
 const [state,setState]=useState<AppState>(initial)
 const [view,setView]=useState<'reconstruct'|'generate'>('reconstruct')
 const [tree,setTree]=useState(sampleTree)
 const [source,setSource]=useState('/Users/boaz/Downloads/loose-files')
 const [destination,setDestination]=useState('/Users/boaz/Documents/organized')
 const [events,setEvents]=useState<OperationEvent[]>([])
 const [progress,setProgress]=useState(0)
 const status=useMemo(()=>({idle:view==='reconstruct'?['Ready to organize','Choose your folders, review the tree, and start when ready.']:['Ready to scan','Choose a folder, then generate its tree.'],running:['Building your workspace','32 of 50 items placed · customers.csv'],conflict:['A file needs your choice','Two source files match data/customers.csv'],success:['Workspace ready','50 items placed safely in 4.2 seconds.'],error:['Couldn’t finish the run','The destination is read-only. Choose another folder.']}[state]),[state,view])
 useEffect(()=>window.desktop?.onEvent(event=>{setEvents(old=>[...old,event]); if(event.kind==='progress'&&event.total)setProgress(Math.round(event.current/event.total*100)); if(event.kind==='conflict')setState('conflict'); if(event.kind==='generated'&&typeof event.data.tree==='string')setTree(event.data.tree); if(event.kind==='complete')setState('success'); if(event.kind==='error')setState('error')}),[])
 const run=()=>{setProgress(0);setState('running'); window.desktop?.startJob(view==='generate'?{operation:'generate',source,include_files:true}:{operation:'reconstruct',source,destination,tree})}
 const browse=async(setter:(value:string)=>void)=>{const selected=await window.desktop?.chooseDirectory(); if(selected)setter(selected)}
 return <div className="shell">
  <aside>
   <div className="brand"><div className="mark"><Icon name="tree"/></div><div><b>Canopy</b><span>File workspace</span></div></div>
   <nav><button className={view==='reconstruct'?'active':''} onClick={()=>{setView('reconstruct');setState('idle')}}><Icon name="tree"/>Reconstruct</button><button className={view==='generate'?'active':''} onClick={()=>{setView('generate');setState('idle')}}><Icon name="spark"/>Generate tree</button><button><Icon name="history"/>Activity</button></nav>
   <div className="asideBottom"><div className="safety"><span>Safe mode</span><b>Copy only</b></div><button><Icon name="settings"/>Settings</button></div>
  </aside>
  <main>
   <header><div><p className="eyebrow">{view==='reconstruct'?'RECONSTRUCT':'GENERATE'}</p><h1>{view==='reconstruct'?'Shape files into a clear workspace':'Map a folder into a clean tree'}</h1><p>{view==='reconstruct'?'Turn an ASCII tree into a real folder structure. Your source files stay untouched by default.':'Scan a local folder and create a portable ASCII tree in seconds.'}</p></div><button className="ghost">View activity <span>⌘K</span></button></header>
   <section className="workflow">
    <div className="step"><div className="stepTitle"><span>1</span><div><h2>{view==='reconstruct'?'Choose locations':'Choose a folder'}</h2><p>{view==='reconstruct'?'Where files come from and where the new workspace goes.':'Select the folder you want to map.'}</p></div></div>
     <label>Source folder</label><div className="field"><Icon name="folder"/><input value={source} onChange={e=>setSource(e.target.value)}/><button onClick={()=>browse(setSource)}>Browse</button></div>
     {view==='reconstruct'&&<><label>Destination</label><div className="field"><Icon name="folder"/><input value={destination} onChange={e=>setDestination(e.target.value)}/><button onClick={()=>browse(setDestination)}>Browse</button></div></>}
    </div>
    <div className="step treeStep"><div className="stepTitle"><span>2</span><div><h2>{view==='reconstruct'?'Define the structure':'Review the result'}</h2><p>{view==='reconstruct'?'Paste a tree or load it from a text file.':'The generated tree stays editable and ready to copy.'}</p></div><div className="toolbar"><button>Load file</button><button onClick={()=>navigator.clipboard?.writeText(tree)}><Icon name="copy"/>Copy</button></div></div>
      <textarea value={tree} onChange={e=>setTree(e.target.value)} spellCheck={false}/><div className="editorFoot"><span><i/>Valid structure</span><span>8 folders · 4 files</span></div>
    </div>
   </section>
   <section className={`runCard ${state}`}>
    <div className="statusIcon"><Icon name={state==='error'||state==='conflict'?'alert':state==='success'?'check':'play'}/></div>
    <div className="statusCopy"><h3>{status[0]}</h3><p>{status[1]}</p>{state==='running'&&<div className="progress"><i style={{width:`${progress||64}%`}}/></div>}</div>
    {state==='conflict'?<div className="conflictActions"><button onClick={()=>{window.desktop?.resolveConflict('/Archive/customers.csv');setState('running')}}>Archive/customers.csv <small>248 KB · newer</small></button><button onClick={()=>{window.desktop?.resolveConflict('/Imports/customers.csv');setState('running')}}>Imports/customers.csv <small>241 KB</small></button><button className="skip" onClick={()=>{window.desktop?.resolveConflict(null);setState('running')}}>Skip file</button></div>:state==='error'?<button className="primary" onClick={()=>setState('idle')}>Choose destination</button>:state==='success'?<button className="primary">Open workspace</button>:<button className="primary" disabled={state==='running'} onClick={run}><Icon name="play"/>{state==='running'?'Working…':view==='reconstruct'?'Start reconstruction':'Generate tree'}</button>}
   </section>
   <footer><span><i/> Changes are previewed before destructive actions</span><span>Canopy 0.3</span></footer>
  </main>
 </div>
}
export default App
