/**
 * =========================================================================
 * canvas-charts.js — ĐỒ THỊ 3 ĐƯỜNG THEO k, BOXPLOT EDA, SCREE PCA & MÀN 04
 * =========================================================================
 */
const canvasCurve = document.getElementById('canvasMetricsCurve');
const ctxCurve = canvasCurve.getContext('2d');

function drawMetricsCurveChart() {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvasCurve.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  if (canvasCurve.width !== Math.round(rect.width * dpr) || canvasCurve.height !== Math.round(rect.height * dpr)) {
    canvasCurve.width = Math.round(rect.width * dpr);
    canvasCurve.height = Math.round(rect.height * dpr);
  }

  const w = rect.width, h = rect.height;
  const padL = 44, padR = 20, padT = 18, padB = 28;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  ctxCurve.save();
  ctxCurve.scale(dpr, dpr);
  ctxCurve.clearRect(0, 0, w, h);

  const yMax = 0.85;
  ctxCurve.font = '10px "JetBrains Mono", monospace';
  for (let v = 0; v <= 0.8; v += 0.2) {
    const py = padT + plotH * (1 - v / yMax);
    ctxCurve.strokeStyle = '#E6E2D8';
    ctxCurve.lineWidth = 1;
    ctxCurve.beginPath();
    ctxCurve.moveTo(padL, py);
    ctxCurve.lineTo(w - padR, py);
    ctxCurve.stroke();

    ctxCurve.fillStyle = '#888880';
    ctxCurve.textAlign = 'right';
    ctxCurve.fillText(v.toFixed(1), padL - 6, py + 3);
  }

  const getX = (kVal) => padL + ((kVal - 2) / 8) * plotW;
  const getY = (val) => padT + plotH * (1 - Math.max(0, Math.min(yMax, val)) / yMax);

  const activeX = getX(state.k);
  ctxCurve.save();
  ctxCurve.strokeStyle = '#1E201E';
  ctxCurve.lineWidth = 1.5;
  ctxCurve.setLineDash([4, 3]);
  ctxCurve.beginPath();
  ctxCurve.moveTo(activeX, padT);
  ctxCurve.lineTo(activeX, padT + plotH);
  ctxCurve.stroke();
  ctxCurve.restore();

  for (let kVal = 2; kVal <= 10; kVal++) {
    const px = getX(kVal);
    ctxCurve.fillStyle = kVal === state.k ? '#1E201E' : '#888880';
    ctxCurve.font = kVal === state.k ? '700 11px "JetBrains Mono", monospace' : '10px "JetBrains Mono", monospace';
    ctxCurve.textAlign = 'center';
    ctxCurve.fillText(`k=${kVal}`, px, h - 8);
  }

  if (state.curveByK.length > 0) {
    drawCurveSeries(ctxCurve, state.curveByK, 'silhouette', getX, getY, '#D97706', true, 'diamond');
    drawCurveSeries(ctxCurve, state.curveByK, 'ariKMeans', getX, getY, '#2563EB', false, 'square');
    drawCurveSeries(ctxCurve, state.curveByK, 'ariMedoids', getX, getY, '#0F766E', false, 'circle');
  }

  ctxCurve.restore();
}

function drawCurveSeries(ctx, data, key, getX, getY, color, dashed, shape) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.2;
  if (dashed) ctx.setLineDash([5, 4]);

  ctx.beginPath();
  data.forEach((pt, idx) => {
    const x = getX(pt.k), y = getY(pt[key]);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.setLineDash([]);

  data.forEach(pt => {
    const x = getX(pt.k), y = getY(pt[key]);
    const r = (pt.k === state.k || pt.k === state.hoveredCurveK) ? 5 : 3.5;
    ctx.fillStyle = color;
    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    if (shape === 'circle') ctx.arc(x, y, r, 0, Math.PI * 2);
    else if (shape === 'square') ctx.rect(x - r, y - r, r * 2, r * 2);
    else {
      ctx.moveTo(x, y - r - 1);
      ctx.lineTo(x + r + 1, y);
      ctx.lineTo(x, y + r + 1);
      ctx.lineTo(x - r - 1, y);
      ctx.closePath();
    }
    ctx.fill();
    ctx.stroke();
  });
  ctx.restore();
}

function bindCurveChartEvents() {
  canvasCurve.addEventListener('pointermove', (e) => {
    const rect = canvasCurve.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const padL = 44, padR = 20;
    const plotW = rect.width - padL - padR;
    const nearestK = Math.round(2 + ((mx - padL) / plotW) * 8);
    const tooltip = document.getElementById('curveTooltip');

    if (nearestK >= 2 && nearestK <= 10 && state.curveByK.length > 0) {
      state.hoveredCurveK = nearestK;
      const item = state.curveByK.find(d => d.k === nearestK);
      if (item) {
        tooltip.style.display = 'block';
        tooltip.innerHTML = `
          <div style="font-weight:700; border-bottom:1px solid #575852; padding-bottom:3px; margin-bottom:3px;">Mốc k = ${item.k}</div>
          <div style="color:#6EE7B7;">ARI K-Medoids: ${item.ariMedoids.toFixed(3)}</div>
          <div style="color:#93C5FD;">ARI K-Means  : ${item.ariKMeans.toFixed(3)}</div>
          <div style="color:#FDE68A;">Silhouette   : ${item.silhouette.toFixed(3)}</div>
        `;
        tooltip.style.left = `${Math.min(rect.width - 175, Math.max(10, mx + 10))}px`;
        tooltip.style.top = `10px`;
      }
      drawMetricsCurveChart();
    } else {
      tooltip.style.display = 'none';
    }
  });

  canvasCurve.addEventListener('pointerleave', () => {
    state.hoveredCurveK = null;
    document.getElementById('curveTooltip').style.display = 'none';
    drawMetricsCurveChart();
  });

  canvasCurve.addEventListener('click', () => {
    if (state.hoveredCurveK && state.hoveredCurveK !== state.k) {
      state.k = state.hoveredCurveK;
      recomputeAll(true);
    }
  });
}

function drawEdaBoxplot() {
  const canvas = document.getElementById('canvasEdaBoxplot');
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const w = rect.width, h = rect.height;
  const padL = 68, padR = 20, padT = 18, padB = 34;
  const plotW = w - padL - padR, plotH = h - padT - padB;

  const meta = FEATURE_META.find(f => f.key === state.edaFeature);
  const st = featureStats[state.edaFeature];
  document.getElementById('edaBoxTitle').textContent = `Biểu đồ hộp (Q1–Median–Q3) của ${meta.key} trên 7 giống đậu`;
  document.getElementById('edaBoxUnit').textContent = state.edaZscore ? 'Đơn vị: Z-score (σ)' : `Đơn vị: ${meta.unit}`;

  ctx.fillStyle = '#F9F7F2';
  ctx.fillRect(0, 0, w, h);

  const statsByVar = VARIETIES.map(v => {
    const vals = [];
    for (let i = 0; i < beansData.length; i++) {
      if (beansData[i].variety === v.key) {
        let val = beansData[i].features[state.edaFeature];
        if (state.edaZscore) val = (val - st.mean) / st.std;
        vals.push(val);
      }
    }
    vals.sort((a, b) => a - b);
    const q = (p) => vals[Math.floor(p * (vals.length - 1))];
    return { v, min: q(0.02), q1: q(0.25), med: q(0.5), q3: q(0.75), max: q(0.98) };
  });

  const gMin = Math.min(...statsByVar.map(s => s.min));
  const gMax = Math.max(...statsByVar.map(s => s.max));
  const span = (gMax - gMin) || 1;
  const toY = (val) => padT + plotH * (1 - (val - gMin) / span);

  ctx.font = '10px "JetBrains Mono", monospace';
  for (let i = 0; i <= 4; i++) {
    const val = gMin + (i / 4) * span;
    const y = toY(val);
    ctx.strokeStyle = '#E6E2D8';
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();

    ctx.fillStyle = '#575852';
    ctx.textAlign = 'right';
    ctx.fillText(Math.abs(val) >= 100 ? Math.round(val).toLocaleString('vi-VN') : val.toFixed(2), padL - 6, y + 3);
  }

  const colW = plotW / VARIETIES.length;
  statsByVar.forEach((s, idx) => {
    const cx = padL + colW * (idx + 0.5);
    const bw = Math.min(36, colW * 0.48);

    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(cx, toY(s.min));
    ctx.lineTo(cx, toY(s.max));
    ctx.stroke();

    const yTop = toY(s.q3), yBot = toY(s.q1);
    ctx.fillStyle = s.v.color + '44';
    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(cx - bw / 2, yTop, bw, Math.max(4, yBot - yTop), 4);
    ctx.fill();
    ctx.stroke();

    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(cx - bw / 2, toY(s.med));
    ctx.lineTo(cx + bw / 2, toY(s.med));
    ctx.stroke();

    ctx.fillStyle = '#1E201E';
    ctx.font = '700 10.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(s.v.label, cx, h - 10);
  });
}

function drawPcaScreeChart() {
  const canvas = document.getElementById('canvasPcaScree');
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const w = rect.width, h = rect.height;
  const padL = 44, padR = 18, padT = 18, padB = 30;
  const plotW = w - padL - padR, plotH = h - padT - padB;

  ctx.fillStyle = '#F9F7F2';
  ctx.fillRect(0, 0, w, h);

  ctx.font = '10px "JetBrains Mono", monospace';
  for (let pct = 0; pct <= 100; pct += 25) {
    const y = padT + plotH * (1 - pct / 100);
    ctx.strokeStyle = '#E6E2D8';
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();

    ctx.fillStyle = '#575852';
    ctx.textAlign = 'right';
    ctx.fillText(`${pct}%`, padL - 6, y + 3);
  }

  const stepW = plotW / 16;
  let cum = 0;
  const pts = [];

  PCA_VARIANCE_RATIO.forEach((r, idx) => {
    const pct = r * 100;
    cum += pct;
    const cx = padL + stepW * (idx + 0.5);
    const bw = stepW * 0.54;
    const bh = (pct / 100) * plotH;

    ctx.fillStyle = idx < 2 ? '#D9F2C6' : '#E6E2D8';
    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.3;
    ctx.beginPath();
    ctx.rect(cx - bw / 2, padT + plotH - bh, bw, bh);
    ctx.fill();
    ctx.stroke();

    pts.push({ x: cx, y: padT + plotH * (1 - cum / 100) });

    ctx.fillStyle = '#1E201E';
    ctx.textAlign = 'center';
    ctx.fillText(`PC${idx + 1}`, cx, h - 10);
  });

  ctx.strokeStyle = '#2563EB';
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  pts.forEach((p, idx) => idx === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
  ctx.stroke();

  pts.forEach((p, idx) => {
    ctx.fillStyle = idx === 1 ? '#FDF3C7' : '#FAF9F5';
    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(p.x, p.y, idx === 1 ? 5 : 3.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  });
}

function drawMechanismDemoCanvas() {
  const canvas = document.getElementById('canvasMechanismDemo');
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const w = rect.width, h = rect.height;
  ctx.fillStyle = '#F9F7F2';
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = '#E6E2D8';
  for (let x = 0; x < w; x += 28) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
  for (let y = 0; y < h; y += 28) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

  const basePts = [
    [0.22, 0.42], [0.25, 0.34], [0.28, 0.48], [0.24, 0.56], [0.30, 0.39],
    [0.32, 0.52], [0.27, 0.62], [0.35, 0.45], [0.20, 0.49], [0.33, 0.33],
    [0.29, 0.45], [0.26, 0.43], [0.31, 0.58], [0.23, 0.39]
  ];
  const outlierPt = [0.88, 0.36];
  const medoidPt = basePts[10];

  const factor = state.mechOutlier ? [0, 0.35, 0.72, 1.0][state.mechIter] : 0;
  const allPts = state.mechOutlier ? [...basePts, outlierPt] : basePts;
  let sumX = 0, sumY = 0;
  basePts.forEach(p => { sumX += p[0]; sumY += p[1]; });
  const cleanMeanX = sumX / basePts.length;
  const cleanMeanY = sumY / basePts.length;

  const fullMeanX = (sumX + (state.mechOutlier ? outlierPt[0] : 0)) / allPts.length;
  const fullMeanY = (sumY + (state.mechOutlier ? outlierPt[1] : 0)) / allPts.length;

  const kmX = (cleanMeanX + (fullMeanX - cleanMeanX) * factor) * w;
  const kmY = (cleanMeanY + (fullMeanY - cleanMeanY) * factor) * h;

  if (state.mechOutlier) {
    ctx.save();
    ctx.strokeStyle = '#DC2626';
    ctx.lineWidth = 1.6;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(outlierPt[0] * w, outlierPt[1] * h);
    ctx.lineTo(kmX, kmY);
    ctx.stroke();
    ctx.restore();
  }

  basePts.forEach((p, idx) => {
    const px = p[0] * w, py = p[1] * h;
    ctx.beginPath();
    ctx.ellipse(px, py, 7, 4.8, -0.3, 0, Math.PI * 2);
    ctx.fillStyle = idx === 10 ? '#D9F2C6' : '#93C5FD';
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#1E201E';
    ctx.stroke();
  });

  if (state.mechOutlier) {
    const ox = outlierPt[0] * w, oy = outlierPt[1] * h;
    ctx.beginPath();
    ctx.ellipse(ox, oy, 13, 8.5, -0.3, 0, Math.PI * 2);
    ctx.fillStyle = '#F8C8B8';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#DC2626';
    ctx.stroke();

    ctx.fillStyle = '#1E201E';
    ctx.font = '700 11px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Hạt ngoại lai (×10 Area)', ox, oy - 16);
  }

  const mx = medoidPt[0] * w, my = medoidPt[1] * h;
  ctx.beginPath();
  ctx.arc(mx, my, 15, 0, Math.PI * 2);
  ctx.strokeStyle = '#0F766E';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = '#0F766E';
  ctx.font = '700 11px "JetBrains Mono", monospace';
  ctx.textAlign = 'center';
  ctx.fillText('◉ Medoid (Đứng yên)', mx, my + 28);

  ctx.strokeStyle = '#DC2626';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(kmX - 9, kmY); ctx.lineTo(kmX + 9, kmY);
  ctx.moveTo(kmX, kmY - 9); ctx.lineTo(kmX, kmY + 9);
  ctx.stroke();

  ctx.fillStyle = '#DC2626';
  ctx.fillText(`+ Tâm K-Means (Bước lặp ${state.mechIter})`, kmX, kmY - 15);
}
