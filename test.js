const fs = require('fs');
const code = fs.readFileSync('.agents/gsd-core/bin/gsd-tools.cjs', 'utf8');
const i = code.indexOf('function parseRoadmap');
if (i > -1) {
  console.log(code.substring(i, i + 2000));
} else {
  console.log("Not found");
}
