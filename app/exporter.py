from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import os

def rows(result):
    out=[]
    for r in result.get("items",[]):
        value=r.get("value",r.get("quantity",0))
        name=r.get("name",r.get("member",""))
        out.append([str(r.get("row","")),r.get("section",""),r.get("member",""),name,
                    f"{float(value):,.3f}",r.get("unit",""),r.get("note","")])
    return out

def _rebar_type_rows(result):
    groups=defaultdict(lambda: {"pieces":0,"length":0.0,"weight":0.0,"branches":0,"buy_weight":0.0,"buy_length":0.0})
    for m in result.get("members",[]):
        for c in m.get("components",[]):
            if c.get("category")!="میلگرد": continue
            name=str(c.get("name",""))
            dia=c.get("diameter_mm")
            if dia is None: continue
            base=name.split(" - ")[0]
            g=groups[(base,float(dia))]
            if name.endswith(" - تعداد قطعه"): g["pieces"] += int(c.get("value",0))
            elif name.endswith(" - طول اجرا"):
                g["length"] += float(c.get("value",0))
            elif name.endswith(" - وزن اجرا"):
                g["weight"] += float(c.get("value",0))
            elif name.endswith(" - شاخه خرید"):
                g["branches"] += int(c.get("value",0))
                g["buy_weight"] += float(c.get("procurement_weight_kg",0))
            elif name.endswith(" - طول خرید"):
                g["buy_length"] += float(c.get("value",0))
    return [(k[0],k[1],v) for k,v in groups.items()]

def _rebar_diameter_rows(result):
    out=[]
    for dia,data in result.get("rebar_by_diameter",{}).items():
        out.append([f"Φ{dia}",data.get("length_m",0),data.get("weight_kg",0),
                    data.get("branches",0),data.get("procurement_length_m",0),
                    data.get("procurement_weight_kg",0)])
    return out

def _style_sheet(ws):
    thin=Side(style="thin",color="B7B7B7")
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment=Alignment(vertical="top",wrap_text=True)
            cell.border=Border(bottom=thin)
    for cell in ws[1]:
        cell.font=Font(bold=True)
    ws.freeze_panes="A2"
    ws.auto_filter.ref=ws.dimensions
    for col in ws.columns:
        letter=get_column_letter(col[0].column)
        width=min(max(max(len(str(c.value or "")) for c in col)+2,12),42)
        ws.column_dimensions[letter].width=width

def create_excel(result,project_name,path):
    wb=Workbook()
    ws=wb.active; ws.title="خلاصه پروژه"
    ws.append(["گزارش جامع متره و برآورد"]); ws.append(["پروژه",project_name])
    ws.append(["تعداد اعضا",result.get("member_count",0)])
    ws.append(["حجم کل بتن (m³)",result.get("concrete_total_m3",0)])
    total_rebar=sum(float(x.get("weight_kg",0)) for x in result.get("rebar_by_diameter",{}).values())
    total_buy=sum(float(x.get("procurement_weight_kg",0)) for x in result.get("rebar_by_diameter",{}).values())
    total_bars=sum(int(x.get("branches",0)) for x in result.get("rebar_by_diameter",{}).values())
    ws.append(["وزن کل میلگرد اجرا (kg)",total_rebar])
    ws.append(["وزن کل میلگرد خرید (kg)",total_buy])
    ws.append(["تعداد کل شاخه خرید",total_bars])
    ps=result.get("project_settings",{})
    ws.append(["استاندارد",ps.get("standard","")])
    ws.append(["زبان",ps.get("language","")])
    _style_sheet(ws)

    detail=wb.create_sheet("متره کامل")
    detail.append(["ردیف","بخش","عضو","آیتم","مقدار","واحد","توضیحات"])
    for row in rows(result): detail.append(row)
    _style_sheet(detail)

    rb=wb.create_sheet("جمع میلگرد - تفکیک نوع")
    rb.append(["نوع میلگرد","قطر","تعداد قطعه","طول اجرا (m)","وزن اجرا (kg)","شاخه خرید","طول خرید (m)","وزن خرید (kg)"])
    for base,dia,g in _rebar_type_rows(result):
        rb.append([base,f"Φ{dia:g}",g["pieces"],g["length"],g["weight"],g["branches"],g["buy_length"],g["buy_weight"]])
    _style_sheet(rb)

    rd=wb.create_sheet("خلاصه خرید بر اساس قطر")
    rd.append(["قطر","طول اجرا (m)","وزن اجرا (kg)","شاخه خرید","طول خرید (m)","وزن خرید (kg)"])
    for row in _rebar_diameter_rows(result): rd.append(row)
    _style_sheet(rd)

    concrete=wb.create_sheet("خلاصه بتن")
    concrete.append(["پروژه",project_name])
    concrete.append(["حجم کل بتن (m³)",result.get("concrete_total_m3",0)])
    concrete.append(["تعداد اعضا",result.get("member_count",0)])
    _style_sheet(concrete)

    qa_ws=wb.create_sheet("کنترل کیفیت")
    qa_ws.append(["وضعیت","توضیح"])
    qa=result.get("qa",{})
    if qa.get("ok"): qa_ws.append(["OK","کنترل اولیه متره بدون هشدار"])
    else:
        for warning in qa.get("warnings",[]): qa_ws.append(["WARNING",warning])
    _style_sheet(qa_ws)

    cl=wb.create_sheet("Cut List")
    cl.append(["قطر","شاخه استاندارد","تعداد قطعات","طول مصرفی (m)","پرت برش (m)"])
    for dia,data in result.get("cut_list",{}).items():
        cl.append([f"Φ{dia}",data.get("stock_bars",0),data.get("pieces_count",0),
                   data.get("used_length_m",0),data.get("waste_length_m",0)])
    _style_sheet(cl)

    units=wb.create_sheet("جمع‌بندی واحدها")
    units.append(["واحد","جمع مقدار"])
    for k,v in result.get("totals_by_unit",{}).items(): units.append([k,v])
    _style_sheet(units)

    ai= result.get("ai_explanation")
    if ai:
        aiws=wb.create_sheet("توضیح هوشمند")
        aiws.append(["توضیح هوشمند"]); aiws.append([ai])
        aiws.column_dimensions["A"].width=110
        aiws["A2"].alignment=Alignment(wrap_text=True,vertical="top")

    wb.save(path); return path

def _pdf_font():
    candidates=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("StructuralBotFont",p))
                return "StructuralBotFont"
            except Exception: pass
    return "Helvetica"

def create_pdf(result,project_name,path):
    doc=SimpleDocTemplate(path,pagesize=landscape(A4),rightMargin=24,leftMargin=24,topMargin=24,bottomMargin=24)
    font=_pdf_font()
    styles=getSampleStyleSheet()
    title=ParagraphStyle("SBTitle",parent=styles["Title"],fontName=font,alignment=TA_CENTER,fontSize=18,leading=22)
    body=ParagraphStyle("SBBody",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=11)
    head=ParagraphStyle("SBHead",parent=styles["Heading2"],fontName=font,fontSize=13,leading=16,alignment=TA_RIGHT)
    story=[Paragraph("گزارش جامع متره و برآورد",title),
           Paragraph(f"پروژه: {project_name}",body),Spacer(1,10)]

    total_rebar=sum(float(x.get("weight_kg",0)) for x in result.get("rebar_by_diameter",{}).values())
    total_buy=sum(float(x.get("procurement_weight_kg",0)) for x in result.get("rebar_by_diameter",{}).values())
    total_bars=sum(int(x.get("branches",0)) for x in result.get("rebar_by_diameter",{}).values())
    summary=[
        ["تعداد اعضا","بتن کل (m³)","وزن میلگرد اجرا (kg)","شاخه خرید","وزن میلگرد خرید (kg)"],
        [result.get("member_count",0),f"{result.get('concrete_total_m3',0):,.3f}",f"{total_rebar:,.2f}",total_bars,f"{total_buy:,.2f}"]
    ]
    t=Table(summary,colWidths=[70,95,120,80,120])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTNAME",(0,0),(-1,-1),font),("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story += [t,Spacer(1,14),Paragraph("متره کامل",head)]
    data=[["ردیف","بخش","عضو","آیتم","مقدار","واحد","توضیحات"]]+rows(result)
    data=[[Paragraph(str(x),body) for x in row] for row in data]
    table=Table(data,repeatRows=1,colWidths=[30,60,75,180,65,45,180])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.35,colors.grey),("FONTNAME",(0,0),(-1,-1),font),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story += [table,PageBreak(),Paragraph("جمع کل میلگرد — تفکیک نوع",head)]
    rb=[["نوع میلگرد","قطر","تعداد قطعه","طول اجرا","وزن اجرا","شاخه خرید","طول خرید","وزن خرید"]]
    for base,dia,g in _rebar_type_rows(result):
        rb.append([base,f"Φ{dia:g}",g["pieces"],f"{g['length']:.2f}",f"{g['weight']:.2f}",g["branches"],f"{g['buy_length']:.2f}",f"{g['buy_weight']:.2f}"])
    rb=[[Paragraph(str(x),body) for x in row] for row in rb]
    rt=Table(rb,repeatRows=1,colWidths=[150,45,65,75,75,65,75,75])
    rt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.35,colors.grey),("FONTNAME",(0,0),(-1,-1),font),("ALIGN",(1,1),(-1,-1),"CENTER")]))
    story += [rt,Spacer(1,14),Paragraph("خلاصه خرید بر اساس قطر",head)]
    rd=[["قطر","طول اجرا","وزن اجرا","شاخه خرید","طول خرید","وزن خرید"]]
    for row in _rebar_diameter_rows(result): rd.append([str(x) for x in row])
    rd=[[Paragraph(str(x),body) for x in row] for row in rd]
    rdt=Table(rd,repeatRows=1)
    rdt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.35,colors.grey),("FONTNAME",(0,0),(-1,-1),font),("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story += [rdt,Spacer(1,14),Paragraph("کنترل کیفیت و یادداشت",head)]
    qa=result.get("qa",{})
    story.append(Paragraph("وضعیت کنترل: "+("بدون هشدار" if qa.get("ok") else f"{len(qa.get('warnings',[]))} هشدار"),body))
    for w in qa.get("warnings",[])[:12]: story.append(Paragraph("⚠ "+str(w),body))
    story.append(Spacer(1,8))
    if result.get("ai_explanation"):
        story += [Paragraph("توضیح هوشمند",head),Paragraph(str(result["ai_explanation"]),body),Spacer(1,8)]
    story.append(Paragraph("مقادیر بر اساس اطلاعات واردشده از نقشه تهیه شده‌اند و باید با مدارک مصوب پروژه کنترل شوند.",body))
    doc.build(story); return path
