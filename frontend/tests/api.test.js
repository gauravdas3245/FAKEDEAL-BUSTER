import { test, describe, beforeEach, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { analyzeProduct, inspectListing, searchCatalogProducts, loadCatalogMetadata, loadSyntheticModelComparison, ApiError } from '../src/services/api.js'
import { getFdiState, getMlState, getSyntheticClassifierState, getAssessmentVerdict } from '../src/services/presentation.js'

const request = {
  product_id: 'P0000001',
  platform: 'Amazon',
  as_of: '2024-10-18T00:00:00',
  current_price: '203.62',
  original_price: '239.02',
  category: 'ignored input',
  product_name: 'ignored input'
}

const actualContractResponse = {
  success: true,
  analysis_status: 'OK',
  verdict: null,
  fdi_score: null,
  confidence: null,
  explanation: 'Anomaly is not proof of fraud. FDI score and risk level are unavailable because required FDI inputs are missing.',
  original_price: 239.02,
  current_price: 203.62,
  discount_percentage: 14.81,
  forecast_status: 'UNAVAILABLE',
  forecast: null,
  ml_anomaly: {
    status: 'OK',
    product_id: 'P0000001',
    platform: 'amazon',
    timestamp: '2024-10-18 00:00:00',
    verdict: 'NO_ANOMALY',
    anomaly_score: -0.15759093500478655,
    is_anomaly: false,
    features: {
      msrp_to_30d_avg: 1.3546942746757602,
      ratio_to_30d_avg: 1.154057602750725,
      price_volatility_30d: 0.1116823092336447,
      recent_7d_surge: 0.18812049535720693
    },
    explanation: { model_result: 'Isolation Forest did not flag an unusual feature combination.' },
    model_version: 'isolation_forest_v1'
  },
  fdi: {
    status: 'INSUFFICIENT_INPUTS',
    fdi_score: null,
    provisional_level: null,
    component_scores: { S_gap: 60.43247277171642, S_mean_ratio: 100, S_msrp_inflation: 100, S_anomaly: null },
    component_weights: { S_gap: 0.35, S_mean_ratio: 0.3, S_msrp_inflation: 0.2, S_anomaly: 0.15 },
    missing_inputs: ['price_spike_flag', 'pre_discount_hike_ratio'],
    explanation: { summary: 'FDI total unavailable because required pricing signals are missing.' },
    methodology_version: 'fdi_provisional_v1',
    validation_status: 'PROVISIONAL_NOT_VALIDATED'
  }
}

function response(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => body
  }
}

describe('API client and actual backend response mapping', () => {
  let originalFetch

  beforeEach(() => { originalFetch = globalThis.fetch })
  afterEach(() => { globalThis.fetch = originalFetch })

  test('loads filter metadata and searches bounded catalogue suggestions with active filters', async () => {
    const calls = []
    globalThis.fetch = async (url) => {
      calls.push(String(url))
      return response(200, calls.length === 1
        ? { platforms: ['amazon'], categories: ['Electronics'], category_platforms: [{ category: 'Electronics', platform: 'amazon' }] }
        : { products: [{ title: 'Example Phone', brand: 'Acme', platform: 'amazon', category: 'Electronics' }] })
    }
    const metadata = await loadCatalogMetadata()
    const products = await searchCatalogProducts({ q: 'acme', category: 'Electronics', platform: 'amazon', limit: 20 })
    assert.deepEqual(metadata.platforms, ['amazon'])
    assert.equal(products[0].brand, 'Acme')
    assert.match(calls[0], /\/api\/catalog\/metadata$/)
    assert.match(calls[1], /q=acme/)
    assert.match(calls[1], /category=Electronics/)
    assert.match(calls[1], /platform=amazon/)
    assert.match(calls[1], /limit=20/)
  })

  test('sends exactly five approved fields with normalized values', async () => {
    let target, options
    globalThis.fetch = async (url, init) => {
      target = url
      options = init
      return response(200, actualContractResponse)
    }
    await analyzeProduct(request)
    assert.equal(target, '/api/analyze')
    assert.equal(options.method, 'POST')
    assert.deepEqual(Object.keys(JSON.parse(options.body)).sort(), [
      'as_of', 'current_price', 'original_price', 'platform', 'product_id'
    ])
    assert.deepEqual(JSON.parse(options.body), {
      product_id: 'P0000001', platform: 'amazon', as_of: '2024-10-18T00:00:00',
      current_price: 203.62, original_price: 239.02
    })
  })

  test('user listing adapter sends user metadata but no product ID', async () => {
    let target, payload
    globalThis.fetch = async (url, init) => {
      target = url
      payload = JSON.parse(init.body)
      return response(200, { status: 'ANALYZED', analysis: actualContractResponse })
    }
    await inspectListing({ product_name: ' Example Phone ', platform: 'amazon', category: 'Electronics', as_of: '2024-10-18T00:00', original_price: '239.02', current_price: '203.62', seller_name: ' Seller ', seller_rating: '4.8', product_url: 'https://shop.example/item' })
    assert.equal(target, '/api/inspect')
    assert.deepEqual(payload, {
      product_name: 'Example Phone', platform: 'amazon', category: 'Electronics', as_of: '2024-10-18T00:00:00',
      original_price: 239.02, current_price: 203.62, seller_name: 'Seller', seller_rating: 4.8,
      product_url: 'https://shop.example/item',
    })
    assert.equal('product_id' in payload, false)
  })

  test('user listing adapter preserves product, history, validation, and model errors', async () => {
    for (const [status, code] of [[404, 'PRODUCT_NOT_FOUND'], [409, 'HISTORY_CONFLICT'], [422, 'VALIDATION_ERROR'], [503, 'ML_SERVICE_UNAVAILABLE']]) {
      globalThis.fetch = async () => response(status, { success: false, error: { code, message: `Actual ${code} message.` } })
      await assert.rejects(() => inspectListing({ product_name: 'Phone' }), (error) => error instanceof ApiError && error.status === status && error.code === code)
    }
    globalThis.fetch = async () => { throw new TypeError('connection refused') }
    await assert.rejects(() => inspectListing({ product_name: 'Phone' }), (error) => error instanceof ApiError && error.code === 'NETWORK_FAILURE')
  })

  test('returns the real response shape including distinct ML and FDI objects', async () => {
    globalThis.fetch = async () => response(200, actualContractResponse)
    const result = await analyzeProduct(request)
    assert.equal(result.ml_anomaly.verdict, 'NO_ANOMALY')
    assert.equal(result.ml_anomaly.anomaly_score, -0.15759093500478655)
    assert.equal(result.fdi.status, 'INSUFFICIENT_INPUTS')
  })

  test('shows FDI unavailable without a fabricated zero, risk level, or confidence', () => {
    const fdi = getFdiState(actualContractResponse.fdi)
    assert.equal(fdi.kind, 'insufficient-inputs')
    assert.match(fdi.label, /FDI unavailable/)
    assert.equal('score' in fdi, false)
    assert.equal(actualContractResponse.confidence, null)
    assert.equal(actualContractResponse.verdict, null)
  })

  test('shows insufficient history with no fabricated ML or FDI score', () => {
    const needsMoreData = {
      analysis_status: 'NEEDS_MORE_DATA',
      verdict: null,
      fdi_score: null,
      confidence: null,
      ml_anomaly: { status: 'NEEDS_MORE_DATA', verdict: null, anomaly_score: null, is_anomaly: null, features: null },
      fdi: { status: 'INSUFFICIENT_INPUTS', fdi_score: null }
    }
    assert.equal(getMlState(needsMoreData).label, 'Insufficient historical data')
    assert.equal(getFdiState(needsMoreData.fdi).kind, 'insufficient-inputs')
    assert.equal(needsMoreData.ml_anomaly.anomaly_score, null)
    assert.equal(needsMoreData.fdi.fdi_score, null)
  })

  test('maps synthetic classifier output as scenario resemblance, never fraud probability', () => {
    const state = getSyntheticClassifierState({ synthetic_classifier: {
      status: 'SYNTHETIC_SCENARIO_EXPERIMENT',
      predicted_scenario: 'SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT',
      synthetic_scenario_score: 0.87,
      disclaimer: 'Generated scenarios only; not a real fraud prediction.',
    } })
    assert.match(state.label, /generated artificial-inflation scenario/)
    assert.match(state.disclaimer, /not a real fraud prediction/)
    assert.equal('confidence' in state, false)
  })

  test('correctly maps the three distinguished assessment verdict states', () => {
    // State 1: Potential Suspicious Discount Pattern
    const suspicious = getAssessmentVerdict({
      analysis_status: 'OK',
      ml_anomaly: { status: 'OK', verdict: 'ANOMALY' },
      assessment_verdict: 'Potential Suspicious Discount Pattern',
    })
    assert.equal(suspicious.state, 'Potential Suspicious Discount Pattern')
    assert.equal(suspicious.badgeClass, 'anomaly')
    assert.match(suspicious.description, /statistical abnormality, not confirmed fraud/)

    // State 2: No Suspicious Pattern Detected
    const normal = getAssessmentVerdict({
      analysis_status: 'OK',
      ml_anomaly: { status: 'OK', verdict: 'NO_ANOMALY' },
      assessment_verdict: 'No Suspicious Pattern Detected',
    })
    assert.equal(normal.state, 'No Suspicious Pattern Detected')
    assert.equal(normal.badgeClass, 'normal')

    // State 3: Insufficient Evidence
    const insufficient = getAssessmentVerdict({
      analysis_status: 'NEEDS_MORE_DATA',
      ml_anomaly: { status: 'NEEDS_MORE_DATA', verdict: null },
      assessment_verdict: 'Insufficient Evidence',
    })
    assert.equal(insufficient.state, 'Insufficient Evidence')
    assert.equal(insufficient.badgeClass, 'inconclusive')
    assert.match(insufficient.description, /Insufficient historical price observations/)
  })

  test('loads synthetic model comparison metrics from backend', async () => {
    globalThis.fetch = async (url) => {
      assert.match(String(url), /\/api\/models\/synthetic-comparison$/)
      return response(200, {
        status: 'AVAILABLE',
        evaluation_scope: 'SYNTHETIC_HELD_OUT_TEST_ONLY',
        selected_model: 'random_forest',
        test_metrics: {
          logistic_regression: { roc_auc: 0.8891 },
          random_forest: { roc_auc: 0.9160 }
        }
      })
    }
    const comparison = await loadSyntheticModelComparison()
    assert.equal(comparison.status, 'AVAILABLE')
    assert.equal(comparison.selected_model, 'random_forest')
    assert.equal(comparison.test_metrics.random_forest.roc_auc, 0.9160)
  })

  for (const [status, code] of [[422, 'VALIDATION_ERROR'], [409, 'HISTORY_CONFLICT'], [503, 'ML_SERVICE_UNAVAILABLE']]) {
    test(`preserves HTTP ${status} ${code} response`, async () => {
      globalThis.fetch = async () => response(status, {
        success: false, error: { code, message: `Actual ${code} message.` }
      })
      await assert.rejects(() => analyzeProduct(request), (error) => {
        assert.ok(error instanceof ApiError)
        assert.equal(error.status, status)
        assert.equal(error.code, code)
        assert.equal(error.message, `Actual ${code} message.`)
        return true
      })
    })
  }

  test('reports network failure in a clear error state', async () => {
    globalThis.fetch = async () => { throw new TypeError('connection refused') }
    await assert.rejects(() => analyzeProduct(request), (error) => {
      assert.equal(error.status, 0)
      assert.equal(error.code, 'NETWORK_FAILURE')
      assert.match(error.message, /Check that the backend is running/)
      return true
    })
  })
})
