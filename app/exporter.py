from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def rows(result):
    return [[str(r["row"]),r["section"],r["name"],f'{r["quantity"]:,.3f}',r["unit"],r.get("note","")] for r in result.get("items",[])]

def create_excel(result,project_name,path):
    wb=Workbook(); ws=wb.active; ws.title="متره جامع"
    ws.append(["پروژه",project_name]); ws.append([]); ws.append(["ردیف","بخش","آیتم","مقدار","واحد","توضیحات"])
    for c in ws[3]: c.font=Font(bold=True)
    for row in rows(result): ws.append(row)
    for col in ws.columns:
        letter=col[0].column_letter; ws.column_dimensions[letter].width=min(max(max(len(str(c.value or "")) for c in col)+2,12),35)
    ws.freeze_panes="A4"; s=wb.create_sheet("جمع‌بندی"); s.append(["واحد","جمع مقدار"])
    for k,v in result.get("totals_by_unit",{}).items(): s.append([k,v])
    wb.save(path); return path

def create_pdf(result,project_name,path):
    doc=SimpleDocTemplate(path,pagesize=landscape(A4),rightMargin=24,leftMargin=24,topMargin=24,bottomMargin=24)
    styles=getSampleStyleSheet(); story=[Paragraph(f"Concrete Building Quantity Takeoff - {project_name}",styles["Title"]),Spacer(1,12)]
    data=[["No.","Section","Item","Quantity","Unit","Note"]]+rows(result)
    table=Table(data,repeatRows=1); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.5,colors.grey),("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story += [table,Spacer(1,12),Paragraph(" | ".join(f"{k}: {v:,.3f}" for k,v in result.get("totals_by_unit",{}).items()),styles["BodyText"])]
    story += [Spacer(1,8),Paragraph("مقادیر بر اساس اطلاعات واردشده از نقشه تهیه شده‌اند و نیازمند کنترل مدارک مصوب پروژه هستند.",styles["BodyText"])]
    doc.build(story); return path
