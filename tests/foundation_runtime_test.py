import bot
from app.foundation_takeoff import calculate_foundation_takeoff

v=[2,2.0,1.8,0.45,12,20,10,25,4,1.0,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
r=bot.calc_member("فونداسیون","پی منفرد",v)
assert abs(next(x for x in r if x["name"]=="بتن فونداسیون")["value"]-3.24)<1e-9
assert next(x for x in r if x["name"]=="میلگرد شبکه پایین - X - تعداد قطعه")["value"]>0
assert next(x for x in r if x["name"]=="میلگرد شبکه بالا - X - تعداد قطعه")["value"]>0
r2=calculate_foundation_takeoff({"foundation_type":"پی منفرد","count":2,"length":2,"width":2,"thickness":.5,"blinding_thickness":.1,"working_space_m":.2,"excavation_depth_m":.8,"formwork_mode":"all","chair_count":20,"spacer_count":40,"anchor_bolt_count":8})
assert r2["totals"]["concrete_m3"]==4
assert r2["totals"]["blinding_m3"]==.8
assert r2["totals"]["formwork_m2"]==8
print("FOUNDATION_RUNTIME_OK")
