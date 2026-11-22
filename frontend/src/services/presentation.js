export function getAssessmentVerdict(analysis) {
  if (!analysis) {
    return {
      state: 'Insufficient Evidence',
      kind: 'insufficient',
      label: 'Insufficient Evidence',
      badgeClass: 'inconclusive',
      description: 'No analysis data available to evaluate pricing patterns.'
    }
  }

  const serverVerdict = analysis.assessment_verdict
  const anomaly = analysis.ml_anomaly

  if (analysis.analysis_status === 'NEEDS_MORE_DATA' || anomaly?.status === 'NEEDS_MORE_DATA') {
    return {
      state: 'Insufficient Evidence',
      kind: 'insufficient',
      label: 'Insufficient Evidence',
      badgeClass: 'inconclusive',
      description: analysis.assessment_explanation || 'Insufficient historical price observations (at least 14 days required) exist to establish a reliable baseline.'
    }
  }

  if (serverVerdict === 'Potential Suspicious Discount Pattern' || anomaly?.verdict === 'ANOMALY') {
    return {
      state: 'Potential Suspicious Discount Pattern',
      kind: 'suspicious',
      label: 'Potential Suspicious Discount Pattern',
      badgeClass: 'anomaly',
      description: analysis.assessment_explanation || 'The Isolation Forest model detected an unusual price/discount pattern relative to historical baseline. This is an assessment of statistical abnormality, not confirmed fraud.'
    }
  }

  if (serverVerdict === 'No Suspicious Pattern Detected' || anomaly?.verdict === 'NO_ANOMALY') {
    return {
      state: 'No Suspicious Pattern Detected',
      kind: 'normal',
      label: 'No Suspicious Pattern Detected',
      badgeClass: 'normal',
      description: analysis.assessment_explanation || 'Current price and discount conform to normal historical patterns observed for this product within normal variance.'
    }
  }

  return {
    state: 'Insufficient Evidence',
    kind: 'insufficient',
    label: 'Insufficient Evidence',
    badgeClass: 'inconclusive',
    description: analysis.assessment_explanation || 'Model or data inputs were insufficient to produce an assessment.'
  }
}

export function canSubmit(isLoading, submissionInProgress = false) {
  return !isLoading && !submissionInProgress
}

export function getSubmitButtonLabel(isLoading) {
  return isLoading ? 'Analysing prices…' : 'Analyse Product'
}

export function getMlState(result) {
  const anomaly = result?.ml_anomaly
  if (result?.analysis_status === 'NEEDS_MORE_DATA' || anomaly?.status === 'NEEDS_MORE_DATA') {
    return { kind: 'needs-more-data', label: 'Insufficient historical data' }
  }
  if (anomaly?.status !== 'OK') return { kind: 'unavailable', label: 'ML result unavailable' }
  if (anomaly.verdict === 'ANOMALY') return { kind: 'anomaly', label: 'Price anomaly detected' }
  if (anomaly.verdict === 'NO_ANOMALY') return { kind: 'no-anomaly', label: 'No price anomaly detected' }
  return { kind: 'unavailable', label: 'ML result unavailable' }
}

export function getFdiState(fdi) {
  if (fdi?.status === 'INSUFFICIENT_INPUTS') {
    return {
      kind: 'insufficient-inputs',
      label: 'FDI unavailable due to insufficient inputs',
      message: fdi.explanation?.summary || 'Required FDI inputs are unavailable.'
    }
  }
  if (fdi?.status === 'OK' && Number.isFinite(fdi.fdi_score)) {
    return { kind: 'available', label: 'FDI score', score: fdi.fdi_score, level: fdi.provisional_level }
  }
  return { kind: 'unavailable', label: 'FDI unavailable', message: fdi?.explanation?.summary || 'FDI result unavailable.' }
}

export function getSyntheticClassifierState(result) {
  const output = result?.synthetic_classifier
  if (output?.status === 'SYNTHETIC_SCENARIO_EXPERIMENT') {
    const label = output.predicted_scenario === 'SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT'
      ? 'Resembles the generated artificial-inflation scenario'
      : output.predicted_scenario === 'SYNTHETIC_GENUINE_DISCOUNT'
        ? 'Resembles the generated genuine-discount scenario'
        : 'Scenario result unavailable'
    return { kind: 'scenario', label, score: output.synthetic_scenario_score, disclaimer: output.disclaimer }
  }
  if (output?.status === 'NEEDS_MORE_DATA') return { kind: 'insufficient', label: 'Insufficient history for synthetic scenario comparison', message: output.message }
  return { kind: 'unavailable', label: 'Synthetic scenario comparison unavailable', message: output?.message || 'No synthetic classifier result was produced.' }
}
