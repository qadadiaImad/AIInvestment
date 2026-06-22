import { join } from 'path'
// studio/out/main -> repo root is three levels up.
export const REPO_ROOT = join(__dirname, '..', '..', '..')
export const HIGGS = join(REPO_ROOT, 'higgs')
export const CONTENT = join(REPO_ROOT, 'content')
export const DATA = join(REPO_ROOT, 'web', 'public', 'data')
