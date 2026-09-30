from app.foundation_takeoff import calculate_foundation_takeoff, foundation_components

def test_isolated_foundation_full_takeoff():
    r=calculate_foundation_takeoff({"foundation_type":"پی منفرد","count":2,"length":2,"width":2,"thickness":.5,
      "blinding_thickness":.1,"working_space_m":.2,"excavation_depth_m":.8,"formwork_mode":"all",
      "bottom_dia_mm":16,"bottom_spacing_cm":20,"top_dia_mm":12,"top_spacing_cm":25,
      "dowel_count":8,"dowel_length_m":1.2,"dowel_dia_mm":16,"chair_count":20,"spacer_count":40,"anchor_bolt_count":8})
    assert r["totals"]["concrete_m3"]==4
    assert r["totals"]["blinding_m3"]==.8
    assert r["totals"]["earthwork_m3"]==2*2.4*2.4*.8
    assert r["totals"]["formwork_m2"]==8
    assert r["totals"]["rebar_kg"]>0
    assert len(r["reinforcement"])==5
    assert any(q["name"]=="خرک" for q in r["quantities"])
    assert any(c["category"]=="میلگرد" for c in foundation_components(r))

def test_soil_contact_has_no_formwork_by_default():
    r=calculate_foundation_takeoff({"foundation_type":"پی نواری","count":1,"length":10,"width":.6,"thickness":.5})
    assert r["totals"]["formwork_m2"]==0
