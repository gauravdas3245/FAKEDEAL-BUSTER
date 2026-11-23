import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import { toNaiveIsoTimestamp, validateInspectionForm } from '../src/services/productValidation.js'

const catalog = {
  products: [{ title: 'Example Phone', category: 'Electronics', platforms: ['amazon'], brand: 'Acme', asin: 'A1' }],
  platforms: ['amazon'], categories: ['Electronics'], date_range: { start: '2023-01-01', end: '2024-12-30' },
}
const valid = {
  product_name: ' Example   Phone ', platform: 'amazon', category: 'Electronics', original_price: '239.02',
  current_price: '203.62', as_of: '2024-10-18T00:00', seller_name: '  Seller  ', seller_rating: '', product_url: '',
  historical_mode: true,
}
const now = new Date('2026-11-18T00:00:00')

describe('dataset-backed inspection form validation', () => {
  test('accepts valid required metadata and blank optional seller fields', () => {
    assert.deepEqual(validateInspectionForm(valid, catalog, now), {})
  })

  test('requires name, platform, category, both prices, and timestamp', () => {
    const errors = validateInspectionForm({ ...valid, product_name: ' ', platform: '', category: '', original_price: '', current_price: '', as_of: '' }, catalog, now)
    for (const field of ['product_name', 'platform', 'category', 'original_price', 'current_price', 'as_of']) assert.ok(errors[field])
  })

  test('ordinary current mode needs no user-entered timestamp', () => {
    assert.deepEqual(validateInspectionForm({ ...valid, historical_mode: false, as_of: '' }, catalog, now), {})
  })

  test('checks dataset-supported platform and name/category compatibility', () => {
    assert.ok(validateInspectionForm({ ...valid, platform: 'ebay' }, catalog, now).platform)
    assert.ok(validateInspectionForm({ ...valid, category: 'Toys' }, catalog, now).category)
  })

  test('accepts seller rating endpoints and decimals', () => {
    for (const rating of ['1.0', '5.0', '4.2', '4.8']) assert.equal(validateInspectionForm({ ...valid, seller_rating: rating }, catalog, now).seller_rating, undefined)
  })

  test('rejects seller rating zero, above five, negative and nonnumeric values', () => {
    for (const rating of ['0', '5.1', '-1', 'bad']) assert.ok(validateInspectionForm({ ...valid, seller_rating: rating }, catalog, now).seller_rating)
  })

  test('accepts HTTP and HTTPS URLs and rejects unsupported schemes', () => {
    for (const url of ['http://shop.example/p', 'https://shop.example/p']) assert.equal(validateInspectionForm({ ...valid, product_url: url }, catalog, now).product_url, undefined)
    for (const url of ['javascript:alert(1)', 'file:///tmp/x', 'data:text/plain,x', 'ftp://shop.example', 'bad']) assert.ok(validateInspectionForm({ ...valid, product_url: url }, catalog, now).product_url)
  })

  test('rejects zero, negative, nonnumeric, and inverted prices', () => {
    for (const original_price of ['0', '-1', 'no']) assert.ok(validateInspectionForm({ ...valid, original_price }, catalog, now).original_price)
    assert.ok(validateInspectionForm({ ...valid, current_price: '0' }, catalog, now).current_price)
    assert.ok(validateInspectionForm({ ...valid, current_price: 'not a price' }, catalog, now).current_price)
    assert.ok(validateInspectionForm({ ...valid, current_price: '250' }, catalog, now).current_price)
  })

  test('rejects impossible and future timestamps but permits historical timestamps', () => {
    assert.ok(validateInspectionForm({ ...valid, as_of: '2024-02-31T10:00' }, catalog, now).as_of)
    assert.ok(validateInspectionForm({ ...valid, as_of: '2026-11-19T00:00' }, catalog, now).as_of)
    assert.equal(validateInspectionForm(valid, catalog, now).as_of, undefined)
    assert.equal(toNaiveIsoTimestamp('2024-10-18T00:00'), '2024-10-18T00:00:00')
  })
})
