import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import { normalizeIsoTimestamp } from '../src/services/api.js'
import { canSubmit, getSubmitButtonLabel } from '../src/services/presentation.js'
import { toNaiveIsoTimestamp, validateInspectionForm } from '../src/services/productValidation.js'

const catalog = { products: [], platforms: ['amazon'], categories: ['Electronics'] }
const validForm = { product_name: 'Phone', platform: 'amazon', category: 'Electronics', as_of: '2024-10-18T00:00', historical_mode: true, original_price: '239.02', current_price: '203.62', seller_name: '', seller_rating: '', product_url: '' }

describe('Product Inspector validation and submission behavior', () => {
  test('loading state is announced on the submit button', () => {
    assert.equal(getSubmitButtonLabel(true), 'Analysing prices…')
    assert.equal(getSubmitButtonLabel(false), 'Analyse Product')
  })

  test('requires product name, platform, category and prices; selected historical mode requires checked date', () => {
    const errors = validateInspectionForm({ ...validForm, product_name: '', platform: '', category: '', as_of: '', current_price: '', original_price: '' }, catalog, new Date('2026-11-18T00:00:00'))
    for (const field of ['product_name', 'platform', 'category', 'as_of', 'current_price', 'original_price']) assert.ok(errors[field])
  })

  test('does not require manual date in ordinary current analysis mode', () => {
    assert.deepEqual(validateInspectionForm({ ...validForm, historical_mode: false, as_of: '' }, catalog, new Date('2026-11-18T00:00:00')), {})
  })

  test('does not require optional seller metadata', () => {
    assert.deepEqual(validateInspectionForm(validForm, catalog, new Date('2026-11-18T00:00:00')), {})
  })

  test('prevents duplicate submissions while loading and permits retry after completion', () => {
    let loading = false
    let submitting = false
    let requests = 0
    const submit = () => { if (canSubmit(loading, submitting)) { submitting = true; loading = true; requests += 1 } }
    submit(); submit()
    assert.equal(requests, 1)
    assert.equal(canSubmit(loading, submitting), false)
    submitting = false; loading = false; submit()
    assert.equal(requests, 2)
  })

  test('normalizes ISO timestamp values and sends the selected date/time without shifting it', () => {
    assert.equal(normalizeIsoTimestamp('2024-10-18T00:00'), '2024-10-18T00:00:00')
    assert.equal(normalizeIsoTimestamp('2024-10-18T00:00:15'), '2024-10-18T00:00:15')
    assert.equal(toNaiveIsoTimestamp('2024-10-18T00:00'), '2024-10-18T00:00:00')
    assert.throws(() => toNaiveIsoTimestamp('2024-02-31T10:00'))
  })
})
