# SafePassage — Data Sources

## NASA FIRMS

**Full name:** Fire Information for Resource Management System  
**Provider:** NASA EOSDIS  
**API:** REST, CSV/JSON output  
**Registration:** Free MAP_KEY at https://firms.modaps.eosdis.nasa.gov/api/map_key/  
**Update frequency:** Near real-time (~minutes after satellite pass)  
**Sensors:** VIIRS SNPP, VIIRS NOAA-20, VIIRS NOAA-21, MODIS  

**How SafePassage uses it:**  
Detects thermal anomalies (brightness temperature + Fire Radiative Power) within a geographic bounding box. In conflict zones, high FRP values often correspond to explosions, large fires from airstrikes, or burning infrastructure.

**Key fields:**
- `latitude`, `longitude` — detection location
- `bright_ti4` — brightness temperature (Kelvin)
- `frp` — Fire Radiative Power (megawatts)
- `confidence` — h (high), n (nominal), l (low)
- `acq_date`, `acq_time` — acquisition timestamp

**Supported conflict zones in SafePassage:**  
Ukraine, Gaza, Sudan, Syria, Yemen, Iran, Iraq, Lebanon, Myanmar, Somalia, Ethiopia

---

## ReliefWeb

**Provider:** UN OCHA  
**API:** REST v2  
**Registration:** Free, appname required  
**Update frequency:** Continuous  

**How SafePassage uses it:**  
Fetches recent humanitarian reports, crisis updates, and disaster alerts. Used as the primary source for structured humanitarian intelligence.

**Endpoints used:**
- `/reports` — crisis reports filtered by country/keyword
- `/disasters` — active disaster declarations

---

## GDELT

**Full name:** Global Database of Events, Language and Tone  
**Provider:** The GDELT Project  
**API:** REST, no registration required  
**Update frequency:** Every 15 minutes  
**Coverage:** 1979–present, 300+ event categories  

**How SafePassage uses it:**  
Queries the GEO API for conflict-related themes within a radius of a location. Tone scoring identifies strongly negative news (attacks, casualties, evacuations).

**Themes queried:** KILL, ATTACK, CONFLICT, PROTEST, EVACUATE, ARMED_CONFLICT, MILITARY, EXPLOSION, REFUGEE

**Limitations:**  
GDELT is media-derived, not field-verified. It reflects news coverage, not necessarily ground truth. Used as a signal, not as a primary source.

---

## UCDP

**Full name:** Uppsala Conflict Data Program  
**Provider:** Uppsala University, Sweden  
**API:** REST, no registration required  
**Dataset:** GED (Georeferenced Event Dataset) v25.1  
**Coverage:** 1989–2025  

**How SafePassage uses it:**  
Provides historical baseline of organised violence events with geocoding. Used to identify areas with known conflict history even when real-time sources show no current activity.

**Endpoint used:** `/api/gedevents` — filtered by bounding box and year range

**Limitations:**  
UCDP data has a multi-month lag. It is not suitable for real-time alerting but provides valuable historical context for the danger score.

---

## LibreTranslate

**Provider:** Self-hosted (open source)  
**Container:** `safepassage_translate` on port 5000  
**Languages:** en, ar, uk, fr, es, pt  

**How SafePassage uses it:**  
Translates civilian SOS messages to English for NGO/admin review. Translates AI responses back to the civilian's language. All translation happens server-side — no data is sent to third-party translation services.

---

## Anthropic Claude

**Model:** claude-sonnet-4  
**Used for:** AI-powered evacuation planning and risk assessment  

**Input:** Location, group composition, vehicle availability, medical needs, language preference  
**Output:** Risk level, evacuation plan, immediate actions, areas to avoid  

If the Anthropic API is unavailable, the system returns a safe fallback response without failing.