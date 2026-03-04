import math

EARTH_R = 6371.0

def haversine_km(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return 2 * EARTH_R * math.asin(math.sqrt(a))

def danger_score_to_level(score):
    if score >= 0.85: return "critical"
    if score >= 0.65: return "high"
    if score >= 0.40: return "medium"
    if score >= 0.20: return "low"
    return "safe"

def wilson_score(pos, total):
    if total == 0: return 0.5
    import math
    z = 1.96
    p = pos / total
    return (p + z*z/(2*total) - z * math.sqrt((p*(1-p) + z*z/(4*total))/total)) / (1 + z*z/total)

def calculate_credibility_score(confirmations, contradictions):
    total = confirmations + contradictions
    if total == 0: return 0.5
    return wilson_score(confirmations, total)

def test_haversine_london_paris():
    dist = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < dist < 360, f"Expected ~340km, got {dist:.1f}"

def test_haversine_same_point():
    assert haversine_km(48.5, 31.2, 48.5, 31.2) == 0.0

def test_danger_critical():
    assert danger_score_to_level(0.95) == "critical"

def test_danger_high():
    assert danger_score_to_level(0.70) == "high"

def test_danger_medium():
    assert danger_score_to_level(0.50) == "medium"

def test_danger_low():
    assert danger_score_to_level(0.30) == "low"

def test_danger_safe():
    assert danger_score_to_level(0.05) == "safe"

def test_credibility_confirmations():
    score = calculate_credibility_score(10, 0)
    assert score > 0.7

def test_credibility_contradictions():
    score = calculate_credibility_score(0, 10)
    assert score < 0.3

def test_credibility_unknown():
    score = calculate_credibility_score(0, 0)
    assert score == 0.5

if __name__ == "__main__":
    tests = [
        test_haversine_london_paris, test_haversine_same_point,
        test_danger_critical, test_danger_high, test_danger_medium,
        test_danger_low, test_danger_safe,
        test_credibility_confirmations, test_credibility_contradictions, test_credibility_unknown,
    ]
    p = f = 0
    for t in tests:
        try:
            t(); print(f"  ✓ {t.__name__}"); p += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}"); f += 1
    print(f"\n{p} passed | {f} failed")
