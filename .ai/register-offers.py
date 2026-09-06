import json
from pathlib import Path
p=Path('design/spec.json')
s=json.loads(p.read_text(encoding='utf-8'))
items={
 'offers-heading':('.offers-title',{'width':'1260px','height':'95px','font-size':'90px','line-height':'95px','font-weight':'500','color':'#847F57','text-align':'center'}),
 'offers-grid':('.page-promotions .promos',{'width':'1260px','height':'1690px','gap':'24px'}),
 'offers-card':('.page-promotions .promo',{'width':'404px','height':'540px','padding-top':'20px','padding-left':'20px','padding-bottom':'40px','border-radius':'20px','background-color':'#847F57'}),
 'offers-image':('.page-promotions .promo__media .ph',{'width':'360px','height':'220px','border-radius':'10px'}),
 'offers-card-title':('.page-promotions .promo__title',{'width':'364px','height':'50px','font-size':'24px','line-height':'25px','font-weight':'400'}),
 'offers-card-text':('.page-promotions .promo__text',{'font-size':'18px','line-height':'22px','color':'#F7F0E6'}),
 'offers-booking':('.page-promotions .promo__book',{'width':'364px','height':'50px','font-size':'18px','line-height':'22px','font-weight':'500','color':'#494949'}),
}
for key,(selector,props) in items.items():
 s['components'][key]={'selector':selector,'viewport':1440,'page':'/akcii/','props':{k:{'value':v,'source':'inspector','node':'Special Offers / user CSS 06.09.2026'} for k,v in props.items()}}
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
