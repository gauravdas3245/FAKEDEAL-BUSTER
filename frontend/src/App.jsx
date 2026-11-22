import { useEffect, useRef, useState } from 'react'
import './App.css'
import { inspectListing, loadCatalogMetadata, loadSyntheticModelComparison, searchCatalogProducts } from './services/api'
import { canSubmit, getAssessmentVerdict, getFdiState, getMlState, getSyntheticClassifierState } from './services/presentation'
import { toNaiveIsoTimestamp, validateInspectionForm } from './services/productValidation'


/**
 * Helper to produce default observation timestamp in YYYY-MM-DDTHH:mm format
 */
function getDefaultAsOf() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/**
 * Reusable ForecastChart Component
 * Strictly renders forecast ONLY when genuine backend forecast data is returned.
 * Never creates fake or synthetic forecast values.
 */
export const ForecastChart = ({ data, status = 'INSUFFICIENT_HISTORY' }) => {
  const points = Array.isArray(data?.points)
    ? data.points
    : Array.isArray(data)
    ? data
    : []

  const forecastStatus = data?.status || status
  const hasGenuineData = forecastStatus === 'AVAILABLE' && points.length === 14

  if (!hasGenuineData) {
    return (
      <div className="forecast-empty">
        <div className="forecast-empty-icon" aria-hidden="true">📈</div>
        <h4 className="forecast-empty-title">Price Forecast Unavailable</h4>
        <p className="forecast-message">
          {data?.message || `A 14-day forecast is unavailable (status: ${forecastStatus}).`}
        </p>
      </div>
    )
  }

  // Calculate coordinates for genuine SVG forecast curve
  const prices = points.map((p) => p.predicted_price ?? p.price ?? 0)
  const minPrice = Math.min(...prices) * 0.95
  const maxPrice = Math.max(...prices) * 1.05
  const width = 600
  const height = 240
  const padding = 40

  const getX = (index) => padding + (index / (points.length - 1)) * (width - padding * 2)
  const getY = (val) => height - padding - ((val - minPrice) / (maxPrice - minPrice || 1)) * (height - padding * 2)

  const linePoints = points.map((p, i) => `${getX(i)},${getY(p.predicted_price ?? p.price ?? 0)}`).join(' ')
  const areaPoints = `${getX(0)},${height - padding} ${linePoints} ${getX(points.length - 1)},${height - padding}`

  return (
    <div className="forecast-chart-wrapper">
      <svg className="forecast-chart-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label={`14-day forecast from the ${data?.method || 'selected baseline'} method`}>
        <defs>
          <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#059669" stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <polygon points={areaPoints} fill="url(#forecastFill)" />
        <polyline fill="none" stroke="#059669" strokeWidth="2.5" strokeDasharray="5 3" points={linePoints} strokeLinecap="round" strokeLinejoin="round" />
        {points.map((p, i) => {
          const val = p.predicted_price ?? p.price ?? 0
          return (
            <circle key={i} cx={getX(i)} cy={getY(val)} r="4" fill="#ffffff" stroke="#047857" strokeWidth="2.5">
              <title>{p.date}: predicted {Number(val).toFixed(2)}</title>
            </circle>
          )
        })}
      </svg>
      <div className="chart-axis-labels"><span>{points[0].date}</span><span>Predicted prices (baseline)</span><span>{points[points.length - 1].date}</span></div>
    </div>
  )
}

function ActualPriceChart({ points }) {
  if (!Array.isArray(points) || points.length === 0) {
    return <p className="forecast-message">No actual observations are available for this period.</p>
  }
  const values = points.map((point) => Number(point.price)).filter(Number.isFinite)
  if (!values.length) {
    return <p className="forecast-message">No valid actual prices are available for this period.</p>
  }

  const width = 760
  const height = 230
  const padX = 28
  const padY = 24
  const min = Math.min(...values)
  const max = Math.max(...values)

  const coordinates = points.map((point, index) => ({
    point,
    x: padX + (index / Math.max(1, points.length - 1)) * (width - padX * 2),
    y: height - padY - ((Number(point.price) - min) / (max - min || 1)) * (height - padY * 2),
  }))

  const linePoints = coordinates.map((c) => `${c.x},${c.y}`).join(' ')
  const areaPoints = `${coordinates[0].x},${height - padY} ${linePoints} ${coordinates[coordinates.length - 1].x},${height - padY}`

  return (
    <div className="forecast-chart-wrapper">
      <svg
        className="forecast-chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`Chart of ${points.length} actual historical price observations`}
      >
        <defs>
          <linearGradient id="actualPriceGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line
            key={ratio}
            x1={padX}
            y1={padY + ratio * (height - padY * 2)}
            x2={width - padX}
            y2={padY + ratio * (height - padY * 2)}
            stroke="#e2e8f0"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
        ))}
        <polygon points={areaPoints} fill="url(#actualPriceGrad)" />
        {/* Solid plain continuous connecting line (NOT dashed) */}
        <polyline
          fill="none"
          stroke="#2563eb"
          strokeWidth="2.2"
          points={linePoints}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Solid small noticeable dots for each data value */}
        {coordinates.map(({ point, x, y }) => (
          <circle
            key={point.timestamp}
            cx={x}
            cy={y}
            r="2.6"
            fill="#1e3a8a"
          >
            <title>{point.timestamp}: ₹{Number(point.price).toFixed(2)}</title>
          </circle>
        ))}
      </svg>
      <div className="chart-axis-labels">
        <span className="axis-pill">{points[0].timestamp.slice(0, 10)}</span>
        <span className="axis-pill axis-pill-center">
          Actual Price Trajectory (₹{min.toFixed(2)} – ₹{max.toFixed(2)})
        </span>
        <span className="axis-pill">{points[points.length - 1].timestamp.slice(0, 10)}</span>
      </div>
    </div>
  )
}

/**
 * Larger, Multi-Toned Dual Counter-Rotating Orbit Visual (520x520)
 */
const HeroOrbitVisual = () => {
  const outerProducts = [
    {
      label: 'Wireless Headphones',
      tag: '-40%',
      angle: 0,
      bg: 'linear-gradient(135deg, #FFF5EB 0%, #FDE2C8 100%)',
      border: '#F4A261',
      tagBg: '#E76F51',
      icon: (
        <svg viewBox="0 0 36 36" width="32" height="32" fill="none">
          <path d="M8 20v-2a10 10 0 0 1 20 0v2" stroke="#2B2338" strokeWidth="2.8" strokeLinecap="round" />
          <rect x="5" y="18" width="6.5" height="10.5" rx="3.2" fill="#E76F51" />
          <rect x="24.5" y="18" width="6.5" height="10.5" rx="3.2" fill="#E76F51" />
        </svg>
      ),
    },
    {
      label: 'Flagship Smartphone',
      tag: 'Check',
      angle: 72,
      bg: 'linear-gradient(135deg, #F5F0FF 0%, #E6DBFF 100%)',
      border: '#9B7EDE',
      tagBg: '#6C4AB6',
      icon: (
        <svg viewBox="0 0 36 36" width="32" height="32" fill="none">
          <rect x="10" y="4" width="16" height="28" rx="3.5" fill="#2B2338" />
          <rect x="12" y="7" width="12" height="20" rx="1.5" fill="#F5F0FF" />
          <circle cx="18" cy="29.5" r="1.4" fill="#E76F51" />
        </svg>
      ),
    },
    {
      label: 'Running Sneakers',
      tag: '-25%',
      angle: 144,
      bg: 'linear-gradient(135deg, #FFF0F3 0%, #FFD9E2 100%)',
      border: '#E57399',
      tagBg: '#B53860',
      icon: (
        <svg viewBox="0 0 36 36" width="32" height="32" fill="none">
          <path d="M5 23c0-3 3-5 7-5l5-5 4 4c3 2 7 2 10 4v4H5v-2z" fill="#2B2338" />
          <rect x="5" y="25" width="26" height="3.2" rx="1.6" fill="#E57399" />
        </svg>
      ),
    },
    {
      label: 'Chronograph Watch',
      tag: '30d Avg',
      angle: 216,
      bg: 'linear-gradient(135deg, #FEF9E7 0%, #FBE7A1 100%)',
      border: '#D99B26',
      tagBg: '#B47812',
      icon: (
        <svg viewBox="0 0 36 36" width="32" height="32" fill="none">
          <rect x="14" y="3.5" width="8" height="6" rx="1.5" fill="#D99B26" />
          <rect x="14" y="26.5" width="8" height="6" rx="1.5" fill="#D99B26" />
          <rect x="9.5" y="8.5" width="17" height="19" rx="4.5" fill="#2B2338" />
          <path d="M18 13.5v4.5l3.2 2" stroke="#FEF9E7" strokeWidth="2.3" strokeLinecap="round" />
        </svg>
      ),
    },
    {
      label: 'Pro Laptop',
      tag: 'Baseline',
      angle: 288,
      bg: 'linear-gradient(135deg, #F3EAE0 0%, #E5D4C0 100%)',
      border: '#A67C52',
      tagBg: '#7A5430',
      icon: (
        <svg viewBox="0 0 36 36" width="32" height="32" fill="none">
          <rect x="6.5" y="7.5" width="23" height="15.5" rx="2.5" fill="#2B2338" />
          <rect x="9" y="10" width="18" height="10.5" rx="1" fill="#FFF8F0" />
          <path d="M3.5 25h29l-2 3.2h-25L3.5 25z" fill="#E76F51" />
        </svg>
      ),
    },
  ]

  const innerMarketplaces = [
    { name: 'Amazon', angle: 36, dot: '#E76F51', bg: '#FFF7F2', border: '#F4BDAA' },
    { name: 'Flipkart', angle: 108, dot: '#6C4AB6', bg: '#F7F3FF', border: '#D4C4F7' },
    { name: 'Best Buy', angle: 180, dot: '#D99B26', bg: '#FFFBEB', border: '#F3D88C' },
    { name: 'eBay', angle: 252, dot: '#B53860', bg: '#FFF2F6', border: '#F2BACB' },
    { name: 'Walmart', angle: 324, dot: '#7A5430', bg: '#FAF3EB', border: '#DFC7AE' },
  ]

  return (
    <div className="hero-radar-stage">
      {/* Concentric Decorative Rings */}
      <div className="radar-ring radar-ring-outer" />
      <div className="radar-ring radar-ring-mid" />
      <div className="radar-ring radar-ring-inner" />

      {/* Outer Orbit: Clockwise Product Icons */}
      <div className="radar-orbit-track radar-orbit-cw">
        {outerProducts.map((node) => (
          <div
            key={node.label}
            className="radar-orbit-arm"
            style={{ '--start-angle': `${node.angle}deg` }}
          >
            <div className="radar-node-card radar-node-cw" title={node.label}>
              <div
                className="radar-node-inner"
                style={{
                  background: node.bg,
                  borderColor: node.border,
                  transform: `rotate(-${node.angle}deg)`,
                }}
              >
                {node.icon}
                <span className="radar-node-tag" style={{ backgroundColor: node.tagBg }}>
                  {node.tag}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Inner Orbit: Anti-Clockwise Marketplace Badges */}
      <div className="radar-orbit-track radar-orbit-ccw">
        {innerMarketplaces.map((item) => (
          <div
            key={item.name}
            className="radar-orbit-arm-inner"
            style={{ '--start-angle': `${item.angle}deg` }}
          >
            <div className="radar-pill-card radar-node-ccw">
              <div
                className="radar-pill-inner"
                style={{
                  backgroundColor: item.bg,
                  borderColor: item.border,
                  transform: `rotate(-${item.angle}deg)`,
                }}
              >
                <span className="radar-pill-dot" style={{ backgroundColor: item.dot }} />
                <span className="radar-pill-text">{item.name}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Center Shield Hub */}
      <div className="radar-center-hub">
        <div className="radar-center-pulse" />
        <div className="radar-center-badge">
          <svg viewBox="0 0 28 28" width="30" height="30" fill="none">
            <path
              d="M14 2.2L4.2 6.3V13.6C4.2 19.9 8.4 25.5 14 27.2C19.6 25.5 23.8 19.9 23.8 13.6V6.3L14 2.2Z"
              fill="url(#hubShieldGrad)"
            />
            <defs>
              <linearGradient id="hubShieldGrad" x1="4" y1="2" x2="24" y2="27" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#F48C6A" />
                <stop offset="100%" stopColor="#C85A32" />
              </linearGradient>
            </defs>
            <path
              d="M10.2 14.2L12.9 16.9L18.2 11.4"
              stroke="#FFF9F2"
              strokeWidth="2.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      <span className="hero-visual-note">Illustrative dual-orbit visual · not live marketplace scraping</span>
    </div>
  )
}

/**
 * Main Navbar Component (No duplicate top-right Inspect button; features Dataset Scope badge)
 */
const Navbar = ({ onHome, onFeatures, onHowItWorks, onInspect: _onInspect, onModelComparison, isFintech = true }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleNav = (callback) => {
    setMobileMenuOpen(false)
    callback()
  }

  return (
    <nav className={`navbar ${isFintech ? 'navbar-fintech' : ''}`} role="navigation" aria-label="Main Navigation">
      <div className="nav-container">
        <div
          className="nav-logo"
          onClick={onHome}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onHome()}
        >
          <span className={`logo-icon ${isFintech ? 'logo-icon-premium' : ''}`} aria-hidden="true">
            <svg viewBox="0 0 28 28" width="22" height="22" fill="none">
              <path
                d="M14 2.5L5 6.2V13.2C5 18.9 8.8 24.1 14 25.8C19.2 24.1 23 18.9 23 13.2V6.2L14 2.5Z"
                fill="#231D30"
              />
              <path
                d="M10.5 14.2L13 16.6L17.8 11.5"
                stroke="#FAF6F0"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="20.5" cy="7.5" r="3" fill="#F5B041" stroke="#231D30" strokeWidth="1.4" />
            </svg>
          </span>
          <div className="brand-wordmark">
            <span className="brand-main">FakeDeal</span>
            <span className="brand-accent">Buster</span>
          </div>
        </div>

        <div className={`nav-links ${mobileMenuOpen ? 'open' : ''}`}>
          <a
            href="#home"
            onClick={(e) => {
              e.preventDefault()
              handleNav(onHome)
            }}
            className="nav-link"
          >
            Home
          </a>
          <a
            href="#features"
            onClick={(e) => {
              e.preventDefault()
              handleNav(onFeatures)
            }}
            className="nav-link"
          >
            Features
          </a>
          <a
            href="#how-it-works"
            onClick={(e) => {
              e.preventDefault()
              handleNav(onHowItWorks)
            }}
            className="nav-link"
          >
            How It Works
          </a>
        </div>

        <div className="nav-cta">
          <div className="nav-status-pill" onClick={_onInspect} role="button" tabIndex={0} title="Inspect a Product Live">
            <span className="status-pill-dot" aria-hidden="true" />
            <span className="status-pill-label">⚡ 30-Day Dataset Active</span>
            <span className="status-pill-tag">Live Engine</span>
          </div>
          <div
            className="nav-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            role="button"
            tabIndex={0}
            aria-label="Toggle navigation menu"
            onKeyDown={(e) => e.key === 'Enter' && setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </nav>
  )
}

/**
 * Landing Page Component (Rich Espresso-Plum, Terracotta Coral, Amber Gold & Champagne Beige Palette)
 */
const LandingPage = ({ onInspect, onFeatures, onModelComparison }) => {
  return (
    <div className="landing-page landing-fintech" id="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-beige-glow" aria-hidden="true" />
        <div className="hero-coral-glow" aria-hidden="true" />

        <div className="container">
          <div className="hero-grid">
            <div className="hero-content">
              <span className="hero-badge">
                <span className="hero-badge-icon" aria-hidden="true">⚡</span> Price Intelligence &amp; Baseline Verification
              </span>

              <h1 className="hero-title">
                Unmask Fake <br />
                <span className="highlight">Sale Discounts.</span>
              </h1>

              <p className="hero-subtitle">
                Verify advertised deals against genuine 30-day historical price baselines and Isolation Forest anomaly
                signals before you buy.
              </p>

              <div className="hero-actions">
                <button className="btn btn-coral btn-hero-main" onClick={onInspect}>
                  Inspect a Product →
                </button>
                <button className="btn btn-beige" onClick={onFeatures}>
                  Explore Features
                </button>
              </div>

              <div className="hero-stats">
                <div className="hero-stat-item stat-accent-coral">
                  <span className="hero-stat-number">30-Day</span>
                  <span className="hero-stat-label">Historical Baseline</span>
                </div>
                <div className="hero-stat-item stat-accent-violet">
                  <span className="hero-stat-number">4-Feature</span>
                  <span className="hero-stat-label">Isolation Forest ML</span>
                </div>
                <div className="hero-stat-item stat-accent-amber">
                  <span className="hero-stat-number">5 Marketplaces</span>
                  <span className="hero-stat-label">Amazon, Best Buy, eBay, Flipkart, Walmart</span>
                </div>
              </div>
            </div>

            <div className="hero-visual" aria-hidden="true">
              <HeroOrbitVisual />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features" id="features">
        <div className="container">
          <div className="section-header">
            <span className="section-tag tag-plum">Historical Price Review</span>
            <h2 className="section-title">Engineered to Spot Every Pricing Trick</h2>
            <p className="section-subtitle">
              Compare submitted prices with available historical observations. An anomaly is an indicative statistical
              signal, not proof of seller fraud.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card card-accent-amber">
              <div className="feature-icon icon-amber" aria-hidden="true">🔍</div>
              <h3 className="feature-title">Price Anomaly Assessment</h3>
              <p className="feature-description">
                The Isolation Forest flags unusual combinations of historical price features without making unsupported
                legal claims about a seller.
              </p>
            </div>

            <div className="feature-card card-accent-coral">
              <div className="feature-icon icon-coral" aria-hidden="true">📉</div>
              <h3 className="feature-title">Historical Price Analysis</h3>
              <p className="feature-description">
                Compares submitted deal prices against trailing 30-day historical pricing baselines for the selected
                marketplace.
              </p>
            </div>

            <div className="feature-card card-accent-violet">
              <div className="feature-icon icon-violet" aria-hidden="true">📈</div>
              <h3 className="feature-title">Conditional 14-Day Forecast</h3>
              <p className="feature-description">
                Projects baseline price trajectories only when sufficient consecutive daily observations exist in the
                dataset.
              </p>
            </div>

            <div className="feature-card card-accent-rose">
              <div className="feature-icon icon-rose" aria-hidden="true">🛡️</div>
              <h3 className="feature-title">Multi-Platform Baseline Engine</h3>
              <p className="feature-description">
                Cross-checks reference MRP against trailing 30-day baseline distributions across Amazon, Flipkart, Walmart, and eBay.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works" id="how-it-works">
        <div className="container">
          <div className="section-header">
            <span className="section-tag tag-amber">How It Works</span>
            <h2 className="section-title">Verify Any Deal in Three Steps</h2>
            <p className="section-subtitle">
              Use the available product history to evaluate the submitted price and model signal in seconds.
            </p>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number step-espresso">01</div>
              <h3 className="step-title">Enter Product Details</h3>
              <p className="step-description">
                Enter a product name, choose its platform and category, then provide the listed prices and observation
                time.
              </p>
            </div>

            <div className="step-card">
              <div className="step-number step-coral">02</div>
              <h3 className="step-title">AI Price Analysis</h3>
              <p className="step-description">
                The backend matches dataset history and the trained Isolation Forest evaluates canonical price and
                discount features.
              </p>
            </div>

            <div className="step-card">
              <div className="step-number step-violet">03</div>
              <h3 className="step-title">Review Clear Verdict</h3>
              <p className="step-description">
                Review the indicative anomaly assessment, historical trajectory chart, and separate FDI status when
                available.
              </p>
            </div>
          </div>

          <div className="how-it-works-cta">
            <button className="btn btn-coral btn-lg" onClick={onInspect}>
              Inspect a Product Now →
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

/**
 * Professional Footer Component
 */
const Footer = ({ onHome, onFeatures, onHowItWorks, onInspect, onModelComparison, isFintech = true }) => (
  <footer className={`footer ${isFintech ? 'footer-fintech' : ''}`} role="contentinfo">
    <div className="footer-content">
      <div className="footer-logo">
        <span className={`logo-icon ${isFintech ? 'logo-icon-premium' : ''}`} aria-hidden="true">
          <svg viewBox="0 0 28 28" width="20" height="20" fill="none">
            <path
              d="M14 2.5L5 6.2V13.2C5 18.9 8.8 24.1 14 25.8C19.2 24.1 23 18.9 23 13.2V6.2L14 2.5Z"
              fill="#231D30"
            />
            <path
              d="M10.5 14.2L13 16.6L17.8 11.5"
              stroke="#FAF6F0"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <div className="brand-wordmark">
          <span className="brand-main">FakeDeal</span>
          <span className="brand-accent">Buster</span>
        </div>
      </div>

      <p className="footer-description">
        Historical price pattern analysis with separate ML anomaly and provisional FDI indicators.
      </p>

      <div className="footer-links">
        <a href="#home" onClick={(e) => { e.preventDefault(); onHome(); }} className="footer-link">Home</a>
        <a href="#features" onClick={(e) => { e.preventDefault(); onFeatures(); }} className="footer-link">Features</a>
        <a href="#how-it-works" onClick={(e) => { e.preventDefault(); onHowItWorks(); }} className="footer-link">How It Works</a>
        <a href="#inspector" onClick={(e) => { e.preventDefault(); onInspect(); }} className="footer-link">Product Inspector</a>
      </div>

      <p className="footer-disclaimer">
        Disclaimer: An anomaly is not proof of fraud. FDI is a provisional pricing indicator, not a certified fraud
        probability.
      </p>

      <p className="footer-copyright">
        © 2026 FakeDeal Buster. All rights reserved.
      </p>
    </div>
  </footer>
)

/**
 * Dataset-backed inspector. Its user-facing metadata is adapted by FastAPI to
 * the unchanged five-field central analysis request.
 */
function DatasetProductInspector({ onBack, onViewModelComparison }) {
  const [catalog, setCatalog] = useState(null)
  const [catalogError, setCatalogError] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [form, setForm] = useState({ product_name: '', platform: '', category: '', original_price: '', current_price: '', as_of: '2024-11-15T12:00', historical_mode: true, seller_name: '', seller_rating: '', product_url: '', selected_product_id: '' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [candidateSelectionPossible, setCandidateSelectionPossible] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const submitting = useRef(false)

  useEffect(() => {
    let mounted = true
    loadCatalogMetadata().then((data) => { if (mounted) setCatalog(data) }).catch((error) => { if (mounted) setCatalogError(error.message) })
    return () => { mounted = false }
  }, [])

  const retryCatalog = async () => {
    setCatalogError('')
    try { setCatalog(await loadCatalogMetadata()) }
    catch (error) { setCatalogError(error.message) }
  }

  const categoryPlatforms = catalog?.category_platforms || []
  const platforms = catalog?.platforms?.filter((platform) => !form.category || categoryPlatforms.some((pair) => pair.category === form.category && pair.platform === platform)) || []
  const categories = catalog?.categories?.filter((category) => !form.platform || categoryPlatforms.some((pair) => pair.platform === form.platform && pair.category === category)) || []
  const dateRange = catalog?.date_range
  const afterDataRange = Boolean(dateRange?.end && form.as_of.slice(0, 10) > dateRange.end)

  useEffect(() => {
    const query = form.product_name.trim()
    if (query.length < 2) return undefined
    let active = true
    const timer = setTimeout(async () => {
      setSearching(true)
      setSearchError('')
      try {
        const matches = await searchCatalogProducts({ q: query, category: form.category, platform: form.platform, limit: 20 })
        if (active) setSuggestions(matches)
      } catch (error) {
        if (active) { setSuggestions([]); setSearchError(error.message || 'Product suggestions are unavailable.') }
      } finally {
        if (active) setSearching(false)
      }
    }, 250)
    return () => { active = false; clearTimeout(timer) }
  }, [form.product_name, form.category, form.platform])

  const change = (event) => {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value, ...(name === 'product_name' || name === 'category' || name === 'platform' ? { selected_product_id: '' } : {}) }))
    if (name === 'product_name' && value.trim().length < 2) setSuggestions([])
    setErrors((previous) => { const next = { ...previous }; delete next[name]; return next })
    setApiError(null)
    if (name !== 'selected_product_id') setCandidates([])
    setResult(null)
  }

  const chooseSuggestion = (item) => {
    setForm((previous) => ({ ...previous, product_name: item.title, category: item.category, platform: item.platform, selected_product_id: item.product_id }))
    setSuggestions([])
    setErrors((previous) => ({ ...previous, product_name: undefined, category: undefined, platform: undefined }))
  }

  const submit = async (event) => {
    event.preventDefault()
    if (!canSubmit(loading, submitting.current)) return
    setApiError(null)
    setResult(null)
    const validation = validateInspectionForm(form, catalog)
    if (Object.keys(validation).length) { setErrors(validation); return }
    setErrors({})
    submitting.current = true
    setLoading(true)
    try {
      const response = await inspectListing({ ...form, as_of: form.historical_mode ? toNaiveIsoTimestamp(form.as_of) : undefined })
      if (response.status === 'AMBIGUOUS_PRODUCT') {
        setCandidates(response.candidates || [])
        setCandidateSelectionPossible(Boolean(response.selection_possible))
      } else if (response.status === 'ANALYZED' && response.analysis?.ml_anomaly && response.analysis?.fdi) {
        setCandidates([])
        setResult(response)
      } else {
        throw new Error('The server returned an unrecognized analysis response. No result was displayed.')
      }
    } catch (error) {
      setApiError({ status: error.status || 0, code: error.code || 'REQUEST_FAILED', message: error.message || 'The request could not be completed.' })
    } finally {
      submitting.current = false
      setLoading(false)
    }
  }

  const analysis = result?.analysis
  const ml = analysis?.ml_anomaly
  const mlState = getMlState(analysis)
  const fdiState = getFdiState(analysis?.fdi)
  const syntheticState = getSyntheticClassifierState(analysis)
  const assessmentVerdict = getAssessmentVerdict(analysis)

  return (
    <div className="inspector-page inspector-nordic-light">
      <div className="container">
        <button className="btn-back" onClick={onBack} aria-label="Back to Home" style={{ background: '#1e1b4b', color: '#ffffff', border: '1.5px solid #312e81', fontWeight: 700 }}>← Back to Home</button>
        <header className="inspector-hero-banner">
          <span className="inspector-badge">🛡️ PRICE ANOMALY ENGINE</span>
          <h1>Live Product Price &amp; Anomaly Inspector</h1>
          <p>Enter listing details to query genuine historical price baselines and Isolation Forest anomaly signals.</p>
        </header>

        <main className="inspector-main">
          <div className="inspector-grid">
            <section className="glass-card section-form" aria-labelledby="form-heading">
              <div className="section-heading-row"><span className="section-icon" aria-hidden="true">📝</span><div><h2 className="card-title" id="form-heading">Product Inspection Form</h2><p className="card-subtitle">Historical analysis requires records earlier than the selected time.</p></div></div>
              {catalogError && <div className="server-error" role="alert">Dataset catalog unavailable: {catalogError}<button type="button" className="btn btn-secondary" onClick={retryCatalog}>Retry loading products</button></div>}
              {apiError && <div className="server-error" role="alert"><strong>{apiError.status ? `HTTP ${apiError.status} · ` : ''}{apiError.code}</strong><p className="server-error-message">{apiError.message}</p><p className="server-error-note">Your entries are preserved. Correct the details or retry when the service is available.</p></div>}

              <form onSubmit={submit} noValidate>
                <div className="form-group">
                  <label htmlFor="product_name" className="form-label">Product Name <span className="required">*</span></label>
                  <input id="product_name" name="product_name" autoComplete="off" className={`form-input ${errors.product_name ? 'input-error' : ''}`} value={form.product_name} onChange={change} maxLength="200" aria-required="true" aria-invalid={!!errors.product_name} aria-controls="catalog-suggestions" aria-expanded={suggestions.length > 0} disabled={loading} />
                  {searching && <span className="form-helper" role="status">Searching actual catalogue…</span>}
                  {suggestions.length > 0 && <ul id="catalog-suggestions" className="catalog-suggestions" role="listbox" aria-label="Matching dataset products">{suggestions.map((item) => <li key={`${item.product_id}-${item.platform}`}><button type="button" role="option" className="catalog-suggestion" onClick={() => chooseSuggestion(item)}>{item.title}<span>{[item.brand, item.category, item.platform].filter(Boolean).join(' · ')}</span>{item.asin && <small>Catalog reference {item.asin}</small>}</button></li>)}</ul>}
                  {searchError && <span className="error-message" role="alert">Catalogue search failed: {searchError}</span>}
                  {!searching && !searchError && form.product_name.trim().length >= 2 && suggestions.length === 0 && <span className="form-helper" role="status">No catalogue suggestions for these filters. You can still submit the exact product details for resolution.</span>}
                  <span className="form-helper">Suggestions come from real dataset records; internal product IDs are never shown.</span>
                  {errors.product_name && <span className="error-message">{errors.product_name}</span>}
                </div>

                <div className="form-row">
                  <div className="form-group"><label htmlFor="platform" className="form-label">Platform <span className="required">*</span></label><select id="platform" name="platform" className={`form-select ${errors.platform ? 'input-error' : ''}`} value={form.platform} onChange={change} aria-required="true" aria-invalid={!!errors.platform} disabled={loading}><option value="">Select platform</option>{platforms.map((item) => <option key={item} value={item}>{{ amazon: 'Amazon', bestbuy: 'Best Buy', ebay: 'eBay', flipkart: 'Flipkart', walmart: 'Walmart' }[item] || item}</option>)}</select>{errors.platform && <span className="error-message">{errors.platform}</span>}</div>
                  <div className="form-group"><label htmlFor="category" className="form-label">Category <span className="required">*</span></label><select id="category" name="category" className={`form-select ${errors.category ? 'input-error' : ''}`} value={form.category} onChange={change} aria-required="true" aria-invalid={!!errors.category} disabled={loading}><option value="">Select category</option>{categories.map((item) => <option key={item} value={item}>{item}</option>)}</select>{errors.category && <span className="error-message">{errors.category}</span>}</div>
                </div>

                <div className="form-row">
                  {['original_price', 'current_price'].map((field) => <div className="form-group" key={field}><label htmlFor={field} className="form-label">{field === 'original_price' ? 'Original Price' : 'Current Price'} (₹) <span className="required">*</span></label><input type="number" id={field} name={field} className={`form-input ${errors[field] ? 'input-error' : ''}`} value={form[field]} onChange={change} min="0.01" step="0.01" placeholder="0.00" aria-required="true" aria-invalid={!!errors[field]} disabled={loading} />{errors[field] && <span className="error-message">{errors[field]}</span>}</div>)}
                </div>

                <div className="historical-mode-card">
                  <div className="historical-toggle-row">
                    <label className="historical-toggle-label">
                      <input
                        type="checkbox"
                        name="historical_mode"
                        className="historical-checkbox"
                        checked={form.historical_mode}
                        onChange={(event) => setForm((previous) => ({ ...previous, historical_mode: event.target.checked }))}
                        disabled={loading}
                      />
                      <span className="historical-toggle-text">
                        <strong>📅 Historical Baseline Analysis Mode</strong> (Select a past reference date &amp; time)
                      </span>
                    </label>
                  </div>
                  <span className="form-helper" style={{ display: 'block', marginTop: '6px' }}>
                    Current analysis uses the live system time. The dataset ends on {dateRange?.end || '2024-12-30'}; choose a 2024 date (e.g. 2024-11-15) to evaluate festive price baselines.
                  </span>
                  {form.historical_mode && (
                    <div className="form-group historical-date-group" style={{ marginTop: '16px' }}>
                      <label htmlFor="as_of" className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>Price Checked On <span className="required">*</span></span>
                        <span className="historical-date-badge">Dataset Range: 2023–2024</span>
                      </label>
                      <input
                        type="datetime-local"
                        id="as_of"
                        name="as_of"
                        className={`form-input datetime-picker-enhanced ${errors.as_of ? 'input-error' : ''}`}
                        value={form.as_of}
                        onChange={change}
                        onClick={(e) => {
                          try {
                            if (e.target && typeof e.target.showPicker === 'function') e.target.showPicker()
                          } catch (_) {}
                        }}
                        aria-required="true"
                        aria-invalid={!!errors.as_of}
                        disabled={loading}
                      />
                      <div className="historical-presets">
                        <span className="historical-presets-label">Quick Demo Date:</span>
                        <button
                          type="button"
                          className="preset-date-btn"
                          onClick={() => {
                            setForm((prev) => ({ ...prev, as_of: '2024-11-15T12:00' }))
                            setErrors((prev) => { const next = { ...prev }; delete next.as_of; return next })
                          }}
                          disabled={loading}
                          title="Festive Season 2024 (recommended for live demo)"
                        >
                          📅 15 Nov 2024 (Festive Demo)
                        </button>
                        <button
                          type="button"
                          className="preset-date-btn"
                          onClick={() => {
                            setForm((prev) => ({ ...prev, as_of: '2024-10-18T10:00' }))
                            setErrors((prev) => { const next = { ...prev }; delete next.as_of; return next })
                          }}
                          disabled={loading}
                          title="Mid-Autumn 2024 Baseline"
                        >
                          📅 18 Oct 2024 (Baseline)
                        </button>
                      </div>
                      <span className="form-helper">Only actual observations strictly earlier than this time are considered.</span>
                      {afterDataRange && <span className="error-message" role="status">This is later than the newest dataset record; the system will not treat stale records as current.</span>}
                      {errors.as_of && <span className="error-message">{errors.as_of}</span>}
                    </div>
                  )}
                </div>

                <div className="form-row-grid form-grid-3">
                  <div className="form-group"><label htmlFor="seller_name" className="form-label">Seller Name (user-provided, unverified)</label><input id="seller_name" name="seller_name" maxLength="120" className={`form-input ${errors.seller_name ? 'input-error' : ''}`} value={form.seller_name} onChange={change} aria-invalid={!!errors.seller_name} disabled={loading} />{errors.seller_name && <span className="error-message">{errors.seller_name}</span>}</div>
                  <div className="form-group"><label htmlFor="seller_rating" className="form-label">Seller Rating (user-provided, unverified; 1.0–5.0)</label><input type="number" id="seller_rating" name="seller_rating" min="1" max="5" step="0.1" className={`form-input ${errors.seller_rating ? 'input-error' : ''}`} value={form.seller_rating} onChange={change} aria-invalid={!!errors.seller_rating} disabled={loading} /><span className="form-helper">Optional metadata only; not verified and not an ML feature.</span>{errors.seller_rating && <span className="error-message">{errors.seller_rating}</span>}</div>
                  <div className="form-group"><label htmlFor="product_url" className="form-label">Product URL</label><input type="url" id="product_url" name="product_url" className={`form-input ${errors.product_url ? 'input-error' : ''}`} value={form.product_url} onChange={change} placeholder="https://" aria-invalid={!!errors.product_url} disabled={loading} /><span className="form-helper">Amazon product URLs can be checked against an exact dataset ASIN. Other URLs are accepted as listing metadata but do not verify product identity.</span>{errors.product_url && <span className="error-message">{errors.product_url}</span>}</div>
                </div>

                {candidates.length > 0 && (candidateSelectionPossible
                  ? <fieldset className="form-group"><legend className="form-label">Select the matching listing</legend><span className="form-helper">Several actual records match. Choose using the real brand or catalog reference.</span>{candidates.map((item) => <label className="candidate-option" key={item.product_id}><input type="radio" name="selected_product_id" value={item.product_id} checked={form.selected_product_id === item.product_id} onChange={change} />{item.title}{item.brand ? ` · ${item.brand}` : ''}{item.asin ? ` · Catalog reference ${item.asin}` : ''}</label>)}</fieldset>
                  : <p className="server-error" role="alert">Several records match, but this dataset has no distinct product metadata to choose between them. The product cannot be resolved reliably.</p>)}
                <button type="submit" className={`btn-submit ${loading ? 'btn-loading' : ''}`} disabled={loading || !catalog || (candidates.length > 0 && (!candidateSelectionPossible || !form.selected_product_id))} aria-busy={loading}>{loading ? 'Analysing historical prices…' : candidates.length ? 'Analyze selected product' : 'Analyse Product'}</button>
                {!catalog && !catalogError && <p role="status" className="form-helper">Loading supported product information…</p>}
              </form>
            </section>

            {loading && <section className="glass-card analysis-loading" role="status" aria-live="polite"><div className="loading-spinner" /><div className="loading-text"><span>Checking historical records and model signals</span><span className="loading-dots">…</span></div></section>}
            {!loading && analysis && <>
              <section className="glass-card result-card assessment-verdict-card" aria-labelledby="assessment-verdict-heading">
                <div className="section-heading-row"><span className="section-icon" aria-hidden="true">⚖️</span><div><h2 className="card-title" id="assessment-verdict-heading">Overall Discount Assessment</h2><p className="card-subtitle">Formal assessment state derived from historical evidence and production ML anomaly detection.</p></div></div>
                <div className="ml-anomaly-card">
                  <div className="ml-anomaly-info">
                    <h3 className="ml-anomaly-title">{assessmentVerdict.label}</h3>
                    <p className="ml-anomaly-desc">{assessmentVerdict.description}</p>
                  </div>
                  <span className={`ml-status-badge ${assessmentVerdict.badgeClass}`}>{assessmentVerdict.label}</span>
                </div>
                <p className="form-helper">Assessment states are descriptive evaluations based on historical baseline conformity. They are not legal or scientifically confirmed fraud judgments.</p>
              </section>
              <section className="glass-card result-card" aria-labelledby="synthetic-classifier-heading">
                <h2 className="card-title" id="synthetic-classifier-heading">Synthetic Scenario Classifier</h2>
                <p className="card-subtitle">{syntheticState.label}</p>
                {syntheticState.message && <p role="status">{syntheticState.message}</p>}
                {syntheticState.disclaimer && <p className="form-helper">{syntheticState.disclaimer}</p>}
                <p className="form-helper">This experiment was trained on generated scenario labels. It is not evidence of real-world fraud, a fraud probability, seller intent, or a verified deal.</p>
              </section>
              <section className="glass-card result-card" aria-label="Listing verification status"><div className="details-grid"><div className="detail-row"><span className="detail-label">Product URL identity</span><span className="detail-value">{result.url_mapping_supported ? 'VERIFIED — exact Amazon ASIN matched dataset metadata' : form.product_url ? 'NOT VERIFIED — URL did not establish identity; name/platform/category were resolved separately' : 'NOT PROVIDED'}</span></div><div className="detail-row"><span className="detail-label">Seller metadata</span><span className="detail-value">{form.seller_name || form.seller_rating ? 'User-provided and unverified; not used by the model' : 'Not provided'}</span></div></div></section>
              <section className="glass-card result-card" aria-labelledby="details-heading"><div className="section-heading-row"><span className="section-icon" aria-hidden="true">📊</span><div><h2 className="card-title" id="details-heading">Product Details &amp; Price Breakdown</h2><p className="card-subtitle">{result.product?.title} · {result.product?.brand} · {result.product?.category} · {form.platform}</p></div></div><div className="price-overview-card"><div className="price-item"><span className="price-item-label">Original Price</span><span className="price-item-value original">₹{Number(analysis.original_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span></div><div className="price-item"><span className="price-item-label">Current Price</span><span className="price-item-value current">₹{Number(analysis.current_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span></div><div className="price-item"><span className="price-item-label">Discount Percentage</span><span className="price-item-value discount">{Number.isFinite(analysis.discount_percentage) ? `${analysis.discount_percentage.toFixed(2)}%` : 'Unavailable'}</span></div></div><div className="details-grid"><div className="detail-row"><span className="detail-label">Analysis timestamp</span><span className="detail-value">{ml?.timestamp || 'Unavailable'}</span></div><div className="detail-row"><span className="detail-label">Dataset identifier</span><span className="detail-value">{result.product?.asin ? `ASIN ${result.product.asin}` : 'Not available'}</span></div></div><p className="explanation-text">{analysis.explanation}</p>{result.historical_summary && <p className="form-helper">Prior 30 day observations: {result.historical_summary.observation_count}; average {result.historical_summary.average_price == null ? 'unavailable' : `₹${result.historical_summary.average_price.toFixed(2)}`}; range {result.historical_summary.minimum_price == null ? 'unavailable' : `₹${result.historical_summary.minimum_price.toFixed(2)}–₹${result.historical_summary.maximum_price.toFixed(2)}`}.</p>}</section>
              {Array.isArray(result.price_history) && result.price_history.length > 0 && <section className="glass-card result-card" aria-labelledby="history-heading"><h2 className="card-title" id="history-heading">Actual recorded price history</h2><p className="card-subtitle">{result.price_history.length} observed points; markers represent source observations only.</p><ActualPriceChart points={result.price_history} /><details className="observation-ledger-details">
                    <summary className="observation-ledger-summary">
                      <span>Show observation dates and prices</span>
                      <span className="ledger-count-pill">{result.price_history.length} Records</span>
                    </summary>
                    <div className="observation-table-scroll">
                      <table className="observation-ledger-table">
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Observation Date</th>
                            <th>Recorded Price (₹)</th>
                            <th>Change vs Prior</th>
                            <th>Trend</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.price_history.map((pt, idx) => {
                            const price = Number(pt.price)
                            const prevPrice = idx > 0 ? Number(result.price_history[idx - 1].price) : null
                            const delta = prevPrice !== null && Number.isFinite(prevPrice) ? price - prevPrice : null
                            return (
                              <tr key={`${pt.timestamp}-${idx}`}>
                                <td className="ledger-idx">{idx + 1}</td>
                                <td className="ledger-date">{String(pt.timestamp).slice(0, 10)}</td>
                                <td className="ledger-price">₹{price.toFixed(2)}</td>
                                <td className="ledger-delta">
                                  {delta === null
                                    ? 'Initial'
                                    : delta > 0.004
                                    ? `+₹${delta.toFixed(2)}`
                                    : delta < -0.004
                                    ? `-₹${Math.abs(delta).toFixed(2)}`
                                    : '₹0.00'}
                                </td>
                                <td>
                                  {delta === null ? (
                                    <span className="trend-badge trend-neutral">Baseline</span>
                                  ) : delta > 0.004 ? (
                                    <span className="trend-badge trend-up">▲ Increase</span>
                                  ) : delta < -0.004 ? (
                                    <span className="trend-badge trend-down">▼ Drop</span>
                                  ) : (
                                    <span className="trend-badge trend-neutral">• Unchanged</span>
                                  )}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </details></section>}
              {Array.isArray(result.cross_platform) && result.cross_platform.length > 1 && <section className="glass-card result-card"><h2 className="card-title">Latest recorded prices across platforms</h2><p className="card-subtitle">Same verified dataset product, latest observation before this analysis time.</p><div className="history-points">{result.cross_platform.map((point) => <span key={point.platform}>{point.platform} · ₹{Number(point.price).toFixed(2)} · {point.timestamp.slice(0, 10)}</span>)}</div></section>}
              <section className="glass-card result-card" aria-labelledby="ml-heading"><div className="section-heading-row"><span className="section-icon" aria-hidden="true">🤖</span><div><h2 className="card-title" id="ml-heading">Machine Learning Anomaly Assessment</h2><p className="card-subtitle">A statistical signal, not proof of fraud.</p></div></div><div className="ml-anomaly-card"><div className="ml-anomaly-info"><h3 className="ml-anomaly-title">{mlState.label}</h3><p className="ml-anomaly-desc">{ml?.status === 'NEEDS_MORE_DATA' ? ml?.explanation?.message || 'Insufficient historical data is available.' : ml?.explanation?.interpretation || 'The model result is unavailable.'}</p></div><span className={`ml-status-badge ${mlState.kind === 'anomaly' ? 'anomaly' : mlState.kind === 'no-anomaly' ? 'normal' : 'inconclusive'}`}>{mlState.label}</span></div>{ml?.status === 'OK' && <div className="details-grid"><div className="detail-row"><span className="detail-label">Anomaly score (model scale)</span><span className="detail-value">{ml.anomaly_score}</span></div><div className="detail-row"><span className="detail-label">Model version</span><span className="detail-value">{ml.model_version}</span></div></div>}</section>
              <section className="glass-card result-card" aria-labelledby="fdi-heading"><div className="section-heading-row"><span className="section-icon" aria-hidden="true">📈</span><div><h2 className="card-title" id="fdi-heading">Fake Discount Indicator (FDI)</h2><p className="card-subtitle">Separate provisional pricing indicator, not a fraud probability.</p></div></div><div className="fdi-card">{fdiState.kind === 'available' ? <p>FDI score: {fdiState.score.toFixed(1)} · {fdiState.level}</p> : <p role="status">{fdiState.label}: {fdiState.message}</p>}</div></section>
              <section className="forecast-container" aria-labelledby="forecast-heading"><div className="forecast-header"><h2 className="forecast-title" id="forecast-heading">Conditional 14-Day Price Forecast</h2><p className="forecast-subtitle">Baseline forecast from observed history, shown only when the required daily record and rolling backtest are available.</p></div><ForecastChart data={result.forecast} status={result.forecast?.status} />{result.forecast?.status === 'AVAILABLE' && <><p className="form-helper">Method: {result.forecast.method.replaceAll('_', ' ')} · {result.forecast.training_observation_count} actual daily observations through {result.forecast.reference_date}.</p><p className="form-helper">Chronological backtest MAE / RMSE: last-observation {result.forecast.backtest.metrics.last_observation.mae} / {result.forecast.backtest.metrics.last_observation.rmse}; trailing 7-day mean {result.forecast.backtest.metrics.trailing_7_day_mean.mae} / {result.forecast.backtest.metrics.trailing_7_day_mean.rmse}. {result.forecast.limitations}</p></>}</section>
            </>}
            {!loading && !analysis && candidates.length === 0 && <section className="glass-card result-empty"><div className="result-empty-icon" aria-hidden="true">🛡️</div><h3 className="result-empty-title">Ready for Price Inspection</h3><p className="result-empty-message">Enter a product name and listing details. The backend resolves the product against actual dataset records.</p></section>}
          </div>
        </main>
      </div>
    </div>
  )
}

/**
 * Model Comparison Component
 * Displays the supervised experiment benchmark comparing Logistic Regression vs Random Forest
 * on held-out synthetic discount scenarios.
 */
function ModelComparisonView({ onBack }) {
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    loadSyntheticModelComparison()
      .then((data) => {
        if (active) {
          setComparison(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message || 'Could not load model comparison metrics.')
          setLoading(false)
        }
      })
    return () => { active = false }
  }, [])

  const lr = comparison?.test_metrics?.logistic_regression
  const rf = comparison?.test_metrics?.random_forest

  return (
    <div className="inspector-page model-comparison-page model-comparison-light">
      <div className="container">
        <button className="btn-back" onClick={onBack} aria-label="Back to Home" style={{ background: '#1e1b4b', color: '#ffffff', border: '1.5px solid #312e81', fontWeight: 700 }}>← Back to Home</button>
        <header className="inspector-header">
          <span className="status-badge">Supervised Experiment Benchmark</span>
          <h1 className="header-title"><span className="header-icon" aria-hidden="true">🔬</span> Model Comparison: LR vs Random Forest</h1>
          <p className="header-subtitle">Side-by-side classification benchmark evaluating discrimination metrics, false-positive control, and decision thresholds across held-out test partitions.</p>
        </header>

        <main className="inspector-main">
          {loading && (
            <section className="glass-card analysis-loading" role="status">
              <div className="loading-spinner" />
              <div className="loading-text"><span>Loading model comparison metrics from backend</span><span className="loading-dots">…</span></div>
            </section>
          )}

          {error && (
            <div className="server-error" role="alert">
              <strong>Error loading model comparison:</strong> {error}
            </div>
          )}

          {!loading && comparison && (
            <div className="inspector-grid" style={{ gridTemplateColumns: '1fr' }}>
              <section className="glass-card result-card">
                <div className="section-heading-row">
                  <span className="section-icon" aria-hidden="true">🏆</span>
                  <div>
                    <h2 className="card-title">Selected Model: Random Forest</h2>
                    <p className="card-subtitle" style={{ color: '#475569' }}>
                      Validation Decision Threshold: <strong style={{ color: '#0f172a', fontWeight: 700 }}>{comparison.selected_threshold?.toFixed(4)}</strong> · Threshold Rule: <span style={{ color: '#0f172a', fontWeight: 700 }}>{comparison.threshold_rule}</span>
                    </p>
                  </div>
                </div>
                <div className="details-grid">
                  <div className="detail-row">
                    <span className="detail-label" style={{ color: '#475569' }}>Training Split</span>
                    <span className="detail-value" style={{ color: '#0f172a', fontWeight: 700 }}>28,000 examples (14k genuine / 14k inflated)</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label" style={{ color: '#475569' }}>Validation Split</span>
                    <span className="detail-value" style={{ color: '#0f172a', fontWeight: 700 }}>6,000 examples (used for threshold &amp; model selection)</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label" style={{ color: '#475569' }}>Held-Out Test Split</span>
                    <span className="detail-value" style={{ color: '#0f172a', fontWeight: 700 }}>6,000 examples (evaluated once for final reporting)</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label" style={{ color: '#475569' }}>Evaluation Scope</span>
                    <span className="detail-value" style={{ color: '#0f172a', fontWeight: 700 }}><strong>{comparison.evaluation_scope}</strong></span>
                  </div>
                </div>
                <p className="form-helper" style={{ marginTop: '14px', background: '#fffbeb', border: '1px solid #fde68a', color: '#78350f', padding: '12px 16px', borderRadius: '10px' }}>
                  ⚠️ <strong>Academic Disclaimer:</strong> {comparison.disclaimer} All scores reflect recovery of generator rules and must not be claimed as real-world e-commerce fraud accuracy.
                </p>
              </section>

              <section className="glass-card result-card">
                <h2 className="card-title">Held-Out Test Set Performance Benchmark</h2>
                <p className="card-subtitle">Side-by-side comparison on 6,000 independent test examples (3,000 genuine, 3,000 artificially inflated).</p>

                <div className="comparison-table-wrapper">
                  <table className="comparison-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Logistic Regression (Baseline)</th>
                        <th>Random Forest (Selected)</th>
                        <th>Advantage / Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Decision Threshold</strong></td>
                        <td>{lr?.threshold?.toFixed(4)}</td>
                        <td><strong>{rf?.threshold?.toFixed(4)}</strong></td>
                        <td>Selected on validation split</td>
                      </tr>
                      <tr>
                        <td><strong>Precision</strong></td>
                        <td>{lr?.precision ? (lr.precision * 100).toFixed(2) + '%' : '—'}</td>
                        <td><strong>{rf?.precision ? (rf.precision * 100).toFixed(2) + '%' : '—'}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+1.54%)</td>
                      </tr>
                      <tr>
                        <td><strong>Recall (Sensitivity)</strong></td>
                        <td>{lr?.recall ? (lr.recall * 100).toFixed(2) + '%' : '—'}</td>
                        <td><strong>{rf?.recall ? (rf.recall * 100).toFixed(2) + '%' : '—'}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+6.90%)</td>
                      </tr>
                      <tr>
                        <td><strong>F1-Score</strong></td>
                        <td>{lr?.f1?.toFixed(4)}</td>
                        <td><strong>{rf?.f1?.toFixed(4)}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+0.0491)</td>
                      </tr>
                      <tr>
                        <td><strong>ROC-AUC</strong></td>
                        <td>{lr?.roc_auc?.toFixed(4)}</td>
                        <td><strong>{rf?.roc_auc?.toFixed(4)}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+0.0269)</td>
                      </tr>
                      <tr>
                        <td><strong>PR-AUC (Average Precision)</strong></td>
                        <td>{lr?.pr_auc_average_precision?.toFixed(4)}</td>
                        <td><strong>{rf?.pr_auc_average_precision?.toFixed(4)}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+0.0289)</td>
                      </tr>
                      <tr>
                        <td><strong>Gini Coefficient (2×AUC − 1)</strong></td>
                        <td>{lr?.gini_coefficient_2auc_minus_1?.toFixed(4)}</td>
                        <td><strong>{rf?.gini_coefficient_2auc_minus_1?.toFixed(4)}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (+0.0538)</td>
                      </tr>
                      <tr>
                        <td><strong>False Positive Rate (Genuine)</strong></td>
                        <td>{lr?.false_positive_rate_on_synthetic_genuine ? (lr.false_positive_rate_on_synthetic_genuine * 100).toFixed(2) + '%' : '—'}</td>
                        <td><strong>{rf?.false_positive_rate_on_synthetic_genuine ? (rf.false_positive_rate_on_synthetic_genuine * 100).toFixed(2) + '%' : '—'}</strong></td>
                        <td style={{ color: '#047857', fontWeight: 600 }}>Random Forest (8.60% vs 9.10%)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="glass-card result-card">
                <h2 className="card-title">Confusion Matrices (Test Set, N = 6,000)</h2>
                <div className="confusion-matrix-grid">
                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
                    <h3 style={{ fontSize: '1rem', marginBottom: '4px', color: '#1e1b4b', fontWeight: 700 }}>Logistic Regression</h3>
                    <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '12px' }}>Threshold: 0.6800</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', textAlign: 'center' }}>
                      <div style={{ background: '#ecfdf5', border: '1.5px solid #6ee7b7', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#065f46' }}>{lr?.confusion_matrix_labels_0_then_1?.tn}</div>
                        <div style={{ fontSize: '0.75rem', color: '#047857' }}>True Negative (TN)</div>
                      </div>
                      <div style={{ background: '#fef2f2', border: '1.5px solid #fca5a5', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#991b1b' }}>{lr?.confusion_matrix_labels_0_then_1?.fp}</div>
                        <div style={{ fontSize: '0.75rem', color: '#b91c1c' }}>False Positive (FP)</div>
                      </div>
                      <div style={{ background: '#fffbeb', border: '1.5px solid #fcd34d', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#92400e' }}>{lr?.confusion_matrix_labels_0_then_1?.fn}</div>
                        <div style={{ fontSize: '0.75rem', color: '#b45309' }}>False Negative (FN)</div>
                      </div>
                      <div style={{ background: '#eff6ff', border: '1.5px solid #93c5fd', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1e40af' }}>{lr?.confusion_matrix_labels_0_then_1?.tp}</div>
                        <div style={{ fontSize: '0.75rem', color: '#1d4ed8' }}>True Positive (TP)</div>
                      </div>
                    </div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
                    <h3 style={{ fontSize: '1rem', marginBottom: '4px', color: '#1e1b4b', fontWeight: 700 }}>Random Forest (Selected)</h3>
                    <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '12px' }}>Threshold: 0.4100</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', textAlign: 'center' }}>
                      <div style={{ background: '#ecfdf5', border: '1.5px solid #6ee7b7', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#065f46' }}>{rf?.confusion_matrix_labels_0_then_1?.tn}</div>
                        <div style={{ fontSize: '0.75rem', color: '#047857' }}>True Negative (TN)</div>
                      </div>
                      <div style={{ background: '#fef2f2', border: '1.5px solid #fca5a5', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#991b1b' }}>{rf?.confusion_matrix_labels_0_then_1?.fp}</div>
                        <div style={{ fontSize: '0.75rem', color: '#b91c1c' }}>False Positive (FP)</div>
                      </div>
                      <div style={{ background: '#fffbeb', border: '1.5px solid #fcd34d', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#92400e' }}>{rf?.confusion_matrix_labels_0_then_1?.fn}</div>
                        <div style={{ fontSize: '0.75rem', color: '#b45309' }}>False Negative (FN)</div>
                      </div>
                      <div style={{ background: '#eff6ff', border: '1.5px solid #93c5fd', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1e40af' }}>{rf?.confusion_matrix_labels_0_then_1?.tp}</div>
                        <div style={{ fontSize: '0.75rem', color: '#1d4ed8' }}>True Positive (TP)</div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <section className="glass-card result-card">
                <h2 className="card-title">Scientific Rationale &amp; Selection Criteria</h2>
                <div className="explanation-text" style={{ fontSize: '0.9rem', lineHeight: '1.6', color: '#334155' }}>
                  <p><strong>Common Feature Set:</strong> Both pipelines consume identical features: <code>msrp_to_30d_avg</code>, <code>ratio_to_30d_avg</code>, <code>price_volatility_30d</code>, <code>recent_7d_surge</code>, <code>advertised_discount_pct</code>, <code>platform</code>, and <code>category</code>.</p>
                  <p style={{ marginTop: '8px' }}><strong>Leakage Prevention:</strong> Preprocessing pipelines (median imputation, one-hot encoding, and standard scaling) were fit strictly on the 28,000-row training split.</p>
                  <p style={{ marginTop: '8px' }}><strong>Validation Selection:</strong> Model and decision thresholds were selected exclusively on the 6,000-row validation split under the rule of maximizing recall subject to false-positive rate &le; 10% on genuine discounts.</p>
                  <p style={{ marginTop: '8px' }}><strong>Why Random Forest Won:</strong> Random Forest achieved superior performance across all discrimination metrics on the held-out test split: Recall 0.7360 (vs 0.6670), F1 0.8079 (vs 0.7588), ROC-AUC 0.9160 (vs 0.8891), PR-AUC 0.9308 (vs 0.9019), and Gini 0.8320 (vs 0.7782), with a lower false positive rate of 8.60% (vs 9.10%).</p>
                </div>
              </section>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}


/** Root App Component */
function App() {
  const [currentView, setCurrentView] = useState(() => {
    if (typeof window !== 'undefined' && window.location.hash === '#inspector') {
      return 'inspector'
    }
    return 'landing'
  })

  const navigateTo = (view, sectionId) => {
    if (view === 'model-comparison') view = 'landing'
    setCurrentView(view)
    if (view === 'inspector') {
      if (typeof window !== 'undefined') window.location.hash = '#inspector'
    } else {
      if (typeof window !== 'undefined' && window.location.hash === '#inspector') {
        window.location.hash = ''
      }
    }
    if (view === 'landing' && sectionId) {
      setTimeout(() => {
        const elem = document.getElementById(sectionId)
        if (elem) {
          elem.scrollIntoView({ behavior: 'smooth' })
        }
      }, 50)
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <div className="app">
      <Navbar
        onHome={() => navigateTo('landing', 'home')}
        onFeatures={() => navigateTo('landing', 'features')}
        onHowItWorks={() => navigateTo('landing', 'how-it-works')}
        onInspect={() => navigateTo('inspector')}
        isFintech={true}
      />

      {currentView === 'landing' && (
        <LandingPage
          onInspect={() => navigateTo('inspector')}
          onFeatures={() => navigateTo('landing', 'features')}
        />
      )}

      {currentView === 'inspector' && (
        <DatasetProductInspector
          onBack={() => navigateTo('landing')}
        />
      )}

      <Footer
        onHome={() => navigateTo('landing', 'home')}
        onFeatures={() => navigateTo('landing', 'features')}
        onHowItWorks={() => navigateTo('landing', 'how-it-works')}
        onInspect={() => navigateTo('inspector')}
        isFintech={true}
      />
    </div>
  )
}

export default App
