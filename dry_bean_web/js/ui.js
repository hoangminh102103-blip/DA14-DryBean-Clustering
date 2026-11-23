/**
 * =========================================================================
 * ui.js — CẬP NHẬT UI KPI, INSPECTOR 16 SỐ ĐO, 6 MÀN HÌNH & DATA ADAPTER
 * =========================================================================
 */
function updateKpiAndInspectorUI() {
  const m = state.metrics;
  document.getElementById('kpiAriKm').textContent = m.kmeansARI.toFixed(3);
  document.getElementById('kpiAriMed').textContent = m.kmedoidsARI.toFixed(3);
  document.getElementById('kpiSilhouette').textContent = m.kmedoidsSil.toFixed(3);
  document.getElementById('kpiCentroidShift').textContent = `${m.centroidShift.toFixed(2)} σ`;
  document.getElementById('kpiConfigText').textContent = `k=${state.k} · ${state.pcaDims}D · ${state.standardized ? 'Scaled' : 'Raw'}`;

  document.getElementById('footKmStatus').textContent = `ARI = ${m.kmeansARI.toFixed(3)}`;
  document.getElementById('footMedStatus').textContent = `ARI = ${m.kmedoidsARI.toFixed(3)}`;

  const kmCard = document.getElementById('kpiCardKmeans');
  const medCard = document.getElementById('kpiCardKmedoids');
  const shiftCard = document.getElementById('kpiCardShift');
  const dKmEl = document.getElementById('kpiDeltaKm');
  const dMedEl = document.getElementById('kpiDeltaMed');

  if (state.outliersInjected) {
    const dKm = m.kmeansARI - m.baselineClean.kmeansARI;
    const dMed = m.kmedoidsARI - m.baselineClean.kmedoidsARI;

    kmCard.classList.add('highlight-danger');
    medCard.classList.add('highlight-safe');
    shiftCard.classList.add('highlight-danger');

    dKmEl.style.display = 'inline-block';
    dKmEl.style.background = '#F8C8B8';
    dKmEl.style.color = '#991B1B';
    dKmEl.textContent = `${dKm >= 0 ? '+' : ''}${dKm.toFixed(3)}`;

    dMedEl.style.display = 'inline-block';
    dMedEl.style.background = '#D9F2C6';
    dMedEl.style.color = '#065F46';
    dMedEl.textContent = `${dMed >= 0 ? '+' : ''}${dMed.toFixed(3)}`;
  } else {
    kmCard.classList.remove('highlight-danger');
    medCard.classList.remove('highlight-safe');
    shiftCard.classList.remove('highlight-danger');
    dKmEl.style.display = 'none';
    dMedEl.style.display = 'none';
  }

  const cIdx = state.selectedMedoidCluster;
  const beanIdx = state.kmedoidIndices[cIdx];
  const bean = beansData[beanIdx];
  if (!bean) return;

  const beanCode = `#Bean_${String(bean.id).padStart(5, '0')}`;
  document.getElementById('medoidActiveTag').textContent = `M${cIdx + 1}`;
  document.getElementById('footSelectedMedoid').textContent = `M${cIdx + 1} (${beanCode})`;
  document.getElementById('medoidMetaBanner').innerHTML = `
    Hạt thật: <strong>${beanCode}</strong> · Giống: <strong>${bean.varietyLabel}</strong>
    <span style="display:block; font-size:10px; color:var(--ink-muted);">Tọa độ chiếu: PC1=${bean.pcCurrent[0].toFixed(2)}, PC2=${bean.pcCurrent[1].toFixed(2)}</span>
  `;

  const pillsWrap = document.getElementById('medoidQuickPills');
  pillsWrap.innerHTML = '';
  for (let i = 0; i < state.k; i++) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `medoid-select-pill ${i === cIdx ? 'active' : ''}`;
    btn.textContent = `M${i + 1}`;
    btn.onclick = () => {
      state.selectedMedoidCluster = i;
      updateKpiAndInspectorUI();
      drawScatterCanvas(canvasKMedoids, ctxKMedoids, 'kmedoids');
    };
    pillsWrap.appendChild(btn);
  }

  const featGrid = document.getElementById('medoidFeaturesGrid');
  featGrid.innerHTML = FEATURE_META.map(f => {
    const val = bean.features[f.key];
    const formatted = val >= 100 ? val.toFixed(1) : (val >= 1 ? val.toFixed(3) : val.toFixed(5));
    return `
      <div class="feat-cell">
        <span class="feat-name">${f.key}</span>
        <span class="feat-val">${formatted}</span>
      </div>
    `;
  }).join('');
}

function syncControlsFromState() {
  document.getElementById('sliderK').value = state.k;
  document.getElementById('badgeK').textContent = `k = ${state.k}`;

  document.getElementById('sliderPCA').value = state.pcaDims;
  let cum = 0;
  for (let i = 0; i < state.pcaDims; i++) cum += PCA_VARIANCE_RATIO[i] * 100;
  document.getElementById('badgePCA').textContent = `d = ${state.pcaDims} (${cum.toFixed(1)}%)`;

  const stdPill = document.getElementById('stdPillBadge');
  const stdSub = document.getElementById('stdSubLabel');
  if (state.standardized) {
    stdPill.textContent = 'BẬT';
    stdPill.className = 'switch-pill bg-mint';
    stdSub.textContent = 'Cân bằng kích thước & hình dáng';
  } else {
    stdPill.textContent = 'TẮT';
    stdPill.className = 'switch-pill bg-coral';
    stdSub.textContent = 'Cảnh báo: Chỉ còn phân lớp theo Area!';
  }

  const btnQuickOut = document.getElementById('btnQuickOutlier');
  const btnSideOut = document.getElementById('btnSidebarOutlier');
  if (state.outliersInjected) {
    btnQuickOut.classList.add('active-outlier');
    btnQuickOut.textContent = '⚡ Đang tiêm ngoại lai 1% (Tắt)';
    btnSideOut.classList.add('active-outlier');
    btnSideOut.textContent = '⚡ Đang tiêm 1% (Bấm để khôi phục)';
  } else {
    btnQuickOut.classList.remove('active-outlier');
    btnQuickOut.textContent = '⚡ Tiêm ngoại lai 1%';
    btnSideOut.classList.remove('active-outlier');
    btnSideOut.textContent = '⚡ Tiêm ngoại lai vào 1% hạt (136 hạt)';
  }

  renderVarietyPills();
}

function renderVarietyPills() {
  const container = document.getElementById('varietyLegendPills');
  container.innerHTML = '';
  VARIETIES.forEach(v => {
    const btn = document.createElement('button');
    btn.type = 'button';
    let cls = 'variety-btn';
    if (state.selectedVariety === v.key) cls += ' active';
    else if (state.selectedVariety) cls += ' dimmed';
    btn.className = cls;
    btn.innerHTML = `<span class="color-dot" style="background:${v.color};"></span><span>${v.label}</span><span style="opacity:0.75;">(${v.count.toLocaleString('vi-VN')})</span>`;
    btn.onclick = () => {
      state.selectedVariety = state.selectedVariety === v.key ? null : v.key;
      renderVarietyPills();
      renderBothScatterCanvases();
    };
    container.appendChild(btn);
  });
}

function buildTimelineSteps() {
  const wrap = document.getElementById('timelineStepsContainer');
  wrap.innerHTML = GUIDED_EXPERIMENTS.map(item => `
    <button class="step-node-btn ${item.step === state.guidedStep ? 'active' : ''}" data-step="${item.step}" type="button" onclick="activateGuidedStep(${item.step})">
      <span class="step-circle">${item.step}</span>
      <span class="step-label">${item.shortLabel}</span>
    </button>
  `).join('');
}

window.activateGuidedStep = function (stepNum) {
  const found = GUIDED_EXPERIMENTS.find(g => g.step === stepNum);
  if (!found) return;
  state.guidedStep = stepNum;
  found.apply();

  document.getElementById('timelineStepCounter').textContent = `Bước ${stepNum} / 6`;
  document.getElementById('rightStepLabel').textContent = `THÍ NGHIỆM ${stepNum} / 6`;
  const badge = document.getElementById('rightStepBadge');
  badge.textContent = found.badge;
  badge.className = `pastel-badge ${found.badgeClass}`;
  document.getElementById('rightStepTitle').textContent = found.title;
  document.getElementById('rightStepDesc').textContent = found.desc;
  document.getElementById('rightKeyIdea').textContent = found.keyIdea;

  document.querySelectorAll('.step-node-btn').forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.step) === stepNum);
  });

  if (state.activeScreen !== 6) switchScreen(6);
  recomputeAll(true);
};

function initScreen1Content() {
  const wrap = document.getElementById('screen1VarietyBars');
  wrap.innerHTML = VARIETIES.map(v => {
    const pct = ((v.count / TOTAL_BEANS) * 100).toFixed(1);
    return `
      <div style="display:grid; grid-template-columns: 110px 1fr 110px; align-items:center; gap:10px; font-size:11.5px;">
        <span style="font-weight:700;">${v.label}</span>
        <div style="height:12px; background:var(--bg-paper); border:1.5px solid var(--ink); border-radius:4px; overflow:hidden;">
          <div style="height:100%; width:${pct}%; background:${v.color};"></div>
        </div>
        <span class="tabular" style="text-align:right;">${v.count.toLocaleString('vi-VN')} (${pct}%)</span>
      </div>
    `;
  }).join('');
}

function initScreen2Content() {
  const sel = document.getElementById('edaSelectFeature');
  sel.innerHTML = FEATURE_META.map(f => `<option value="${f.key}">${f.key} (${f.group})</option>`).join('');
  sel.onchange = (e) => { state.edaFeature = e.target.value; drawEdaBoxplot(); };

  document.getElementById('btnToggleEdaZscore').onclick = (e) => {
    state.edaZscore = !state.edaZscore;
    e.target.textContent = state.edaZscore ? 'Thang đo: Chuẩn hóa (Z-score)' : 'Thang đo: Giá trị gốc (Raw)';
    drawEdaBoxplot();
  };

  const tbody = document.getElementById('edaDictionaryTableBody');
  tbody.innerHTML = FEATURE_META.map((f, idx) => {
    const st = featureStats[f.key];
    const fmt = (x) => x >= 100 ? x.toFixed(1) : (x >= 1 ? x.toFixed(3) : x.toFixed(5));
    return `
      <tr style="cursor:pointer;" onclick="document.getElementById('edaSelectFeature').value='${f.key}'; state.edaFeature='${f.key}'; drawEdaBoxplot();">
        <td>${idx + 1}</td>
        <td><strong>${f.key}</strong></td>
        <td>${f.group}</td>
        <td>${f.desc}</td>
        <td class="tabular">${fmt(st.mean)}</td>
        <td class="tabular">${fmt(st.std)}</td>
      </tr>
    `;
  }).join('');
}

function initScreen4Mechanism() {
  document.getElementById('btnMechToggleOutlier').onclick = (e) => {
    state.mechOutlier = !state.mechOutlier;
    e.target.classList.toggle('active-outlier', state.mechOutlier);
    e.target.textContent = state.mechOutlier ? '⚡ Ngoại lai: ĐANG BẬT' : '⚡ Ngoại lai: ĐÃ TẮT';
    drawMechanismDemoCanvas();
  };
  document.getElementById('btnMechNextIter').onclick = () => {
    state.mechIter = (state.mechIter + 1) % 4;
    drawMechanismDemoCanvas();
  };
}

window.selectExpDim = function (dim) {
  state.expDim = dim;
  document.querySelectorAll('.exp-dim-btn').forEach(b => {
    b.classList.toggle('mint', Number(b.dataset.dim) === dim);
  });
  renderBenchmarkTable();
};

function renderBenchmarkTable() {
  const rows = BENCHMARK_DATA[state.expDim] || BENCHMARK_DATA[2];
  document.getElementById('benchmarkTableBody').innerHTML = rows.map(r => `
    <tr class="${r.k === 7 ? 'row-highlight' : ''}">
      <td style="text-align:center; font-weight:700;">${r.k}</td>
      <td>${r.cMed}</td>
      <td>${r.cKm}</td>
      <td>${r.cSil}</td>
      <td>${r.cTime}</td>
      <td>${r.oMed}</td>
      <td class="delta-bad">${r.oKm}</td>
      <td>${r.oSil}</td>
      <td>${r.oTime}</td>
      <td class="delta-good">${r.dMed.toFixed(3)}</td>
      <td class="delta-bad">${r.dKm.toFixed(3)}</td>
    </tr>
  `).join('');
}

window.copyBenchmarkMarkdown = function () {
  const rows = BENCHMARK_DATA[state.expDim];
  let md = `| k | ARI Medoids (Sạch) | ARI K-Means (Sạch) | Silhouette | Time (s) | ARI Medoids (1% Ngoại lai) | ARI K-Means (1% Ngoại lai) | Δ Medoids | Δ K-Means |\n|---|---|---|---|---|---|---|---|---|\n`;
  rows.forEach(r => {
    md += `| ${r.k} | ${r.cMed} | ${r.cKm} | ${r.cSil} | ${r.cTime} | ${r.oMed} | ${r.oKm} | ${r.dMed.toFixed(3)} | ${r.dKm.toFixed(3)} |\n`;
  });
  copyRawString(md, 'btnCopyBenchmarkMd', '⎘ Chép bảng Markdown');
};

window.copyTextToClipboard = function (elementId, btnId, defaultLabel) {
  const txt = document.getElementById(elementId).innerText;
  copyRawString(txt, btnId, defaultLabel);
};

function copyRawString(text, btnId, defaultLabel) {
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);

  const btn = document.getElementById(btnId);
  if (btn) {
    btn.textContent = '✓ Đã sao chép!';
    setTimeout(() => { btn.textContent = defaultLabel; }, 1600);
  }
}

window.switchScreen = function (num) {
  state.activeScreen = Number(num);

  document.querySelectorAll('.screen-view').forEach(v => v.classList.remove('active'));
  const targetView = document.getElementById(`view-screen-${state.activeScreen}`);
  if (targetView) targetView.classList.add('active');

  document.querySelectorAll('.screen-nav-item').forEach(item => {
    item.classList.toggle('active', Number(item.dataset.screen) === state.activeScreen);
  });

  document.getElementById('sidebarProgressText').textContent = `${state.activeScreen} / 6`;
  document.getElementById('sidebarProgressFill').style.width = `${(state.activeScreen / 6) * 100}%`;

  document.querySelectorAll('.top-tab').forEach(t => t.classList.remove('active'));
  if (state.activeScreen === 6) document.querySelector('[data-quick-tab="lab"]').classList.add('active');
  else if (state.activeScreen === 5) document.querySelector('[data-quick-tab="benchmark"]').classList.add('active');
  else if (state.activeScreen === 1) document.querySelector('[data-quick-tab="readme"]').classList.add('active');
  else document.querySelector('[data-quick-tab="screens"]').classList.add('active');

  document.getElementById('leftSidebar').classList.remove('mobile-open');

  if (state.activeScreen === 2) drawEdaBoxplot();
  if (state.activeScreen === 3) drawPcaScreeChart();
  if (state.activeScreen === 4) drawMechanismDemoCanvas();
  if (state.activeScreen === 6) {
    renderBothScatterCanvases();
    drawMetricsCurveChart();
  }
};

window.handleTopTab = function (tabKey) {
  if (tabKey === 'lab') switchScreen(6);
  else if (tabKey === 'screens') switchScreen(state.activeScreen === 6 ? 2 : state.activeScreen);
  else if (tabKey === 'benchmark') switchScreen(5);
  else if (tabKey === 'readme') switchScreen(1);
};

window.DA14_DATA_ADAPTER = {
  getState: () => state,
  getBeans: () => beansData,
  loadFromResults(jsonData) {
    if (!jsonData || typeof jsonData !== 'object') return;
    if (Array.isArray(jsonData.beans) && jsonData.beans.length > 0) {
      beansData = jsonData.beans.map((item, idx) => ({
        id: item.id ?? idx,
        variety: item.variety,
        varietyLabel: item.varietyLabel || item.variety,
        varietyIndex: Math.max(0, VARIETIES.findIndex(v => v.key === item.variety)),
        isOutlier: false,
        isOutlierCandidate: idx % 100 === 0,
        features: item.features,
        stdFeatures: new Float64Array(item.stdFeatures || 16),
        rawFeaturesArr: new Float64Array(FEATURE_META.map(f => item.features[f.key])),
        pcClean: new Float64Array(item.pc),
        pcCurrent: new Float64Array(item.pc)
      }));
      recomputeAll(false);
    }
    if (jsonData.benchmarkTable) {
      Object.assign(BENCHMARK_DATA, jsonData.benchmarkTable);
      renderBenchmarkTable();
    }
  }
};
