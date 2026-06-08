const fs = require('fs');
const m = JSON.parse(fs.readFileSync('D:\\pycharm\\test-generator\\skill.manifest.json','utf8'));
console.log('VERSION=' + (m['版本'] || 'NONE'));
console.log('RUNTIME=' + JSON.stringify(m['运行时文件']));
const excludes = m['分发排除'] || [];
console.log('EXCLUDES_LEN=' + excludes.length);
const exclSet = new Set(excludes);
['.harness','.claude','.codebuddy','.cursor','.windsurf','.qoder','.trae','.agents','.workbuddy'].forEach(d => {
 const hit = excludes.some(e => e.startsWith(d + '/') || e === d || e === d + '/**');
 console.log('EXCL_' + d + '=' + (hit ? 'YES' : 'NO'));
});
const runtime = m['运行时文件'] || [];
['.harness','.claude','.codebuddy','.cursor','.windsurf'].forEach(d => {
 const hit = runtime.some(e => e.startsWith(d + '/') || e === d);
 console.log('RUNTIME_HAS_' + d + '=' + (hit ? 'YES(FAIL)' : 'NO(PASS)'));
});
console.log('ADAPTERS=' + JSON.stringify(m['宿主适配入口']));
console.log('NPM_ENVS=' + JSON.stringify(m['Node.js安装入口']['支持环境']));
console.log('LANG_OK=' + JSON.stringify(m['语言']));
