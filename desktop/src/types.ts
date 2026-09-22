export type AppState = 'idle' | 'running' | 'conflict' | 'success' | 'error'
export interface OperationEvent {kind:string; message:string; level:'info'|'warning'|'error'; current:number; total:number; data:Record<string,unknown>}
export interface DesktopApi {
  chooseDirectory(): Promise<string | null>
  startJob(request: Record<string, unknown>): Promise<void>
  cancelJob(): Promise<void>
  resolveConflict(choice: string | null): Promise<void>
  onEvent(callback: (event: OperationEvent) => void): () => void
}
declare global { interface Window { desktop?: DesktopApi } }
