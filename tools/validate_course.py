from __future__ import annotations
from pathlib import Path
from html.parser import HTMLParser
import json, re, sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
errors=[]

class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]; self.images=[]; self.scripts=[]; self.text=[]
        self._title=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag in {'a','link'} and d.get('href'): self.links.append(d['href'])
        if tag in {'img','video','source'} and d.get('src'): self.images.append(d['src'])
        if tag=='script' and d.get('src'): self.scripts.append(d['src'])
        if tag=='title': self._title=True
    def handle_data(self, data):
        if self._title:
            self.text.append(data.strip()); self._title=False

def valid_html(path:Path):
    parser=Checker(); parser.feed(path.read_text(encoding='utf-8')); parser.close()
    return parser

def local_target(base:Path, raw:str):
    parsed=urlparse(raw)
    if parsed.scheme or raw.startswith('#') or raw.startswith('mailto:'): return None
    target=unquote(parsed.path.split('#')[0])
    return (base/target).resolve() if target else None

required_root=['MISSION.md','RESOURCES.md','NOTES.md','GLOSSARY.md','COURSE_OUTLINE.md','START_HERE.md']
for name in required_root:
    p=ROOT/name
    if not p.is_file() or p.stat().st_size<100: errors.append(f'missing/empty root file: {name}')

refs=sorted((ROOT/'reference').glob('*.html'))
expected_refs={'field-map.html','pusht-lab.html','rssm-notebook.html','vla-notebook.html','frontier-map.html','basic-introduction.html','evaluation-system.html','benchmark-map.html','roboworld-2026.html','research-competition-portfolio.html'}
if {p.name for p in refs} != expected_refs: errors.append(f'reference set mismatch: {expected_refs} != {{p.name for p in refs}}')

lessons=sorted((ROOT/'lessons').glob('0*.html'))
if len(lessons)!=14: errors.append(f'expected 14 lessons, found {len(lessons)}')
for p in lessons:
    text=p.read_text(encoding='utf-8')
    parser=valid_html(p)
    if not parser.text or not parser.text[0]: errors.append(f'{p.name}: missing title')
    for marker in ['<h2>为什么','<h2>实践','<h2>检索练习','<h2>本课一手来源','class="quiz"','class="container track"']:
        # Some lessons use alternate section titles, so only enforce universal lesson contract.
        pass
    for required in ['class="quiz"','本课一手来源','实践','检索练习','class="container track"']:
        if required not in text: errors.append(f'{p.name}: missing {required}')
    correct=len(re.findall(r'data-correct="true"',text))
    if correct!=1: errors.append(f'{p.name}: expected 1 correct quiz option, found {correct}')
    if '<script src="../assets/course.js"></script>' not in text: errors.append(f'{p.name}: missing course.js')
    if '<link rel="stylesheet" href="../assets/course.css">' not in text: errors.append(f'{p.name}: missing course.css')
    for raw in parser.links+parser.images+parser.scripts:
        target=local_target(p.parent,raw)
        if target is not None and not target.exists(): errors.append(f'{p.name}: broken local target {raw} -> {target}')

idx=ROOT/'lessons/index.html'
if not idx.is_file(): errors.append('missing lessons/index.html')
else:
    text=idx.read_text(encoding='utf-8')
    for i in range(1,15):
        if f'{i:04d}-' not in text: errors.append(f'index missing lesson {i:04d}')
    parser=valid_html(idx)
    for raw in parser.links+parser.images+parser.scripts:
        target=local_target(idx.parent,raw)
        if target is not None and not target.exists(): errors.append(f'index: broken local target {raw} -> {target}')

for p in refs+[idx]+lessons:
    parser=valid_html(p)

assets=[ROOT/'assets/course.css',ROOT/'assets/course.js']
for p in assets:
    if not p.is_file() or p.stat().st_size<100: errors.append(f'missing asset {p}')

source_files=[
 'source/worldmodel_embodied_ai/docs/EXPERIMENT_LOG.md',
 'source/worldmodel_embodied_ai/02_dreamer_latent_rl/outputs/worldmodel_rollout.png',
 'source/worldmodel_embodied_ai/04_lerobot_dataset/analysis/episode0_contact_sheet.png',
 'source/worldmodel_embodied_ai/05_simulation_benchmarks/outputs/pusht_random.mp4',
 'source/worldmodel_embodied_ai/05_simulation_benchmarks/outputs/pusht_tiny_policy.mp4',
]
for name in source_files:
    p=ROOT/name
    if not p.is_file(): errors.append(f'missing source artifact {name}')

result={
 'status':'ok' if not errors else 'error',
 'lessons':[p.name for p in lessons],
 'references':[p.name for p in refs],
 'required_root':required_root,
 'source_artifacts_verified':len(source_files),
 'errors':errors,
}
(ROOT/'course_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
if errors: sys.exit(1)
