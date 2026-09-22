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

type Conflict={path:string;candidates:string[]}
function Icon({name}:{name:'tree'|'spark'|'folder'|'play'|'copy'|'check'|'alert'}) {
 const paths={tree:'M4 4h6v5H7v4h10V9h-3V4h6M7 13v5m10-5v5',spark:'m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z',folder:'M3 6h7l2 2h9v11H3V6Z',play:'m9 7 8 5-8 5V7Z',copy:'M8 8h11v11H8V8Zm-3 8H4V4h12v1',check:'m5 12 4 4L19 6',alert:'M12 4 3 20h18L12 4Zm0 6v4m0 3v.1'}
 return <svg viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name]}/></svg>
}

function App(){
 const [state,setState]=useState<AppState>('idle')
 const [view,setView]=useState<'reconstruct'|'generate'>('reconstruct')
 const [tree,setTree]=useState(sampleTree)
 const [source,setSource]=useState('')
 const [destination,setDestination]=useState('')
 const [progress,setProgress]=useState(0)
 const [message,setMessage]=useState('')
 const [conflict,setConflict]=useState<Conflict|null>(null)
 const status=useMemo(()=>{
  if(state==='idle') return view==='reconstruct'?['Ready to organize','Choose your folders, review the tree, and start when ready.']:['Ready to scan','Choose a folder, then generate its tree.']
  if(state==='running') return ['Working…',message||'Preparing the workspace.']
  if(state==='conflict') return ['A file needs your choice',conflict?.path||message]
  if(state==='success') return ['Finished',message||'The operation completed successfully.']
  return ['Couldn’t finish',message||'Check the folders and try again.']
 },[state,view,message,conflict])
 useEffect(()=>window.desktop?.onEvent(event=>{
  if(event.kind==='progress'&&event.total)setProgress(Math.round(event.current/event.total*100))
  if(event.message)setMessage(event.message)
  if(event.kind==='conflict'){
   const candidates=Array.isArray(event.data.candidates)?event.data.candidates.filter((item):item is string=>typeof item==='string'):[]
   setConflict({path:typeof event.data.path==='string'?event.data.path:event.message,candidates});setState('conflict')
  }
  if(event.kind==='generated'&&typeof event.data.tree==='string')setTree(event.data.tree)
  if(event.kind==='complete'){setConflict(null);setState('success')}
  if(event.kind==='cancelled'){setConflict(null);setState('idle')}
  if(event.kind==='error'){setConflict(null);setState('error')}
 }),[])
 const canRun=Boolean(source.trim()&&(view==='generate'||destination.trim())&&tree.trim())
 const run=async()=>{setProgress(0);setMessage('');setConflict(null);setState('running');await window.desktop?.startJob(view==='generate'?{operation:'generate',source,include_files:true}:{operation:'reconstruct',source,destination,tree})}
 const cancel=async()=>{await window.desktop?.cancelJob()}
 const browse=async(setter:(value:string)=>void)=>{const selected=await window.desktop?.chooseDirectory();if(selected)setter(selected)}
 const chooseConflict=async(choice:string|null)=>{await window.desktop?.resolveConflict(choice);setConflict(null);setState('running')}
 return <div className="shell">
  <aside>
   <div className="brand"><div className="mark"><Icon name="tree"/></div><div><b>Canopy</b><span>File workspace</span></div></div>
   <nav aria-label="Workspace mode"><button className={view==='reconstruct'?'active':''} onClick={()=>{setView('reconstruct');setState('idle')}}><Icon name="tree"/>Reconstruct</button><button className={view==='generate'?'active':''} onClick={()=>{setView('generate');setState('idle')}}><Icon name="spark"/>Generate tree</button></nav>
   <div className="asideBottom"><div className="safety"><span>Safe mode</span><b>Copy only</b><small>Canopy never moves, overwrites, or cleans files.</small></div></div>
  </aside>
  <main>
   <header><div><p className="eyebrow">{view==='reconstruct'?'RECONSTRUCT':'GENERATE'}</p><h1>{view==='reconstruct'?'Shape files into a clear workspace':'Map a folder into a clean tree'}</h1><p>{view==='reconstruct'?'Turn an ASCII tree into a real folder structure. Your source files stay untouched.':'Scan a local folder and create a portable ASCII tree.'}</p></div></header>
   <section className="workflow">
    <div className="step"><div className="stepTitle"><span>1</span><div><h2>{view==='reconstruct'?'Choose locations':'Choose a folder'}</h2><p>{view==='reconstruct'?'Where files come from and where the new workspace goes.':'Select the folder you want to map.'}</p></div></div>
     <label htmlFor="source-folder">Source folder</label><div className="field"><Icon name="folder"/><input id="source-folder" value={source} onChange={e=>setSource(e.target.value)}/><button onClick={()=>browse(setSource)}>Browse</button></div>
     {view==='reconstruct'&&<><label htmlFor="destination-folder">Destination</label><div className="field"><Icon name="folder"/><input id="destination-folder" value={destination} onChange={e=>setDestination(e.target.value)}/><button onClick={()=>browse(setDestination)}>Browse</button></div></>}
    </div>
    <div className="step treeStep"><div className="stepTitle"><span>2</span><div><h2>{view==='reconstruct'?'Define the structure':'Review the result'}</h2><p>{view==='reconstruct'?'Paste a tree below.':'The generated tree stays editable and ready to copy.'}</p></div><div className="toolbar"><button onClick={()=>navigator.clipboard?.writeText(tree)}><Icon name="copy"/>Copy</button></div></div>
      <label className="srOnly" htmlFor="tree-editor">ASCII directory tree</label><textarea id="tree-editor" value={tree} onChange={e=>setTree(e.target.value)} spellCheck={false}/><div className="editorFoot"><span>{tree.split(/\r?\n/).filter(Boolean).length} non-empty lines</span></div>
    </div>
   </section>
   <section className={`runCard ${state}`} aria-live="polite" aria-busy={state==='running'}>
    <div className="statusIcon"><Icon name={state==='error'||state==='conflict'?'alert':state==='success'?'check':'play'}/></div>
    <div className="statusCopy"><h3>{status[0]}</h3><p>{status[1]}</p>{state==='running'&&<div className="progress" role="progressbar" aria-label="Operation progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><i style={{width:`${progress}%`}}/></div>}</div>
    {state==='conflict'?<div className="conflictActions">{conflict?.candidates.map(candidate=><button key={candidate} onClick={()=>chooseConflict(candidate)} title={candidate}>{candidate}<small>Use this source</small></button>)}<button className="skip" onClick={()=>chooseConflict(null)}>Skip file</button></div>:state==='running'?<button className="secondary" onClick={cancel}>Cancel</button>:state==='error'?<button className="primary" onClick={()=>setState('idle')}>Try again</button>:<button className="primary" disabled={!canRun} onClick={run}><Icon name="play"/>{view==='reconstruct'?'Start reconstruction':'Generate tree'}</button>}
   </section>
   <footer><span><i/> Canopy desktop uses safe copy-only reconstruction</span><span>Canopy 0.3</span></footer>
  </main>
 </div>
}
export default App
