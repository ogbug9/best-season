from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset
from pathlib import Path
root=Path('config/static/fonts')
for script in ('latin','cyrillic'):
    chars=TTFont(root/f'montserrat-400-{script}.woff2').getBestCmap().keys()
    font=instantiateVariableFont(TTFont('.ai/Montserrat-variable.ttf'), {'wght':500}, inplace=True)
    opts=subset.Options()
    sub=subset.Subsetter(options=opts)
    sub.populate(unicodes=chars)
    sub.subset(font)
    font.flavor='woff2'
    font.save(root/f'montserrat-500-{script}.woff2')
p=Path('config/static/css/fonts.css')
s=p.read_text(encoding='utf-8')
start=s.index('@font-face {')
end=s.index('@font-face {',s.index('@font-face {', start+1)+1)
block=s[start:end].replace('font-weight: 400','font-weight: 500').replace('montserrat-400','montserrat-500')
s=s[:end]+block+s[end:]
p.write_text(s,encoding='utf-8')
