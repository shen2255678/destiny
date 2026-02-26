// Usage example:
// import { BirthInput, BirthData } from '@/components/BirthInput'
//
// const [personA, setPersonA] = useState<BirthData>({
//   name: '',
//   birth_date: '',
//   birth_time: '',
//   lat: 25.033,
//   lng: 121.565,
//   data_tier: 3,
//   gender: 'M',
// })
//
// <BirthInput label="A" value={personA} onChange={setPersonA} />

'use client'

import { useState } from 'react'

// ---------------------------------------------------------------------------
// TypeScript interfaces
// ---------------------------------------------------------------------------

export interface BirthData {
  name: string
  birth_date: string   // "YYYY-MM-DD"
  birth_time: string   // "HH:MM" or "" if unknown
  lat: number
  lng: number
  data_tier: 1 | 2 | 3
  gender: 'M' | 'F'
}

interface BirthInputProps {
  label: 'A' | 'B'
  value: BirthData
  onChange: (v: BirthData) => void
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.3)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.5)',
  boxShadow: '0 8px 32px rgba(217,134,149,0.1)',
  borderRadius: '20px',
  padding: '24px 22px',
  width: '100%',
}

const baseInputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  background: 'rgba(255,255,255,0.5)',
  border: '1px solid rgba(255,255,255,0.6)',
  borderRadius: '12px',
  color: '#5c4059',
  fontSize: '13px',
  outline: 'none',
  marginBottom: '10px',
  backdropFilter: 'blur(4px)',
  WebkitBackdropFilter: 'blur(4px)',
  boxSizing: 'border-box',
}

const focusedInputStyle: React.CSSProperties = {
  ...baseInputStyle,
  border: '1px solid rgba(217,134,149,0.5)',
  boxShadow: '0 0 0 3px rgba(217,134,149,0.15)',
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '11px',
  fontWeight: 700,
  letterSpacing: '0.10em',
  color: '#8c7089',
  textTransform: 'uppercase' as const,
  marginBottom: '4px',
}

const noteMicroStyle: React.CSSProperties = {
  fontSize: '10px',
  color: '#8c7089',
  marginTop: '-8px',
  marginBottom: '10px',
  letterSpacing: '0.02em',
}

const tierBadgeStyle: React.CSSProperties = {
  display: 'inline-block',
  padding: '2px 8px',
  borderRadius: '999px',
  fontSize: '11px',
  fontWeight: 600,
  background: 'rgba(217,134,149,0.14)',
  color: '#d98695',
  border: '1px solid rgba(217,134,149,0.35)',
  marginLeft: '6px',
}

// ---------------------------------------------------------------------------
// Small controlled input — handles its own focus ring state
// ---------------------------------------------------------------------------

function Field({
  label,
  note,
  children,
}: {
  label: string
  note?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <span style={labelStyle}>{label}</span>
      {children}
      {note && <p style={noteMicroStyle}>{note}</p>}
    </div>
  )
}

function TextInput({
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
}) {
  const [focused, setFocused] = useState(false)
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={focused ? focusedInputStyle : baseInputStyle}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  )
}

function NumberInput({
  value,
  onChange,
  step = 'any',
  placeholder,
}: {
  value: number
  onChange: (v: number) => void
  step?: string
  placeholder?: string
}) {
  const [focused, setFocused] = useState(false)
  return (
    <input
      type="number"
      value={value}
      step={step}
      onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      placeholder={placeholder}
      style={focused ? focusedInputStyle : baseInputStyle}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  )
}

function SelectInput({
  value,
  onChange,
  options,
}: {
  value: string | number
  onChange: (v: string) => void
  options: { label: string; value: string | number }[]
}) {
  const [focused, setFocused] = useState(false)
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ ...(focused ? focusedInputStyle : baseInputStyle), cursor: 'pointer' }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

// ---------------------------------------------------------------------------
// Tier label helper
// ---------------------------------------------------------------------------

function tierLabel(tier: 1 | 2 | 3): string {
  if (tier === 1) return 'Gold — 精確時間'
  if (tier === 2) return 'Silver — 約略時間'
  return 'Bronze — 僅日期'
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * BirthInput — Controlled form card for a single person's birth data.
 *
 * Props:
 *   label   — 'A' or 'B'; displayed as PERSON A / PERSON B
 *   value   — BirthData object (controlled)
 *   onChange — Called with the updated BirthData on every field change
 *
 * Auto-behaviour:
 *   - Clearing birth_time forces data_tier to 3 (Bronze)
 *   - Default coordinates preset to Taipei (25.033, 121.565)
 */
export function BirthInput({ label, value, onChange }: BirthInputProps) {
  // Generic single-field updater
  const update = <K extends keyof BirthData>(key: K, val: BirthData[K]) =>
    onChange({ ...value, [key]: val })

  // Birth time change: auto-demote tier to 3 when cleared
  const handleTimeChange = (t: string) => {
    onChange({
      ...value,
      birth_time: t,
      data_tier: t ? value.data_tier : 3,
    })
  }

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <div
          style={{
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.18em',
            color: '#c0828e',
            textTransform: 'uppercase',
            marginBottom: '2px',
          }}
        >
          PERSON {label}
        </div>
        <div
          style={{
            height: '2px',
            borderRadius: '1px',
            background: 'linear-gradient(90deg, #d98695, transparent)',
          }}
        />
      </div>

      {/* 1. Name */}
      <Field label="顯示名稱">
        <TextInput
          value={value.name}
          onChange={(v) => update('name', v)}
          placeholder="暱稱或姓名"
        />
      </Field>

      {/* 2. Birth date */}
      <Field label="出生日期">
        <TextInput
          type="date"
          value={value.birth_date}
          onChange={(v) => update('birth_date', v)}
        />
      </Field>

      {/* 3. Birth time */}
      <Field label="出生時間" note="留空 = Tier 3（僅日期，Bronze 精度）">
        <TextInput
          type="time"
          value={value.birth_time}
          onChange={handleTimeChange}
        />
      </Field>

      {/* 4. Lat / Lng grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '10px',
        }}
      >
        <Field label="緯度 (Lat)">
          <NumberInput
            value={value.lat}
            onChange={(v) => update('lat', v)}
            step="0.001"
            placeholder="25.033"
          />
        </Field>
        <Field label="經度 (Lng)">
          <NumberInput
            value={value.lng}
            onChange={(v) => update('lng', v)}
            step="0.001"
            placeholder="121.565"
          />
        </Field>
      </div>

      {/* 5. Data tier select — with current tier badge */}
      <Field label="精確度 Tier">
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <span style={tierBadgeStyle}>Tier {value.data_tier}</span>
        </div>
        <SelectInput
          value={value.data_tier}
          onChange={(v) => update('data_tier', Number(v) as 1 | 2 | 3)}
          options={[
            { label: 'Tier 1 — Gold（精確時間）', value: 1 },
            { label: 'Tier 2 — Silver（約略時間）', value: 2 },
            { label: 'Tier 3 — Bronze（僅日期）', value: 3 },
          ]}
        />
        <p style={noteMicroStyle}>
          {value.birth_time === '' ? '已清除時間，自動設為 Tier 3' : tierLabel(value.data_tier)}
        </p>
      </Field>

      {/* 6. Gender select */}
      <Field label="性別">
        <SelectInput
          value={value.gender}
          onChange={(v) => update('gender', v as 'M' | 'F')}
          options={[
            { label: '男 (M)', value: 'M' },
            { label: '女 (F)', value: 'F' },
          ]}
        />
      </Field>
    </div>
  )
}

export default BirthInput
