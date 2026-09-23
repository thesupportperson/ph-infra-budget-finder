def review_label(score):
    if score is None: return "Unreviewed"
    if score >= .70: return "Needs Manual Review"
    if score >= .40: return "Maybe Review"
    return "Low Priority"

def peso(amount):
    return f"₱{float(amount or 0):,.0f}"

def normalize_type(title):
    title = (title or "").lower()
    for word, kind in [("flood", "flood_control"), ("bridge", "bridge"), ("drain", "drainage"), ("road", "road"), ("water", "water_system"), ("hospital", "hospital_health_facility"), ("school", "school_facility"), ("building", "public_building")]:
        if word in title: return kind
    return "unknown"
