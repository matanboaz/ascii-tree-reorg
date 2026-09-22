// @vitest-environment jsdom
import {act, type ReactElement} from 'react'
import {createRoot, type Root} from 'react-dom/client'
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest'
import App from './App'
import type {OperationEvent} from './types'

let root:Root
let host:HTMLDivElement
let receive:(event:OperationEvent)=>void
;(globalThis as {IS_REACT_ACT_ENVIRONMENT?:boolean}).IS_REACT_ACT_ENVIRONMENT=true
const desktop={
 chooseDirectory:vi.fn(),startJob:vi.fn().mockResolvedValue(undefined),cancelJob:vi.fn().mockResolvedValue(undefined),resolveConflict:vi.fn().mockResolvedValue(undefined),
 onEvent:vi.fn((callback:(event:OperationEvent)=>void)=>{receive=callback;return()=>{}}),
}
const click=(button:Element)=>act(async()=>{(button as HTMLButtonElement).click();await Promise.resolve()})
const fill=(input:HTMLInputElement,value:string)=>act(()=>{const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!;setter.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true}))})
const button=(text:string)=>[...host.querySelectorAll('button')].find(node=>node.textContent?.includes(text))!

beforeEach(()=>{vi.clearAllMocks();window.desktop=desktop;host=document.createElement('div');document.body.append(host);root=createRoot(host);act(()=>root.render(<App/>))})
afterEach(()=>{act(()=>root.unmount());host.remove()})

describe('Canopy runtime states',()=>{
 it('renders and returns real conflict candidates',async()=>{
  act(()=>receive({kind:'conflict',message:'choose',level:'warning',current:0,total:0,data:{path:'docs/report.txt',candidates:['/real/a/report.txt','/real/b/report.txt']}}))
  expect(host.textContent).toContain('/real/a/report.txt')
  expect(host.textContent).not.toContain('/Archive/customers.csv')
  await click(button('/real/b/report.txt'))
  expect(desktop.resolveConflict).toHaveBeenCalledWith('/real/b/report.txt')
 })
 it('offers cancellation only while a job is running',async()=>{
  const inputs=host.querySelectorAll('input');fill(inputs[0],'/source');fill(inputs[1],'/destination')
  await click(button('Start reconstruction'))
  expect(button('Cancel')).toBeTruthy()
  await click(button('Cancel'))
  expect(desktop.cancelJob).toHaveBeenCalledOnce()
  act(()=>receive({kind:'cancelled',message:'Operation cancelled.',level:'warning',current:0,total:0,data:{partial_results:true}}))
  expect(host.textContent).toContain('Ready to organize')
 })
 it('has no placeholder activity, settings, load, or open controls',()=>{
  expect(host.textContent).not.toContain('View activity')
  expect(host.textContent).not.toContain('Settings')
  expect(host.textContent).not.toContain('Load file')
  expect(host.textContent).not.toContain('Open workspace')
 })
})
