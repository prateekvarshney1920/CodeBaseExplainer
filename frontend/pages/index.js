import React from 'react';
import Link from 'next/link';

const LandingPage = () => {
  const featureStrip = [
    { num: '01', title: 'GitHub URL + file upload', desc: 'Paste any public repo URL or drag-drop your source files directly.' },
    { num: '02', title: 'File tree viewer', desc: 'Navigate your entire project structure with recursive folder expansion.' },
    { num: '03', title: 'Dependency graph', desc: 'Force-directed D3 graph of all imports, modules and their relationships.' },
    { num: '04', title: 'AI file explanation', desc: 'Claude streams a per-file summary covering purpose, exports and functions.' },
  ];

  const mainFeatures = [
    { num: '01', badge: 'React · Tailwind', title: 'GitHub URL input + file upload', desc: 'Paste any public GitHub URL or drag-and-drop your source files. Supports bulk upload with instant file-type detection.' },
    { num: '02', badge: 'Virtualized', title: 'File tree viewer', desc: 'Recursive folder and file tree with expand/collapse, file type icons, keyword search and active file highlighting.' },
    { num: '03', badge: 'D3.js · React Flow', title: 'Dependency graph visualization', desc: 'Force-directed graph of all imports and module relationships. Highlights circular dependencies and lets you click any node to inspect.' },
    { num: '04', badge: 'Claude API', title: 'File explanation panel', desc: 'Select any file to stream an AI summary — purpose, key exports, functions and complexity metrics.' },
  ];

  return (
    <div className="page-container">
      {/* NAV */}
      <nav className="nav">
        <div className="brand-name">codebase<em>.</em>explainer</div>
        <div className="nav-links">
          <a className="nav-link">Features</a>
          <a className="nav-link">Docs</a>
          <Link href="/upload" className="nav-cta text-center">Get started ↗</Link>
        </div>
      </nav>

      {/* HERO */}
      <header className="hero">
        <div className="hero-grid" />
        <div className="hero-inner">
          <h1 className="hero-title">Understand any<br/><em>codebase</em><br/>instantly.</h1>
          <p className="hero-sub">Drop a GitHub URL or upload your files. Get a full dependency graph, file-by-file AI explanations, and an editable prompt interface.</p>
          <div style={{ display: 'flex' }}>
            <Link href="/upload" className="hero-btn solid" style={{ textDecoration: 'none' }}>Start analysing ↗</Link>
            <button className="hero-btn" style={{ borderLeft: 'none' }}>View demo</button>
          </div>
        </div>
      </header>

      {/* FEATURE STRIP */}
      <div className="strip">
        {featureStrip.map(item => (
          <div key={item.num} className="strip-item">
            <div style={{ fontSize: '9px', color: 'var(--color-text-tertiary)', marginBottom: '8px' }}>{item.num}</div>
            <div style={{ fontSize: '11px', marginBottom: '4px' }}>{item.title}</div>
            <p style={{ fontSize: '9px', color: 'var(--color-text-tertiary)' }}>{item.desc}</p>
          </div>
        ))}
      </div>

      {/* MAIN FEATURES GRID */}
      <section style={{ padding: '3.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2.5rem' }}>
          <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '2rem', fontWeight: 300 }}>What's <em>inside</em></h2>
          <span style={{ fontSize: '9px', color: 'var(--color-text-tertiary)', letterSpacing: '0.14em' }}>5 CORE FEATURES</span>
        </div>
        <div className="feature-grid">
          {mainFeatures.map(feat => (
            <div key={feat.num} className="feat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '9px', border: '0.5px solid var(--color-border-tertiary)', padding: '0 5px' }}>{feat.num}</span>
                <span className="feat-badge">{feat.badge}</span>
              </div>
              <div style={{ fontSize: '12px', marginBottom: '8px' }}>{feat.title}</div>
              <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', lineHeight: '1.8' }}>{feat.desc}</p>
            </div>
          ))}
          {/* Bento-style span for the final feature */}
          <div className="feat-card" style={{ gridColumn: '1 / -1', borderBottom: 'none' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '9px', border: '0.5px solid var(--color-border-tertiary)', padding: '0 5px' }}>05</span>
              <span className="feat-badge" style={{ borderColor: '#fca5a5', color: '#f87171' }}>Required</span>
            </div>
            <div style={{ fontSize: '12px', marginBottom: '8px' }}>Prompt editor UI</div>
            <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', lineHeight: '1.8' }}>Monaco-powered prompt editor with live variable token insertion, saved presets, and a reviewer annotation sidebar.</p>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div>codebase<em>.</em>viewer</div>
        <div style={{ display: 'flex', gap: '24px' }}>
          <span>GitHub</span>
          <span>Twitter</span>
          <span>Changelog</span>
        </div>
        <div>Built with Claude API · v2.1.0</div>
      </footer>
    </div>
  );
};

export default LandingPage;