import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const DANGER_COLORS = {
  critical: '#ff2b2b',
  high: '#ff6600',
  medium: '#ffb800',
  low: '#00cc66',
  safe: '#0088ff',
}

function LocationMarker({ onLocationFound }) {
  const map = useMap()
  useEffect(() => {
    map.locate({ setView: true, maxZoom: 12 })
    map.on('locationfound', (e) => onLocationFound?.(e.latlng))
  }, [map, onLocationFound])
  return null
}

export default function Map({ reports = [], shelters = [], onLocationFound, center = [48.5, 31.2] }) {
  return (
    <MapContainer
      center={center}
      zoom={7}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
      />
      <LocationMarker onLocationFound={onLocationFound} />

      {reports.map((r) => (
        <CircleMarker
          key={r.id}
          center={[r.lat, r.lng]}
          radius={8}
          pathOptions={{
            color: DANGER_COLORS[r.danger_level] || '#888',
            fillColor: DANGER_COLORS[r.danger_level] || '#888',
            fillOpacity: 0.7,
            weight: 2,
          }}
        >
          <Popup>
            <div style={{ color: '#000', minWidth: 150 }}>
              <strong>{r.report_type?.replace(/_/g, ' ').toUpperCase()}</strong>
              <br />
              <span style={{ color: DANGER_COLORS[r.danger_level] }}>
                ⚠ {r.danger_level?.toUpperCase()}
              </span>
              {r.description && <p style={{ marginTop: 4 }}>{r.description}</p>}
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {shelters.map((s) => (
        <CircleMarker
          key={s.id}
          center={[s.lat, s.lng]}
          radius={10}
          pathOptions={{ color: '#00cc66', fillColor: '#00cc66', fillOpacity: 0.8, weight: 2 }}
        >
          <Popup>
            <div style={{ color: '#000', minWidth: 150 }}>
              <strong>🏠 {s.name}</strong>
              <br />
              <span>{s.shelter_type} — {s.status}</span>
              {s.capacity_total && <p>Capacity: {s.capacity_current ?? '?'}/{s.capacity_total}</p>}
              {s.operating_org && <p>Org: {s.operating_org}</p>}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
