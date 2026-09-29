"""Versões derivadas do v2 (sem nova geração no HeyGen):
- essencial 16:9: cenas 1-4 + 10-11 cortadas do vídeo completo v2, legendas deslocadas;
- reel 9:16: cenas 1, 2 e 11 — manchete no topo, avatar no meio (legenda na altura do peito),
  animação v2 recortada (sem o canto do avatar nem a legenda de baixo) na base.
Corta nas divisas de cena medidas (align/*.json). Tudo local, ffmpeg."""
import json, re, subprocess
from pathlib import Path

OUT = Path.home() / 'projetos/output/codex-claude-video'
V1, V2 = OUT / 'v1', OUT / 'v2'
FULL = V2 / 'final/codex-claude-pt.mp4'
B1 = json.loads((V2 / 'align/pt-b01.json').read_text())['starts']
B2 = json.loads((V2 / 'align/pt-b02.json').read_text())['starts']
D1 = float(json.loads((V2 / 'verification/blocos-downloads.json').read_text())['pt-b01']['duration'])


def ts(s):
    h, m, r = s.split(':'); sec, ms = r.split(','); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def st(t, sep=','):
    n = round(t * 1000); return f'{n // 3600000:02d}:{n // 60000 % 60:02d}:{n // 1000 % 60:02d}{sep}{n % 1000:03d}'


def cues(srt):
    for item in srt.read_text().strip().split('\n\n'):
        l = item.splitlines(); a, z = l[1].split(' --> '); yield ts(a), ts(z), ' '.join(l[2:])


def cut_cues(srt, segs):
    """segs: [(a,b)] no tempo da fonte -> cues deslocados para o tempo de saída."""
    out, off = [], 0.0
    for a, b in segs:
        for s, e, t in cues(srt):
            if s >= a - .05 and s < b - .05:
                out.append((off + s - a, off + min(e, b) - a, t))
        off += b - a
    return out


def ff(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def trimcat(segs, src_idx=0, audio=True):
    parts, labels = [], []
    for i, (a, b) in enumerate(segs):
        parts.append(f'[{src_idx}:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]')
        labels.append(f'[v{i}]')
        if audio:
            parts.append(f'[{src_idx}:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]'); labels.append(f'[a{i}]')
    parts.append(''.join(labels) + f'concat=n={len(segs)}:v=1:a={1 if audio else 0}' + ('[v][a]' if audio else '[v]'))
    return ';'.join(parts)


def essencial():
    segs = [(0, B1[4]), (D1 + B2[4], D1 + B2[6])]
    dest = OUT / 'final/codex-claude-essencial-16x9.mp4'; dest.parent.mkdir(exist_ok=True)
    ff('-i', str(FULL), '-filter_complex', trimcat(segs), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium',
       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(dest))
    c = cut_cues(V2 / 'final/codex-claude-pt.srt', segs)
    dest.with_suffix('.srt').write_text('\n'.join(f'{i + 1}\n{st(s)} --> {st(e)}\n{t}\n' for i, (s, e, t) in enumerate(c)))
    return dest


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kicker,Montserrat ExtraBold,40,&H0000C3FF,&H0000C3FF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,0,0,8,60,60,110,1
Style: Head,Montserrat Black,92,&H00D8EBF0,&H00D8EBF0,&H00211A0D,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,60,60,190,1
Style: Cap,Montserrat ExtraBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,3,14,0,2,70,70,820,1
Style: Cta,Montserrat Black,64,&H0000C3FF,&H0000C3FF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,2,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
AMB = r'{\c&H0000C3FF&}'; CRE = r'{\c&H00D8EBF0&}'


def ass_t(t):
    cs = round(t * 100); return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'


def reel():
    segs1 = [(0, B1[1]), (B1[1], B1[2])]           # cenas 1 e 2 (bloco 1)
    seg2 = (B2[5], B2[6])                          # cena 11 (bloco 2)
    total = sum(b - a for a, b in segs1) + seg2[1] - seg2[0]
    t2, t3 = B1[1], B1[2]
    heads = [  # (início, fim, texto) — o frame 0 já é a capa
        (0, 12.2, f'A IA aprova{{\\N}}{AMB}o próprio plano.'),
        (12.2, t2, f'Um planeja.{{\\N}}{AMB}O outro critica.'),
        (t2, t3, f'Mesmo briefing.{{\\N}}{AMB}Artefato real.'),
        (t3, total - 5, f'Comece hoje.{{\\N}}{AMB}Duas rodadas.'),
    ]
    ev = [f'Dialogue: 0,{ass_t(0)},{ass_t(total)},Kicker,,0,0,0,,CLAUDE + CODEX · USAR OS DOIS JUNTOS']
    for a, b, t in heads:
        fade = r'{\fad(0,180)}' if a == 0 else r'{\fad(220,180)\move(540,230,540,190,0,260)}'
        ev.append(f'Dialogue: 0,{ass_t(a)},{ass_t(b)},Head,,0,0,0,,{fade}{t.replace("{\\N}", chr(92) + "N")}')
    ev.append(f'Dialogue: 0,{ass_t(total - 5)},{ass_t(total)},Head,,0,0,0,,{{\\fad(220,0)}}eventos.inema.pro\\N{AMB}/codex-claude')
    ev.append(f'Dialogue: 1,{ass_t(total - 5)},{ass_t(total)},Cta,,0,0,0,,{{\\fad(220,0)}}Saiba mais no inema.club')
    caps = cut_cues(V2 / 'final/pt-b01/captions.srt', segs1)
    off = sum(b - a for a, b in segs1)
    caps += [(off + s - seg2[0], off + min(e, seg2[1]) - seg2[0], t) for s, e, t in cues(V2 / 'final/pt-b02/captions.srt') if seg2[0] - .05 <= s < seg2[1] - .05]
    for s, e, t in caps:
        ev.append(f'Dialogue: 2,{ass_t(s)},{ass_t(e)},Cap,,0,0,0,,{t}')
    ass = OUT / 'final/reel.ass'; ass.write_text(ASS_HEAD + '\n'.join(ev) + '\n')
    dest = OUT / 'final/codex-claude-reel-9x16.mp4'
    av1, av2 = V1 / 'assets/nei-pt-b01.mp4', V1 / 'assets/nei-pt-b02.mp4'
    ex1, ex2 = V2 / 'final/pt-b01.mp4', V2 / 'final/pt-b02.mp4'
    (a1, b1), (a2, b2) = (0, B1[2]), seg2
    fc = (f'[0:v]trim={a1}:{b1},setpts=PTS-STARTPTS,fps=30[av1];[1:v]trim={a2}:{b2},setpts=PTS-STARTPTS,fps=30[av2];'
          f'[av1][av2]concat=n=2:v=1:a=0,scale=1080:608,setsar=1[av];'
          f'[2:v]trim={a1}:{b1},setpts=PTS-STARTPTS,fps=30[ex1];[3:v]trim={a2}:{b2},setpts=PTS-STARTPTS,fps=30[ex2];'
          f'[ex1][ex2]concat=n=2:v=1:a=0,crop=1440:944:0:0,scale=1080:708,setsar=1[ex0];'
          f'[4:v]trim=start=3.5:duration=0.04,setpts=PTS-STARTPTS,crop=1440:944:0:0,scale=1080:708,setsar=1,loop=loop=40:size=1,setpts=N/30/TB[cov];'
          f"[ex0][cov]overlay=0:0:enable='lt(t,1.2)'[ex];"
          f'[2:a]atrim={a1}:{b1},asetpts=PTS-STARTPTS[x1];[3:a]atrim={a2}:{b2},asetpts=PTS-STARTPTS[x2];[x1][x2]concat=n=2:v=0:a=1[a];'
          f'color=c=0x0D1321:s=1080x1920:r=30:d={total:.3f}[bg];'
          f'[bg][av]overlay=0:520[o1];[o1][ex]overlay=0:1140[o2];'
          f'[o2]drawbox=x=0:y=517:w=1080:h=4:color=0xFFC300@0.9:t=fill,drawbox=x=0:y=1128:w=1080:h=4:color=0xFFC300@0.9:t=fill,'
          f"subtitles='{ass}'[v]")
    ff('-i', str(av1), '-i', str(av2), '-i', str(ex1), '-i', str(ex2), '-i', str(ex1), '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{total:.3f}',
       '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(dest))
    dest.with_suffix('.srt').write_text('\n'.join(f'{i + 1}\n{st(s)} --> {st(e)}\n{t}\n' for i, (s, e, t) in enumerate(caps)))
    return dest


if __name__ == '__main__':
    import sys
    for f in (essencial, reel) if len(sys.argv) < 2 else [globals()[sys.argv[1]]]:
        d = f()
        p = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', str(d)]))
        print(d.name, round(float(p['format']['duration']), 2), [(s['codec_type'], s.get('width'), s.get('height')) for s in p['streams']])
