import {describe,expect,it} from 'vitest'
import {isTrustedRendererUrl,validateConflictChoice,validateJobRequest} from './security.js'
describe('Electron trust boundary',()=>{
 it('accepts only shaped job requests',()=>{
  expect(validateJobRequest({operation:'generate',source:'/tmp/source',include_files:true})).toEqual({operation:'generate',source:'/tmp/source',include_files:true})
  expect(()=>validateJobRequest({operation:'reconstruct',source:'/tmp/source',destination:'',tree:'a'})).toThrow(/destination/)
  expect(()=>validateJobRequest({operation:'shell',source:'/tmp'})).toThrow(/operation/)
 })
 it('accepts only absolute conflict candidates or skip',()=>{
  expect(validateConflictChoice(null)).toBeNull()
  expect(validateConflictChoice('/tmp/a.txt')).toBe('/tmp/a.txt')
  expect(()=>validateConflictChoice('relative.txt')).toThrow(/absolute/)
 })
 it('trusts packaged files and the configured dev origin only',()=>{
  expect(isTrustedRendererUrl('file:///app/dist/index.html')).toBe(true)
  expect(isTrustedRendererUrl('http://localhost:5173/page','http://localhost:5173')).toBe(true)
  expect(isTrustedRendererUrl('https://evil.example/page','http://localhost:5173')).toBe(false)
 })
})
