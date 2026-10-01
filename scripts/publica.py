"""Publica os 3 vídeos v2 (completo 16:9, essencial 16:9, reel 9:16) em PT, EN e ES em inematds/codex-claude-video.
Release video-v2.0.0 (MP4 + SRT; EN/ES com sufixo -en/-es) + Pages: videos/ (PT), videos/en/, videos/es/,
com players, capítulos, legendas VTT e seletor de idioma. Publica os idiomas que estiverem prontos (PT sempre).
Idempotente: sobe só o que mudou de tamanho; commit só se houver diff."""
import html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

OUT = Path.home() / 'projetos/output/codex-claude-video'
REPO = Path.home() / 'projetos/codex-claude-video'
GH = 'inematds/codex-claude-video'
TAG = 'video-v2.0.0'
BASE = f'https://github.com/{GH}/releases/download/{TAG}/'
PAGES = 'https://inematds.github.io/codex-claude-video/'
AREA = 'https://eventos.inema.pro/codex-claude/'

T = {
    'pt': dict(html='pt-BR', nome='Português', bandeira='PT', area=AREA, track='Português',
               title='Codex + Claude em vídeo · INEMA.CLUB',
               meta='Vídeo explicativo com avatar do Nei: usar Claude e Codex juntos — os seis níveis do Use Both, quem faz o quê e todos os cursos e kits abertos do INEMA.',
               h1='Codex + Claude: <b>um planeja, o outro critica.</b>',
               lead='Vídeo explicativo com avatar e voz do Nei sobre usar as duas ferramentas juntas: os seis níveis do kit Use Both, quem faz o quê, as três formas de conectar, como os cursos e kits do INEMA se integram — e todos os recursos abertos. Três versões: completa, essencial e reel vertical.',
               v=[('Completo', 'Tudo o que a área traz: os seis níveis, quem faz o quê, as três formas de conectar, a integração e todos os recursos.'),
                  ('Essencial', 'O gancho, a regra, os seis níveis, os recursos e o primeiro passo.'),
                  ('Reel 9:16', 'Para Shorts, Reels e TikTok.')],
               mp4='Baixar MP4', srt='Baixar legendas', cap='Capítulos', rec='Recursos citados', aberto='Tudo aberto.',
               nav_area='Área Codex + Claude', cursos_pt='',
               footer='Produzido com o <a href="https://inematds.github.io/explicavideos/guia/">Explicavideos v2</a>. Níveis e cartão de rotas resumidos do kit Use Both (Prompt Advisers / Mark Kashef, MIT). Recurso educacional independente, não é produto da OpenAI nem da Anthropic. Conteúdo aberto do <a href="https://inema.club">INEMA.CLUB</a>.',
               rel='Codex + Claude em vídeo — avatar e voz do Nei, animações explicativas sincronizadas à fala e legendas.'),
    'en': dict(html='en', nome='English', bandeira='EN', area=AREA + 'en/', track='English',
               title='Codex + Claude on video · INEMA.CLUB',
               meta="Explainer video with Nei's avatar: using Claude and Codex together — the six levels of Use Both, who does what, and all of INEMA's open courses and kits.",
               h1='Codex + Claude: <b>one plans, the other critiques.</b>',
               lead="Explainer video with Nei's avatar and voice on using both tools together: the six levels of the Use Both kit, who does what, the three ways to connect them, how INEMA's courses and kits fit together — and every open resource. Three versions: full, essential and vertical reel.",
               v=[('Full', 'Everything the section covers: the six levels, who does what, the three ways to connect, the integration and all resources.'),
                  ('Essential', 'The hook, the rule, the six levels, the resources and the first step.'),
                  ('Reel 9:16', 'For Shorts, Reels and TikTok.')],
               mp4='Download MP4', srt='Download subtitles', cap='Chapters', rec='Resources mentioned', aberto='All open.',
               nav_area='Codex + Claude section', cursos_pt='Most courses and kits are in Portuguese.',
               footer='Made with <a href="https://inematds.github.io/explicavideos/guia/">Explicavideos v2</a>. Levels and route card summarized from the Use Both kit (Prompt Advisers / Mark Kashef, MIT). Independent educational resource, not a product of OpenAI or Anthropic. Open content from <a href="https://inema.club">INEMA.CLUB</a>.',
               rel=None),
    'es': dict(html='es', nome='Español', bandeira='ES', area=AREA + 'es/', track='Español',
               title='Codex + Claude en video · INEMA.CLUB',
               meta='Video explicativo con el avatar de Nei: usar Claude y Codex juntos — los seis niveles de Use Both, quién hace qué y todos los cursos y kits abiertos de INEMA.',
               h1='Codex + Claude: <b>uno planifica, el otro critica.</b>',
               lead='Video explicativo con el avatar y la voz de Nei sobre usar las dos herramientas juntas: los seis niveles del kit Use Both, quién hace qué, las tres formas de conectarlas, cómo se integran los cursos y kits de INEMA — y todos los recursos abiertos. Tres versiones: completa, esencial y reel vertical.',
               v=[('Completo', 'Todo lo que trae la sección: los seis niveles, quién hace qué, las tres formas de conectar, la integración y todos los recursos.'),
                  ('Esencial', 'El gancho, la regla, los seis niveles, los recursos y el primer paso.'),
                  ('Reel 9:16', 'Para Shorts, Reels y TikTok.')],
               mp4='Descargar MP4', srt='Descargar subtítulos', cap='Capítulos', rec='Recursos citados', aberto='Todo abierto.',
               nav_area='Sección Codex + Claude', cursos_pt='La mayoría de los cursos y kits está en portugués.',
               footer='Producido con <a href="https://inematds.github.io/explicavideos/guia/">Explicavideos v2</a>. Niveles y tarjeta de rutas resumidos del kit Use Both (Prompt Advisers / Mark Kashef, MIT). Recurso educativo independiente, no es un producto de OpenAI ni de Anthropic. Contenido abierto de <a href="https://inema.club">INEMA.CLUB</a>.',
               rel=None),
}
RECURSOS = [('Claude → Codex', 'https://inematds.github.io/curso-claude-codex/'), ('Codex Básico', 'https://inematds.github.io/codexbasico/'),
            ('Master Codex', 'https://inematds.github.io/mastercodex/'), ('iClaudeX', 'https://inematds.github.io/iclaudex/'),
            ('MakeClaudeX', 'https://inematds.github.io/makeclaudex/'), ('DeepClaudeX', 'https://inematds.github.io/deepclaudex/'),
            ('agente-claude-codex', 'https://inematds.github.io/agente-claude-codex/guia/'), ('Use Both', 'https://inematds.github.io/use-both-claude-codex/guia/'),
            ('claudex', 'https://github.com/inematds/claudex'), ('Codex Cheat Sheet', 'https://inematds.github.io/codex-cheat-sheet/guia/')]
CSS = '''<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0D1321;color:#F0EBD8;font:18px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 16px}
a{color:#FFC300}h1{font-size:clamp(1.8rem,5vw,2.8rem);line-height:1.15;margin:.4em 0}h1 b{color:#FFC300}.lead{color:#b9c3d0;max-width:780px}
.card{background:#1D2D44;border:1px solid #3E5C76;border-radius:16px;padding:20px;margin:28px 0}.card h2{margin:0 0 4px;font-size:1.3rem}.card h2 span{color:#748CAB;font-size:1rem;font-weight:500}.meta{color:#b9c3d0;margin:0 0 12px}
video{width:100%;aspect-ratio:16/9;background:#0a0f19;border-radius:12px}.vert video{aspect-ratio:9/16;max-width:420px;display:block;margin:auto}
summary{cursor:pointer;color:#FFC300;margin-top:8px}button{display:block;background:#0D1321;color:#F0EBD8;border:1px solid #3E5C76;border-radius:8px;padding:10px 12px;margin:6px 0;text-align:left;cursor:pointer;width:100%;font:inherit;font-size:16px}
.chip{display:inline-block;border:1px solid #3E5C76;border-radius:999px;padding:6px 14px;margin:4px;text-decoration:none;font-size:15px}.langs{float:right}.langs a,.langs b{margin-left:10px}.langs b{color:#F0EBD8}
:focus-visible{outline:3px solid #FFC300;outline-offset:3px}footer{color:#748CAB;font-size:15px;margin-top:40px}</style>'''


def sh(*a, **kw):
    return subprocess.run(a, check=True, text=True, capture_output=True, **kw).stdout


def dur(p):
    return float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)))


def decode_ok(p):
    return subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'null', '-'], capture_output=True, text=True).stderr.strip() == ''


def pasta(lang):
    return 'videos' if lang == 'pt' else f'videos/{lang}'


def pronto(lang):
    v2 = OUT / ('v2' if lang == 'pt' else f'{lang}-v2'); suf = '' if lang == 'pt' else f'-{lang}'
    return (v2 / f'verification/assembled-{lang}.json').exists() and all(
        (OUT / f'final/codex-claude-{n}{suf}.mp4').exists() for n in ('essencial-16x9', 'reel-9x16'))


def videos(lang):
    """Confere a produção do idioma e devolve os 3 vídeos com nomes públicos."""
    t = T[lang]; v2 = OUT / ('v2' if lang == 'pt' else f'{lang}-v2'); suf = '' if lang == 'pt' else f'-{lang}'
    rec = json.loads((v2 / f'verification/assembled-{lang}.json').read_text())
    full = Path(rec['file'])
    assert full.stat().st_size == rec['bytes'] and (v2 / f'verification/decode-full-{lang}.log').read_text() == '', lang
    for b in rec['blocks']:
        assert json.loads((v2 / f'final/{b}/alignment.json').read_text())['ratio'] > .90, b
    scenes = json.loads((v2 / f'docs/lesson-{lang}.json').read_text())
    assert len(rec['chapters']) == len(scenes), lang
    ess, reel = OUT / f'final/codex-claude-essencial-16x9{suf}.mp4', OUT / f'final/codex-claude-reel-9x16{suf}.mp4'
    for p in (ess, reel):
        assert p.exists() and p.with_suffix('.srt').exists() and decode_ok(p), p
    vids = [
        dict(id='completo', file=full, srt=full.with_suffix('.srt'), name=f'codex-claude-completo-16x9{suf}', ratio='16/9',
             chapters=[(int(c['time']), scenes[c['scene'] - 1]['title']) for c in rec['chapters']]),
        dict(id='essencial', file=ess, srt=ess.with_suffix('.srt'), name=f'codex-claude-essencial-16x9{suf}', ratio='16/9', chapters=[]),
        dict(id='reel', file=reel, srt=reel.with_suffix('.srt'), name=f'codex-claude-reel-9x16{suf}', ratio='9/16', chapters=[]),
    ]
    for v, (title, desc) in zip(vids, t['v']):
        v.update(title=title, desc=desc, duration=dur(v['file']))
    return vids


def pagina(lang, vids, langs):
    t = T[lang]; folder = REPO / pasta(lang); folder.mkdir(parents=True, exist_ok=True)
    cards = []
    for v in vids:
        (folder / f"{v['id']}.vtt").write_text('WEBVTT\n\n' + re.sub(r'(\d\d:\d\d:\d\d),(\d{3})', r'\1.\2', v['srt'].read_text()))
        d = f"{int(v['duration'] // 60)}min{int(v['duration'] % 60):02d}s"
        caps = ''.join(f'<button type="button" data-time="{s}">{s // 60:02d}:{s % 60:02d} · {html.escape(c)}</button>' for s, c in v['chapters'])
        vert = ' vert' if v['ratio'] == '9/16' else ''
        cards.append(f'<section class="card{vert}" id="{v["id"]}"><h2>{v["title"]} <span>{d}</span></h2><p class="meta">{html.escape(v["desc"])}</p>'
                     f'<video controls preload="metadata" playsinline><source src="{BASE}{v["name"]}.mp4" type="video/mp4">'
                     f'<track default kind="subtitles" src="{v["id"]}.vtt" srclang="{lang}" label="{t["track"]}"></video>'
                     f'<p><a href="{BASE}{v["name"]}.mp4">{t["mp4"]}</a> · <a href="{BASE}{v["name"]}.srt">{t["srt"]}</a></p>'
                     + (f'<details open><summary>{t["cap"]}</summary>{caps}</details>' if caps else '') + '</section>')
    links = ''.join(f'<a class="chip" href="{u}">{html.escape(n)}</a>' for n, u in RECURSOS)
    rel = lambda o: ('' if lang == 'pt' else '../') + ('' if o == 'pt' else f'{o}/')
    seletor = ''.join(f'<b>{T[o]["bandeira"]}</b>' if o == lang else f'<a href="{rel(o)}" hreflang="{T[o]["html"]}">{T[o]["bandeira"]}</a>' for o in langs)
    alternos = ''.join(f'<link rel="alternate" hreflang="{T[o]["html"]}" href="{PAGES}{pasta(o)}/">' for o in langs)
    page = f'''<!doctype html><html lang="{t['html']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title><meta name="description" content="{html.escape(t['meta'])}">{alternos}
{CSS}</head>
<body><main><nav><span class="langs">{seletor}</span><a href="https://inema.club">INEMA.CLUB</a> · <a href="{t['area']}">{t['nav_area']}</a> · <a href="https://github.com/{GH}">GitHub</a></nav>
<h1>{t['h1']}</h1>
<p class="lead">{t['lead']}</p>
{''.join(cards)}
<section class="card"><h2>{t['rec']}</h2><p class="meta">{t['aberto']} {t['cursos_pt']}</p>{links}</section>
<footer>{t['footer']}</footer></main>
<script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{{const v=b.closest('.card').querySelector('video');v.currentTime=Number(b.dataset.time);v.play();}}));</script></body></html>
'''
    (folder / 'index.html').write_text(page)
    (folder / 'delivery.json').write_text(json.dumps({v['id']: {'url': BASE + v['name'] + '.mp4', 'srt': BASE + v['name'] + '.srt', 'duration': round(v['duration'], 2)} for v in vids}, indent=2) + '\n')


def main():
    langs = [l for l in ('pt', 'en', 'es') if pronto(l)]
    assert 'pt' in langs
    todos = {l: videos(l) for l in langs}
    # Release: nomes públicos estáveis
    stage = OUT / 'release'; stage.mkdir(exist_ok=True)
    assets = []
    for vids in todos.values():
        for v in vids:
            for src, ext in ((v['file'], 'mp4'), (v['srt'], 'srt')):
                dst = stage / f"{v['name']}.{ext}"
                if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                    dst.write_bytes(src.read_bytes())
                assets.append(dst)
    if subprocess.run(['gh', 'release', 'view', TAG, '--repo', GH], capture_output=True).returncode:
        notes = stage / 'RELEASE.md'
        notes.write_text(T['pt']['rel'] + f'\n\nAssistir: {PAGES}videos/\n\nFonte: {AREA}\n\n'
                         'Produção: https://inematds.github.io/explicavideos/guia/ (Explicavideos v2)\n\n'
                         + '\n'.join(f"- {v['title']}: {int(v['duration'] // 60)}min{int(v['duration'] % 60):02d}s" for v in todos['pt']))
        sh('gh', 'release', 'create', TAG, '--repo', GH, '--draft', '--title', 'Codex + Claude em vídeo (v2)', '--notes-file', str(notes))
    have = {a['name']: a['size'] for a in json.loads(sh('gh', 'release', 'view', TAG, '--repo', GH, '--json', 'assets'))['assets']}
    for f in assets:
        if have.get(f.name) != f.stat().st_size:
            print('upload', f.name, flush=True); sh('gh', 'release', 'upload', TAG, str(f), '--repo', GH, '--clobber')
    # Pages
    for lang, vids in todos.items():
        pagina(lang, vids, langs)
    (REPO / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Codex + Claude em vídeo</title><meta http-equiv="refresh" content="0; url=videos/"><a href="videos/">Assistir</a>\n')
    g = lambda *a: sh('git', '-c', 'user.name=inematds', '-c', 'user.email=inematds@gmail.com', *a, cwd=REPO)
    g('add', '-A')
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO).returncode:
        g('commit', '-m', f'feat: Codex + Claude em vídeo (v2) — {"/".join(l.upper() for l in langs)}: completo, essencial e reel 9:16\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
        g('push', '-q', 'origin', 'HEAD:main')
    sh('gh', 'release', 'edit', TAG, '--repo', GH, '--draft=false')
    for vids in todos.values():
        for v in vids:
            with urllib.request.urlopen(urllib.request.Request(BASE + v['name'] + '.mp4', method='HEAD'), timeout=60) as r:
                assert r.status == 200, v['name']
    for lang in langs:
        for _ in range(40):
            try:
                with urllib.request.urlopen(PAGES + pasta(lang) + '/delivery.json?v=' + str(int(time.time())), timeout=30) as f:
                    if 'reel' in f.read().decode():
                        break
            except Exception:
                pass
            time.sleep(30)
        else:
            sys.exit(f'push e release feitos; Pages ({lang}) ainda não respondeu')
        print('OK', PAGES + pasta(lang) + '/')


if __name__ == '__main__':
    main()
