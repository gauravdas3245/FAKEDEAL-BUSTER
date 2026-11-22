export function normalizeText(value) {
  return String(value ?? '').trim().replace(/\s+/g, ' ').toLocaleLowerCase()
}

function isValidLocalDateTime(value) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return false
  const parsed = new Date(value)
  return !Number.isNaN(parsed.valueOf())
    && parsed.getFullYear() === Number(value.slice(0, 4))
    && parsed.getMonth() + 1 === Number(value.slice(5, 7))
    && parsed.getDate() === Number(value.slice(8, 10))
    && parsed.getHours() === Number(value.slice(11, 13))
    && parsed.getMinutes() === Number(value.slice(14, 16))
}

export function validateInspectionForm(form, catalog, now = new Date()) {
  const errors = {}
  const productName = String(form.product_name ?? '').trim().replace(/\s+/g, ' ')
  if (!productName) errors.product_name = 'Product Name is required.'
  else if (productName.length > 200) errors.product_name = 'Product Name must be 200 characters or fewer.'

  if (!form.platform) errors.platform = 'Please select a supported platform.'
  else if (catalog && !catalog.platforms?.includes(form.platform)) errors.platform = 'This platform is not available in the historical dataset.'
  if (!form.category) errors.category = 'Please select a category.'
  else if (catalog && !catalog.categories?.some((item) => normalizeText(item) === normalizeText(form.category))) errors.category = 'This category is not available in the historical dataset.'
  else if (catalog?.category_platforms?.length && form.platform && !catalog.category_platforms.some((pair) => normalizeText(pair.category) === normalizeText(form.category) && normalizeText(pair.platform) === normalizeText(form.platform))) errors.category = 'This category is not available on the selected platform.'

  for (const field of ['original_price', 'current_price']) {
    const raw = String(form[field] ?? '').trim()
    const value = Number(raw)
    if (!raw) errors[field] = `${field === 'original_price' ? 'Original' : 'Current'} Price is required.`
    else if (!Number.isFinite(value) || value <= 0) errors[field] = 'Price must be a positive number greater than zero.'
  }
  const original = Number(form.original_price)
  const current = Number(form.current_price)
  if (!errors.original_price && !errors.current_price && current > original) errors.current_price = 'Current Price cannot exceed Original Price.'

  const rawDate = String(form.as_of ?? '').trim()
  const selected = rawDate ? new Date(rawDate) : null
  if (form.historical_mode && !rawDate) errors.as_of = 'Price Checked On is required for historical analysis.'
  else if (form.historical_mode && (!selected || Number.isNaN(selected.valueOf()) || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/.test(rawDate)
    || selected.getFullYear() !== Number(rawDate.slice(0, 4))
    || selected.getMonth() + 1 !== Number(rawDate.slice(5, 7))
    || selected.getDate() !== Number(rawDate.slice(8, 10))
    || selected.getHours() !== Number(rawDate.slice(11, 13))
    || selected.getMinutes() !== Number(rawDate.slice(14, 16)))) errors.as_of = 'Enter a valid date and time.'
  else if (form.historical_mode && selected > now) errors.as_of = 'Future dates are not supported.'

  const sellerName = String(form.seller_name ?? '').trim()
  if (sellerName.length > 120) errors.seller_name = 'Seller Name must be 120 characters or fewer.'
  const ratingText = String(form.seller_rating ?? '').trim()
  if (ratingText) {
    const rating = Number(ratingText)
    if (!Number.isFinite(rating) || rating < 1 || rating > 5) errors.seller_rating = 'Seller Rating must be a number from 1.0 through 5.0.'
  }
  const urlText = String(form.product_url ?? '').trim()
  if (urlText) {
    try {
      const url = new URL(urlText)
      if (!['http:', 'https:'].includes(url.protocol) || !url.hostname) throw new Error('unsupported')
    } catch {
      errors.product_url = 'Enter a valid HTTP or HTTPS URL.'
    }
  }
  return errors
}

export function toNaiveIsoTimestamp(value) {
  if (!value || !isValidLocalDateTime(value)) throw new Error('Price Checked On must be a valid local date and time.')
  return `${value}:00`
}
