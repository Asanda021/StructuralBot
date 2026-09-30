from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def rows(result):
    out=[]
    for r in result.get("items",[]):
        value=r.get("value",r.get("quantity",0))
        name=r.get("name",r.get("member",""))
        out.append([str(r.get("row","")),r.get("section",""),r.get("member",""),name,
                    f"{float(value):,.3f}",r.get("unit",""),r.get("note","")])
    return out

def create_excel(result,project_name,path):
    wb=Workbook(); ws=wb.active; ws.title="متره جامع"
    ws.append(["پروژه",project_name]); ws.append([])
    ws.append(["ردیف","بخش","عضو","آیتم","مقدار","واحد","توضیحات"])
    for c in ws[3]: c.font=Font(bold=True)
    for row in rows(result): ws.append(row)
    for col in ws.columns:
        letter=col[0].column_letter
        ws.column_dimensions[letter].width=min(max(max(len(str(c.value or "")) for c in col)+2,12),35)
    ws.freeze_panes="A4"

    s=wb.create_sheet("خلاصه بتن")
    s.append(["پروژه",project_name]); s.append(["حجم کل بتن (m³)",result.get("concrete_total_m3",0)])
    s.append(["تعداد اعضا",result.get("member_count",0)])
    s.append(["تعداد آیتم‌ها",result.get("item_count",0)])
    s.append(["وضعیت کنترل", "بدون هشدار" if result.get("qa",{}).get("ok") else f"هشدار: {len(result.get('qa',{}).get('warnings',[]))}"])

    q=wb.create_sheet("کنترل کیفیت")
    q.append(["وضعیت","توضیح"])
    qa=result.get("qa",{})
    if qa.get("ok"):
        q.append(["OK","کنترل اولیه متره بدون هشدار"])
    else:
        for warning in qa.get("warnings",[]): q.append(["WARNING",warning])

    r=wb.create_sheet("خلاصه میلگرد")
    r.append(["قطر","وزن اجرا (kg)","طول اجرا (m)","طول خرید (m)","شاخه 12m","وزن خرید (kg)"])
    for c in r[1]: c.font=Font(bold=True)
    for dia,data in result.get("rebar_by_diameter",{}).items():
        r.append([f"Φ{dia}",data.get("weight_kg",0),data.get("length_m",0),
                  data.get("procurement_length_m",0),data.get("branches",0),
                  data.get("procurement_weight_kg",0)])

    cl=wb.create_sheet("Cut List")
    cl.append(["قطر","شاخه 12m","تعداد قطعات","طول مصرفی (m)","پرت برش (m)"])
    for c in cl[1]: c.font=Font(bold=True)
    for dia,data in result.get("cut_list",{}).items():
        cl.append([f"Φ{dia}",data.get("stock_bars",0),data.get("pieces_count",0),
                   data.get("used_length_m",0),data.get("waste_length_m",0)])

    s2=wb.create_sheet("جمع‌بندی واحدها")
    s2.append(["واحد","جمع مقدار"])
    for k,v in result.get("totals_by_unit",{}).items(): s2.append([k,v])
    wb.save(path); return path

def create_pdf(result,project_name,path):
    doc=SimpleDocTemplate(path,pagesize=landscape(A4),rightMargin=24,leftMargin=24,topMargin=24,bottomMargin=24)
    styles=getSampleStyleSheet()
    story=[Paragraph(f"Concrete Building Quantity Takeoff - {project_name}",styles["Title"]),Spacer(1,12)]
    data=[["No.","Section","Member","Item","Quantity","Unit","Note"]]+rows(result)
    table=Table(data,repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
                                ("GRID",(0,0),(-1,-1),0.5,colors.grey),
                                ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story += [table,Spacer(1,12),
              Paragraph(f"Concrete total: {result.get('concrete_total_m3',0):,.3f} m³",styles["BodyText"]),
              Spacer(1,6),
              Paragraph(" | ".join(f"Φ{k}: {v.get('stock_bars',0)} bars / {v.get('waste_length_m',0):,.2f} m waste" for k,v in result.get("cut_list",{}).items()),styles["BodyText"]),
              Spacer(1,8),
              Paragraph(f"QA: {'OK' if result.get('qa',{}).get('ok') else 'WARNING'}",styles["BodyText"]),
              Spacer(1,6),
              Paragraph(" | ".join(result.get("qa",{}).get("warnings",[])[:8]),styles["BodyText"]),
              Spacer(1,8),
              Paragraph("مقادیر بر اساس اطلاعات واردشده از نقشه تهیه شده‌اند و نیازمند کنترل مدارک مصوب پروژه هستند.",styles["BodyText"])]
    doc.build(story); return path
