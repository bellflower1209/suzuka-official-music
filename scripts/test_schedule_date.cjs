const assert = require('node:assert/strict');
const { classify, jstDay } = require('../assets/release-schedule.js');
const at = day => `${day}T00:00:00+09:00`;
const check = (now, entries) => {
  for (const [day, expected] of Object.entries(entries)) assert.equal(classify(at(day), new Date(now)), expected, `${now}: ${day}`);
};
check(at('2026-09-14'), {'2026-09-14':'today','2026-09-20':'this-week','2026-09-21':'next-week','2026-09-22':'next-week','2026-09-27':'next-week','2026-09-28':'this-month','2026-10-01':'later','2026-09-13':'awaiting-confirmation'});
check(at('2026-09-21'), {'2026-09-21':'today','2026-09-22':'this-week','2026-09-27':'this-week','2026-09-28':'next-week'});
check('2026-09-13T14:59:59Z', {'2026-09-21':'this-month'});
check('2026-09-13T15:00:00Z', {'2026-09-21':'next-week','2026-09-22':'next-week'});
check(at('2026-12-28'), {'2027-01-03':'this-week','2027-01-04':'next-week'});
assert.equal(jstDay(new Date('2026-09-13T15:00:00Z')), '2026-09-14');
assert.equal(classify('2026-09-20T15:00:00Z',new Date(at('2026-09-14'))),'next-week');
console.log(`Schedule JST/Monday boundary tests passed (host TZ=${process.env.TZ || 'default'}).`);
