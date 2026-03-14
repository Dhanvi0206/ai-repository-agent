export function renderSafe(value) {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  if (typeof value === 'string' || typeof value === 'number') {
    return value
  }

  if (Array.isArray(value)) {
    return value.map((item) => renderSafe(item)).filter(Boolean).join(', ')
  }

  if (typeof value === 'object') {
    if (value.summary) {
      return renderSafe(value.summary)
    }

    if (value.label) {
      return renderSafe(value.label)
    }

    if (value.name) {
      return renderSafe(value.name)
    }

    return JSON.stringify(value)
  }

  return String(value)
}
