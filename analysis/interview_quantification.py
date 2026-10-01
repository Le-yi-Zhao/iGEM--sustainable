"""Deterministic keyword counts and transparent rule-based interview themes.

Uses Pillow for charts on Windows or Linux; no network, LLM scoring or imputation.
Run from the repository root, or pass a site/export root as the first argument.
"""
import csv
import hashlib
import html
import json
import math
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DATA='data/human_practices'
TABLES='results/tables/human_practices'
FIG='figures/human_practices'

def pattern(aliases):
    parts=[]
    for term in sorted(set(aliases),key=lambda t:(-len(t),t)):
        escaped=re.escape(term)
        parts.append(r'(?<![A-Za-z])'+escaped+r'(?![A-Za-z])' if re.fullmatch('[A-Za-z ]+',term) else escaped)
    return re.compile('|'.join(parts),re.I)

def csv_write(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)

def analyze(root):
    corpus_path=root/DATA/'professor_corpus.json';codebook_path=root/DATA/'interview_codebook.json'
    corpus=json.loads(corpus_path.read_text(encoding='utf-8'))
    book=json.loads(codebook_path.read_text(encoding='utf-8'))
    records=corpus['records'];out=root/TABLES;out.mkdir(parents=True,exist_ok=True)
    assert len(records)==len({r['id'] for r in records})
    occurrences=[];keywords=[]
    for keyword in book['keywords']:
        rx=pattern(keyword['aliases']);hits=[]
        for record in records:
            for m in rx.finditer(record['text']):
                row={'keyword':keyword['label'],'record_id':record['id'],'section':record['section'],
                     'matched_text':m.group(),'start':m.start(),'end':m.end(),
                     'context':record['text'][max(0,m.start()-20):m.end()+20]}
                hits.append(row);occurrences.append(row)
        keywords.append({'keyword':keyword['label'],'count':len(hits),'segment_count':len({h['record_id'] for h in hits}),
                         'aliases':'；'.join(keyword['aliases'])})
    keywords.sort(key=lambda r:(-r['count'],r['keyword']))
    themes=[];matrix=[]
    for theme in book['themes']:
        rx=pattern(theme['terms']);positive=[]
        for record in records:
            matches=list(rx.finditer(record['text']))
            if matches:positive.append(record['id'])
            matrix.append({'record_id':record['id'],'section':record['section'],'theme_id':theme['id'],
                           'theme':theme['label'],'hit':int(bool(matches)),
                           'matched_terms':'；'.join(dict.fromkeys(m.group() for m in matches))})
        themes.append({'theme_id':theme['id'],'theme':theme['label'],'segment_count':len(positive),
                       'denominator':len(records),'segment_percent':100*len(positive)/len(records),
                       'record_ids':'；'.join(positive),'rules':'；'.join(theme['terms'])})
    themes.sort(key=lambda r:(-r['segment_count'],r['theme_id']))
    csv_write(out/'interview_keyword_counts.csv',keywords,['keyword','count','segment_count','aliases'])
    csv_write(out/'interview_keyword_occurrences.csv',occurrences,['keyword','record_id','section','matched_text','start','end','context'])
    csv_write(out/'interview_theme_counts.csv',themes,['theme_id','theme','segment_count','denominator','segment_percent','record_ids','rules'])
    csv_write(out/'interview_theme_matrix.csv',matrix,['record_id','section','theme_id','theme','hit','matched_terms'])
    meta={'interviews':1,'professor_segments':len(records),'keyword_entries':len(keywords),
          'nonzero_keyword_entries':sum(k['count']>0 for k in keywords),'themes':len(themes),
          'source_selection':corpus['selection'],'excluded':corpus['excluded'],
          'method':book['method'],'interpretation':book['interpretation'],
          'source_sha256':hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
          'codebook_sha256':hashlib.sha256(codebook_path.read_bytes()).hexdigest(),
          'keyword_total_is_token_count':False,'theme_categories_are_mutually_exclusive':False,
          'source_technical_claims_verified_by_this_analysis':False,'independent_coding_validation':False,
          'charts':'Python/Pillow numeric plots, not image generation'}
    (out/'interview_quantification_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return corpus,book,keywords,themes,matrix,meta

class Figure:
    def __init__(self,w,h,title,subtitle):
        self.w=w;self.h=h;self.image=Image.new('RGB',(w,h),'#fcfaf7');self.draw=ImageDraw.Draw(self.image)
        choices=['C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf']
        self.font_path=next((p for p in choices if Path(p).exists()),None)
        if not self.font_path:raise FileNotFoundError('A Chinese font is required')
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title><desc>{html.escape(subtitle)}</desc><rect width="{w}" height="{h}" fill="#fcfaf7"/>']
        self.text(65,42,title,48);self.text(67,119,subtitle,25,'#586b61')
    def font(self,size):return ImageFont.truetype(self.font_path,size)
    def text(self,x,y,value,size=28,color='#244137'):
        self.draw.text((x,y),value,font=self.font(size),fill=color,anchor='lt')
        self.svg.append(f'<text x="{x:.1f}" y="{y:.1f}" dominant-baseline="text-before-edge" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" fill="{color}">{html.escape(str(value))}</text>')
    def rect(self,x,y,w,h,fill):
        self.draw.rectangle((x,y,x+w,y+h),fill=fill)
        self.svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"/>')
    def line(self,x1,y1,x2,y2,color='#ccd7ce',width=2):
        self.draw.line((x1,y1,x2,y2),fill=color,width=width)
        self.svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"/>')
    def save(self,root,name):
        out=root/FIG;out.mkdir(parents=True,exist_ok=True)
        self.image.save(out/(name+'.png'))
        (out/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>'])+'\n',encoding='utf-8')

def plot(root,keywords,themes,n):
    positive=[r for r in keywords if r['count']]
    f=Figure(1800,1060,'教授访谈关键词词云','单份访谈 · 14 段明确归属教授的相关发言 · 固定词表匹配')
    maximum=positive[0]['count'];placed=None
    for scale in [1,.95,.90,.85,.80,.75,.70]:
        boxes=[];layout=[]
        for index,row in enumerate(positive):
            size=round(scale*(28+140*math.sqrt(row['count']/maximum)))
            bounds=f.font(size).getbbox(row['keyword'],anchor='lt');w=bounds[2]+10;h=bounds[3]+12
            found=False
            for step in range(8000):
                angle=step*.27+index*.9;radius=step*.18
                x=900+radius*1.75*math.cos(angle)-w/2;y=590+radius*.83*math.sin(angle)-h/2
                if x<65 or x+w>1735 or y<210 or y+h>920:continue
                box=(x-8,y-8,x+w+8,y+h+8)
                if any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in boxes):continue
                boxes.append(box);layout.append((x,y,size,row));found=True;break
            if not found:break
        if len(layout)==len(positive):placed=layout;break
    if placed is None:raise RuntimeError('Word cloud placement incomplete')
    palette=['#244137','#39745f','#54768b','#8b6349']
    for i,(x,y,size,row) in enumerate(placed):f.text(x,y,row['keyword'],size,palette[i%len(palette)])
    f.text(67,956,'字号随提及次数增加；颜色不编码类别。词频不代表重要性、赞同度或实验效果。',25,'#586b61')
    f.text(67,996,'“自然形成”与“自然环境”等语境差异保留在原文定位表中。',23,'#586b61')
    f.save(root,'interview_wordcloud')

    top=positive[:15];f=Figure(1800,1160,'教授反复提到哪些技术与研究概念？','前 15 个关键词 · 数值为原文提及次数，同一段中重复出现分别计数')
    x0=450;max_width=1160;row_height=54
    for tick in range(0,maximum+1,5):
        x=x0+max_width*tick/maximum;f.line(x,211,x,1042)
        f.text(x-10,1055,str(tick),23,'#586b61')
    for i,r in enumerate(top):
        y=220+i*row_height;f.text(70,y+2,r['keyword'],30)
        width=max_width*r['count']/maximum;f.rect(x0,y,width,33,'#39745f')
        f.text(x0+width+15,y,str(r['count']),29)
    f.text(950,1092,'提及次数（次）',27)
    f.text(67,1129,'例如“人工智能”合并 AI 与人工智能；“实验”包含干实验和湿实验中的该词。',22,'#586b61')
    f.save(root,'interview_keyword_frequency')

    f=Figure(1800,950,'教授发言覆盖了哪些主题？',f'规则命中的发言片段数 / 纳入片段数（n={n}） · 同一片段可涉及多个主题')
    x0=535;max_width=955
    for tick in range(0,n+1,2):
        x=x0+max_width*tick/n;f.line(x,215,x,803);f.text(x-8,817,str(tick),23,'#586b61')
    for i,r in enumerate(themes):
        y=230+i*70;f.text(70,y+1,r['theme'],30);width=max_width*r['segment_count']/n
        f.rect(x0,y,width,41,'#39745f');f.text(x0+width+16,y+2,f'{r["segment_count"]}/{n}  ({r["segment_percent"]:.1f}%)',27)
    f.text(800,860,'命中的发言片段数（段）',26)
    f.text(67,906,'主题非互斥，百分比不合计为 100%；关键词命中不等同于理解、认可或议题重要性。',23,'#586b61')
    f.save(root,'interview_theme_coverage')

def section(root):
    with (root/TABLES/'interview_keyword_counts.csv').open(encoding='utf-8-sig') as f:keywords=list(csv.DictReader(f))
    with (root/TABLES/'interview_theme_counts.csv').open(encoding='utf-8-sig') as f:themes=list(csv.DictReader(f))
    def fig(name,caption):
        return f'<figure class="figure"><a href="{FIG}/{name}.png"><img loading="lazy" src="{FIG}/{name}.svg" alt="{html.escape(caption)}"></a><figcaption>{caption}</figcaption></figure>'
    summary='、'.join(f'{html.escape(r["keyword"])}（{r["count"]} 次）' for r in keywords[:3])
    body=f'''<div id="interview-quantification"><h3>访谈量化｜哪些概念被反复提及？</h3>
<p>统计一份转写中明确归属教授、与研究和表达相关的 <b>14 段发言</b>。采用固定关键词表和公开主题规则，保留每次命中的原文位置。较高频词包括 {summary}。</p>
<p>学生发言、混合说话人的开场段、人物照片建议，以及“反应原理与策略”中未明确标记说话人的两段文字未纳入。统计范围与前面的八项建议摘录不同。</p>'''
    body+=fig('interview_wordcloud','关键词词云：字号随原文提及次数增加。它描述所选教授发言的用词，不表示观点的重要性、态度或项目效果。')
    body+=fig('interview_keyword_frequency','前 15 个关键词的提及次数。AI 与人工智能等按词表归并；每一词条内部不重复计数，不同词条可嵌套。')
    body+=fig('interview_theme_coverage','八类主题的发言覆盖。分母固定为 14 段；同一段可命中多个主题，百分比不是互斥份额。')
    body+='''<details class="hp-feedback"><summary>查看统计方法与语境限制</summary><p>本轮为探索性固定词表匹配，不是情感分析或独立编码者验证。关键词共现、频次和规则命中都不能证明认同、因果关系或公众共识。</p><ul>
<li>按原转写的教授发言块计段，不按句号拆分；较长发言更容易命中多个主题。</li>
<li>“实验”计入干实验和湿实验中的词；“酶”计入酶催化等复合词。词频总和不是完整分词后的总词数。</li>
<li>P03 中 AI 用于讨论依赖工具，P09 中“通用性”出现在暂缓讨论的建议中；命中不代表赞同。</li>
<li>P10 的“自然形成”与“让自然有更多空间”含义不同；资源生态主题不会仅由“自然”一词自动触发。</li>
<li>原文中的科学主张不因被计数而得到验证，仍按上方访谈核对说明处理。</li></ul></details>
<div class="downloads">'''
    for path,label in [('interview_keyword_counts.csv','关键词计数与归并规则'),('interview_keyword_occurrences.csv','每次命中的原文位置'),('interview_theme_counts.csv','主题覆盖计数'),('interview_theme_matrix.csv','逐段主题矩阵'),('interview_quantification_metadata.json','统计口径与来源校验')]:
        body+=f'<a href="{TABLES}/{path}">{label}</a>'
    body+=f'<a href="{DATA}/professor_corpus.json">纳入的 14 段教授原文</a><a href="{DATA}/interview_codebook.json">完整关键词表与主题规则</a></div></div>'
    return body

def integrate(root,page):
    if 'id="interview-quantification"' in page:raise ValueError('Quantification already integrated')
    marker='<h3>二、干湿迭代如何落地</h3>'
    if page.count(marker)!=1:raise ValueError('Interview section marker missing')
    return page.replace(marker,section(root)+marker,1)

def run(root):
    corpus,book,keywords,themes,matrix,meta=analyze(root)
    plot(root,keywords,themes,len(corpus['records']))
    return meta

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    result=run(root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
