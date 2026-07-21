import {reelPropsSchema} from './props';
import fixture from './fixtures/ddog.json';

const r = reelPropsSchema.safeParse(fixture);
if (!r.success) {
  console.error(r.error.format());
  process.exit(1);
}
console.log('fixture OK');
