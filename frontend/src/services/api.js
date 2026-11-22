/** API client for the implemented FastAPI contract. */

const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/+$/, '')

async function requestJson(path, init) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch (error) {
    throw new ApiError('Could not connect to the analysis service. Check that the backend is running.', 0, 'NETWORK_FAILURE', error?.message)
  }
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    throw new ApiError(`The server returned a non-JSON response (HTTP ${response.status}).`, response.status, 'NON_JSON_RESPONSE')
  }
  let data
  try {
    data = await response.json()
  } catch (error) {
    throw new ApiError(`The server returned invalid JSON (HTTP ${response.status}).`, response.status, 'INVALID_JSON', error?.message)
  }
  if (!response.ok || data?.success === false) {
    throw new ApiError(data?.error?.message || 'The analysis request failed.', response.status, data?.error?.code || `HTTP_${response.status}`, data)
  }
  return data
}

export async function loadProductCatalog() {
  return requestJson('/api/catalog', { headers: { Accept: 'application/json' } })
}

export async function loadCatalogMetadata() {
  return requestJson('/api/catalog/metadata', { headers: { Accept: 'application/json' } })
}

export async function loadSyntheticModelComparison() {
  return requestJson('/api/models/synthetic-comparison', { headers: { Accept: 'application/json' } })
}

export async function searchCatalogProducts({ q = '', category = '', platform = '', limit = 20 } = {}) {
  const params = new URLSearchParams({ q, category, platform, limit: String(limit) })
  const data = await requestJson(`/api/catalog/search?${params}`, { headers: { Accept: 'application/json' } })
  return data.products || []
}

export async function inspectListing(form) {
  const payload = {
    product_name: String(form.product_name ?? '').trim(),
    platform: String(form.platform ?? '').trim().toLowerCase(),
    category: String(form.category ?? '').trim(),
    current_price: Number(form.current_price),
    original_price: Number(form.original_price),
    seller_name: String(form.seller_name ?? '').trim() || null,
    seller_rating: String(form.seller_rating ?? '').trim() ? Number(form.seller_rating) : null,
    product_url: String(form.product_url ?? '').trim() || null,
  }
  if (form.as_of) payload.as_of = normalizeIsoTimestamp(form.as_of)
  if (form.selected_product_id) payload.selected_product_id = form.selected_product_id
  return requestJson('/api/inspect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  })
}

export class ApiError extends Error {
  constructor(message, status = 0, code = 'UNKNOWN_ERROR', details = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export function normalizeIsoTimestamp(dateInput) {
  if (!dateInput) return new Date().toISOString()
  if (dateInput instanceof Date) return dateInput.toISOString()
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(dateInput)) return `${dateInput}:00`
  return String(dateInput)
}

export async function analyzeProduct({ product_id, platform, as_of, current_price, original_price }) {
  const requestPayload = {
    product_id: String(product_id ?? '').trim(),
    platform: String(platform ?? '').trim().toLowerCase(),
    as_of: normalizeIsoTimestamp(as_of),
    current_price: Number(current_price),
    original_price: Number(original_price)
  }

  if (!requestPayload.product_id) throw new ApiError('Product ID is required.', 400, 'CLIENT_VALIDATION_ERROR')
  if (!requestPayload.platform) throw new ApiError('Platform is required.', 400, 'CLIENT_VALIDATION_ERROR')
  if (!as_of) throw new ApiError('Observation timestamp (as_of) is required.', 400, 'CLIENT_VALIDATION_ERROR')
  if (!Number.isFinite(requestPayload.current_price) || requestPayload.current_price <= 0) {
    throw new ApiError('Current price must be a positive finite number.', 400, 'CLIENT_VALIDATION_ERROR')
  }
  if (!Number.isFinite(requestPayload.original_price) || requestPayload.original_price <= 0) {
    throw new ApiError('Original price must be a positive finite number.', 400, 'CLIENT_VALIDATION_ERROR')
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(requestPayload)
    })
  } catch (error) {
    throw new ApiError('Could not connect to the analysis service. Check that the backend is running.', 0, 'NETWORK_FAILURE', error?.message)
  }

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    const body = await response.text()
    throw new ApiError(`The server returned a non-JSON response (HTTP ${response.status}).`, response.status, 'NON_JSON_RESPONSE', body)
  }

  let data
  try {
    data = await response.json()
  } catch (error) {
    throw new ApiError(`The server returned invalid JSON (HTTP ${response.status}).`, response.status, 'INVALID_JSON', error?.message)
  }

  if (!response.ok || data?.success === false) {
    const code = data?.error?.code || `HTTP_${response.status}`
    const message = data?.error?.message || 'The analysis request failed.'
    throw new ApiError(message, response.status, code, data)
  }

  return data
}
