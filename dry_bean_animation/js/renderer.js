/**
 * =========================================================================
 * dry_bean_animation/js/renderer.js
 * Bộ vẽ HTML5 Canvas 60fps: nội suy hạt đậu, vòng lặp, lực kéo & biểu đồ kép
 * =========================================================================
 */
window.ANIM_RENDERER = (function () {
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeOutCubic = (t) => 1 - Math.pow(1 - clamp01(t), 3);
  const easeInOutCubic = (t) => {
    const x = clamp01(t);
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  };

  function getCoordDomain(actId) {
    if (actId <= 2) return { xMin: -6.0, xMax: 12.0, yMin: -4.2, yMax: 4.5 };
    return { xMin: -6.5, xMax: 13.5, yMin: -6.0, yMax: 9.2 };
  }

  function mapPoint(px, py, box, domain) {
    const padL = 42, padR = 16, padT = 36, padB = 34;
    const plotW = box.w - padL - padR;
    const plotH = box.h - padT - padB;
    const nx = (px - domain.xMin) / (domain.xMax - domain.xMin);
    const ny = 1 - (py - domain.yMin) / (domain.yMax - domain.yMin);
    return {
      x: box.x + padL + nx * plotW,
      y: box.y + padT + ny * plotH
    };
  }

  function drawPanelFrame(ctx, box, title, subtitle, domain, xAxisText, yAxisText) {
    ctx.save();
    ctx.fillStyle = '#FAF8F3';
    ctx.strokeStyle = '#181A18';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(box.x, box.y, box.w, box.h, 8);
    ctx.fill();
    ctx.stroke();

    // Header strip inside panel
    ctx.fillStyle = '#F4F1EA';
    ctx.beginPath();
    ctx.roundRect(box.x + 1, box.y + 1, box.w - 2, 30, [7, 7, 0, 0]);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(box.x, box.y + 31);
    ctx.lineTo(box.x + box.w, box.y + 31);
    ctx.strokeStyle = '#C9C4B8';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#181A18';
    ctx.font = '700 12.5px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(title, box.x + 12, box.y + 20);

    if (subtitle) {
      ctx.fillStyle = '#464842';
      ctx.font = '600 11px Consolas, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(subtitle, box.x + box.w - 12, box.y + 20);
    }

    // Grid lines
    const padL = 42, padR = 16, padT = 36, padB = 34;
    const xStart = box.x + padL, xEnd = box.x + box.w - padR;
    const yStart = box.y + padT, yEnd = box.y + box.h - padB;

    ctx.beginPath();
    ctx.rect(xStart, yStart, xEnd - xStart, yEnd - yStart);
    ctx.clip();

    ctx.strokeStyle = '#E5E0D5';
    ctx.lineWidth = 1;
    for (let tx = Math.ceil(domain.xMin / 2) * 2; tx <= domain.xMax; tx += 2) {
      const p = mapPoint(tx, 0, box, domain);
      ctx.beginPath();
      ctx.moveTo(p.x, yStart);
      ctx.lineTo(p.x, yEnd);
      ctx.stroke();
    }
    for (let ty = Math.ceil(domain.yMin / 2) * 2; ty <= domain.yMax; ty += 2) {
      const p = mapPoint(0, ty, box, domain);
      ctx.beginPath();
      ctx.moveTo(xStart, p.y);
      ctx.lineTo(xEnd, p.y);
      ctx.stroke();
    }

    // Axes lines
    const origin = mapPoint(0, 0, box, domain);
    ctx.strokeStyle = '#C9C4B8';
    ctx.lineWidth = 1.2;
    if (origin.x >= xStart && origin.x <= xEnd) {
      ctx.beginPath(); ctx.moveTo(origin.x, yStart); ctx.lineTo(origin.x, yEnd); ctx.stroke();
    }
    if (origin.y >= yStart && origin.y <= yEnd) {
      ctx.beginPath(); ctx.moveTo(xStart, origin.y); ctx.lineTo(xEnd, origin.y); ctx.stroke();
    }
    ctx.restore();

    // Axis labels outside clip
    ctx.save();
    ctx.fillStyle = '#464842';
    ctx.font = '600 11px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(xAxisText, box.x + box.w - 14, box.y + box.h - 10);

    ctx.save();
    ctx.translate(box.x + 15, box.y + padT + 8);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'right';
    ctx.fillText(yAxisText, 0, 0);
    ctx.restore();
    ctx.restore();
  }

  function interpolateCenters(frames, floatIdx) {
    const maxIdx = frames.length - 1;
    const clamped = Math.max(0, Math.min(maxIdx, floatIdx));
    const lo = Math.floor(clamped);
    const hi = Math.min(maxIdx, lo + 1);
    const frac = easeInOutCubic(clamped - lo);
    const fLo = frames[lo];
    const fHi = frames[hi];

    const listLo = fLo.centroids || fLo.medoidCoords;
    const listHi = fHi.centroids || fHi.medoidCoords;
    const merged = listLo.map((pt, i) => ({
      x: lerp(pt.x, listHi[i].x, frac),
      y: lerp(pt.y, listHi[i].y, frac),
      beanIdx: listHi[i].beanIdx ?? pt.beanIdx
    }));

    return {
      points: merged,
      assignments: frac > 0.5 ? fHi.assignments : fLo.assignments,
      ari: lerp(fLo.ari, fHi.ari, frac),
      nmi: lerp(fLo.nmi || 0, fHi.nmi || 0, frac),
      purity: lerp(fLo.purity || 0, fHi.purity || 0, frac),
      sse: lerp(fLo.sse || 0, fHi.sse || 0, frac),
      l1Cost: lerp(fLo.l1Cost || 0, fHi.l1Cost || 0, frac),
      sil: lerp(fLo.sil, fHi.sil, frac),
      shift: lerp(fLo.shift || 0, fHi.shift || 0, frac),
      iterDisplay: Math.round(lerp(fLo.iter, fHi.iter, frac)),
      totalIters: maxIdx,
      trailFrames: frames.slice(0, hi + 1)
    };
  }

  function drawBeansBatch(ctx, beans, visibleCount, getXY, getColorIdx, palette, box, domain, outlierProgress) {
    const padL = 42, padR = 16, padT = 36, padB = 34;
    const xStart = box.x + padL, xEnd = box.x + box.w - padR;
    const yStart = box.y + padT, yEnd = box.y + box.h - padB;

    ctx.save();
    ctx.beginPath();
    ctx.rect(xStart, yStart, xEnd - xStart, yEnd - yStart);
    ctx.clip();

    const buckets = Array.from({ length: palette.length }, () => []);
    const outPts = [];

    for (let i = 0; i < visibleCount; i++) {
      const b = beans[i];
      const [px, py] = getXY(b, i);
      const sp = mapPoint(px, py, box, domain);
      if (outlierProgress > 0.02 && b.isOutlierCandidate) {
        outPts.push({ x: sp.x, y: sp.y, rawX: px });
      } else {
        buckets[getColorIdx(b, i) % palette.length].push(sp.x, sp.y);
      }
    }

    ctx.globalAlpha = 0.72;
    for (let c = 0; c < buckets.length; c++) {
      const arr = buckets[c];
      if (arr.length === 0) continue;
      ctx.fillStyle = palette[c];
      ctx.beginPath();
      for (let j = 0; j < arr.length; j += 2) {
        ctx.rect(arr[j] - 1.1, arr[j + 1] - 1.1, 2.2, 2.2);
      }
      ctx.fill();
    }

    // Highlight outlier shock beans
    if (outPts.length > 0) {
      ctx.globalAlpha = 0.95;
      let offscreenCount = 0;
      for (let i = 0; i < outPts.length; i++) {
        const op = outPts[i];
        if (op.x > xEnd - 4) {
          offscreenCount++;
          continue;
        }
        ctx.beginPath();
        ctx.arc(op.x, op.y, 3.3, 0, Math.PI * 2);
        ctx.fillStyle = '#B91C1C';
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#181A18';
        ctx.stroke();
      }

      if (offscreenCount > 0) {
        const bx = xEnd - 172, by = yStart + 8;
        ctx.fillStyle = '#FAD0C3';
        ctx.strokeStyle = '#181A18';
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.roundRect(bx, by, 164, 24, 5);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#7F1D1D';
        ctx.font = '700 11px "Segoe UI", system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${offscreenCount} ngoại lai văng phải →`, bx + 82, by + 16);
      }
    }

    ctx.restore();
  }

  function drawKMeansCentroids(ctx, stateKm, box, domain, isOutlierPhase, cleanRefCenters) {
    const padL = 42, padR = 16, padT = 36, padB = 34;
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.x + padL, box.y + padT, box.w - padL - padR, box.h - padT - padB);
    ctx.clip();

    // Motion trails
    if (stateKm.trailFrames && stateKm.trailFrames.length > 1) {
      const k = stateKm.points.length;
      for (let c = 0; c < k; c++) {
        ctx.beginPath();
        stateKm.trailFrames.forEach((fr, idx) => {
          const pt = fr.centroids[c];
          const p = mapPoint(pt.x, pt.y, box, domain);
          if (idx === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        });
        const curr = mapPoint(stateKm.points[c].x, stateKm.points[c].y, box, domain);
        ctx.lineTo(curr.x, curr.y);
        ctx.strokeStyle = isOutlierPhase ? 'rgba(185, 28, 28, 0.7)' : 'rgba(29, 78, 216, 0.55)';
        ctx.lineWidth = 1.8;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    // Pull tension vectors during Act 6 (nối từ tâm sạch gần nhất sang tâm lệch)
    if (isOutlierPhase && cleanRefCenters) {
      stateKm.points.forEach((pt) => {
        let bestRef = cleanRefCenters[0], bestD = Infinity;
        for (let j = 0; j < cleanRefCenters.length; j++) {
          const d = Math.hypot(pt.x - cleanRefCenters[j].x, pt.y - cleanRefCenters[j].y);
          if (d < bestD) { bestD = d; bestRef = cleanRefCenters[j]; }
        }
        const ref = mapPoint(bestRef.x, bestRef.y, box, domain);
        const cur = mapPoint(pt.x, pt.y, box, domain);
        if (Math.hypot(cur.x - ref.x, cur.y - ref.y) > 7) {
          ctx.beginPath();
          ctx.arc(ref.x, ref.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#9CA3AF';
          ctx.fill();

          ctx.beginPath();
          ctx.moveTo(ref.x, ref.y);
          ctx.lineTo(cur.x, cur.y);
          ctx.strokeStyle = '#B91C1C';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 3]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });
    }

    const xEnd = box.x + box.w - 16;
    stateKm.points.forEach((pt, idx) => {
      const pos = mapPoint(pt.x, pt.y, box, domain);
      if (pos.x > xEnd - 8) {
        ctx.fillStyle = '#B91C1C';
        ctx.beginPath();
        ctx.roundRect(xEnd - 96, Math.max(box.y + 64, Math.min(box.y + box.h - 46, pos.y - 11)), 90, 22, 4);
        ctx.fill();
        ctx.fillStyle = '#FCFBF8';
        ctx.font = '700 10.5px "Segoe UI", system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`C${idx + 1} văng phải →`, xEnd - 51, Math.max(box.y + 64, Math.min(box.y + box.h - 46, pos.y - 11)) + 15);
        return;
      }

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 11.5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(252, 251, 248, 0.94)';
      ctx.fill();
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = '#181A18';
      ctx.setLineDash([3, 2]);
      ctx.stroke();
      ctx.setLineDash([]);

      const arm = 7.5;
      ctx.lineWidth = 2.6;
      ctx.strokeStyle = isOutlierPhase ? '#B91C1C' : '#181A18';
      ctx.beginPath();
      ctx.moveTo(pos.x - arm, pos.y); ctx.lineTo(pos.x + arm, pos.y);
      ctx.moveTo(pos.x, pos.y - arm); ctx.lineTo(pos.x, pos.y + arm);
      ctx.stroke();

      ctx.fillStyle = '#181A18';
      ctx.beginPath();
      ctx.roundRect(pos.x + 9, pos.y - 16, 22, 14, 3);
      ctx.fill();
      ctx.fillStyle = '#FCFBF8';
      ctx.font = '700 9.5px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`C${idx + 1}`, pos.x + 20, pos.y - 6);
    });

    ctx.restore();
  }

  function drawMedoidBeans(ctx, statePam, box, domain, featuredIdx) {
    const padL = 42, padR = 16, padT = 36, padB = 34;
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.x + padL, box.y + padT, box.w - padL - padR, box.h - padT - padB);
    ctx.clip();

    statePam.points.forEach((pt, idx) => {
      const pos = mapPoint(pt.x, pt.y, box, domain);
      const isFeatured = idx === featuredIdx;
      const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isFeatured ? 16 : 12, 0, Math.PI * 2);
      ctx.fillStyle = isFeatured ? 'rgba(217, 242, 198, 0.92)' : 'rgba(253, 243, 199, 0.8)';
      ctx.fill();
      ctx.lineWidth = isFeatured ? 2 : 1.3;
      ctx.strokeStyle = '#181A18';
      ctx.stroke();

      ctx.save();
      ctx.translate(pos.x, pos.y);
      ctx.rotate(-0.35);
      ctx.beginPath();
      ctx.ellipse(0, 0, 6.8, 4.5, 0, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = '#181A18';
      ctx.stroke();
      ctx.restore();

      ctx.fillStyle = isFeatured ? '#D9F2C6' : '#FCFBF8';
      ctx.strokeStyle = '#181A18';
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.roundRect(pos.x + 8, pos.y - 16, 23, 14, 3);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#181A18';
      ctx.font = '700 9.5px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`M${idx + 1}`, pos.x + 19.5, pos.y - 6);
    });

    ctx.restore();
  }

  function drawPcaOverlayWidget(ctx, box, progress) {
    const bw = 224, bh = 86;
    const x = box.x + box.w - bw - 16;
    const y = box.y + 42;

    ctx.save();
    ctx.globalAlpha = clamp01(progress * 2);
    ctx.fillStyle = 'rgba(252, 251, 248, 0.94)';
    ctx.strokeStyle = '#181A18';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.roundRect(x, y, bw, bh, 6);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#181A18';
    ctx.font = '700 11px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Phương sai tích lũy PCA (thực đo)', x + 10, y + 18);

    const bars = [
      { label: '2D', pct: 81.9, color: '#D9F2C6' },
      { label: '4D', pct: 95.0, color: '#D6ECFA' },
      { label: '7D', pct: 99.6, color: '#FDF3C7' }
    ];
    bars.forEach((b, i) => {
      const ry = y + 28 + i * 18;
      ctx.fillStyle = '#464842';
      ctx.font = '700 10.5px Consolas, monospace';
      ctx.fillText(b.label, x + 10, ry + 10);

      ctx.fillStyle = '#E5E0D5';
      ctx.fillRect(x + 36, ry + 1, 132, 10);

      const wBar = 132 * (b.pct / 100) * easeOutCubic(clamp01(progress * 1.4 - i * 0.15));
      ctx.fillStyle = b.color;
      ctx.strokeStyle = '#181A18';
      ctx.lineWidth = 1;
      ctx.fillRect(x + 36, ry + 1, wBar, 10);
      ctx.strokeRect(x + 36, ry + 1, wBar, 10);

      ctx.fillStyle = '#181A18';
      ctx.textAlign = 'right';
      ctx.fillText(`${b.pct.toFixed(1)}%`, x + bw - 10, ry + 10);
      ctx.textAlign = 'left';
    });
    ctx.restore();
  }

  function drawCalloutPill(ctx, x, y, text, bg = '#FCFBF8', textColor = '#181A18', align = 'left') {
    ctx.save();
    ctx.font = '700 11.5px "Segoe UI", system-ui, sans-serif';
    const padX = 10;
    const tw = ctx.measureText(text).width + padX * 2;
    const rx = align === 'right' ? x - tw : (align === 'center' ? x - tw / 2 : x);
    ctx.fillStyle = bg;
    ctx.strokeStyle = '#181A18';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.roundRect(rx, y, tw, 24, 5);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    ctx.fillText(text, rx + tw / 2, y + 16);
    ctx.restore();
  }

  function renderFrame(canvas, data, currentTime) {
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return null;
    const dpr = window.devicePixelRatio || 1;
    const cw = Math.round(rect.width * dpr);
    const ch = Math.round(rect.height * dpr);
    if (canvas.width !== cw || canvas.height !== ch) {
      canvas.width = cw;
      canvas.height = ch;
    }

    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.scale(dpr, dpr);
    const W = rect.width, H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const acts = window.ANIM_STORY;
    let act = acts[acts.length - 1];
    for (let i = 0; i < acts.length; i++) {
      if (currentTime <= acts[i].end || i === acts.length - 1) {
        act = acts[i];
        break;
      }
    }
    const localU = clamp01((currentTime - act.start) / (act.end - act.start));

    const beans = data.beans;
    const varietyPalette = VARIETIES.map(v => v.color);

    const cleanKmRef = data.kmClean[data.kmClean.length - 1];
    const cleanPamRef = data.pamClean[data.pamClean.length - 1];

    let telemetry = {
      act,
      localU,
      beanCount: data.totalCount,
      outlierText: '0 (0%)',
      iterText: 'Chuẩn bị',
      ariKm: '0.379*',
      ariMed: 'Chờ PAM',
      deltaKmText: '',
      deltaMedText: '',
      nmiKm: '—',
      nmiMed: '—',
      silKmText: '0.533*',
      silText: '—',
      purityKm: '—',
      purityMed: '—',
      sseText: '—',
      l1Text: '—',
      shiftText: '0.00 σ',
      dangerKm: false,
      safeMed: false,
      evalTone: 'neutral',
      evalVerdict: 'Đang nạp dữ liệu ban đầu...',
      ariBarPct: 38,
      purityBarPct: 45,
      robustBarPct: 30,
      featuredMedoidBean: null,
      featuredMedoidIdx: 6
    };

    const singleBox = { x: 8, y: 8, w: W - 16, h: H - 16 };
    const splitGap = 12;
    const halfW = (W - 16 - splitGap) / 2;
    const leftBox = { x: 8, y: 8, w: halfW, h: H - 16 };
    const rightBox = { x: 8 + halfW + splitGap, y: 8, w: halfW, h: H - 16 };

    if (act.id === 1) {
      const revealU = easeOutCubic(clamp01(localU / 0.48));
      const vis = Math.round(data.totalCount * revealU);
      const dom = getCoordDomain(1);
      drawPanelFrame(ctx, singleBox, 'Dữ liệu gốc chưa chuẩn hóa (16 biến)', `${vis.toLocaleString('vi-VN')} / 13.611 hạt`, dom, 'Area gốc (20.420 → 254.616 px²)', 'AspectRation (1,0 → 2,4 · bị nén dẹt)');
      drawBeansBatch(ctx, beans, vis, (b) => b.rawCoord, (b) => b.varietyIndex, varietyPalette, singleBox, dom, 0);
      if (localU > 0.42) {
        drawCalloutPill(ctx, singleBox.x + 52, singleBox.y + 44, 'Chiều dọc (Hình dáng): chỉ 1,0 → 2,4 nên bị ép thành đường mảnh!', '#FAD0C3', '#7F1D1D');
        drawCalloutPill(ctx, singleBox.x + singleBox.w - 22, singleBox.y + singleBox.h - 68, 'Chiều ngang (Diện tích): tới 254.616 px² chi phối >99,9% khoảng cách!', '#FDF3C7', '#181A18', 'right');
      }
      telemetry.beanCount = vis;
      telemetry.iterText = 'Dữ liệu thô';
      telemetry.ariKm = '0.379*';
      telemetry.silKmText = '0.533*';
      telemetry.purityKm = 'Mốc thô';
      telemetry.evalTone = 'warn';
      telemetry.evalVerdict = localU < 0.45
        ? 'Đang nạp từng giống hạt đậu khô (0 → 13.611 hạt)...'
        : 'Cảnh báo Baseline thô: Nếu gom ngay không chuẩn hóa, ARI tụt còn 0,379 ± 0,011!';
      telemetry.ariBarPct = 38;
      telemetry.purityBarPct = 48;
      telemetry.robustBarPct = 20;
    } else if (act.id === 2) {
      const shiftStep = clamp01(localU / 0.24);
      const morph = easeInOutCubic(clamp01((localU - 0.22) / 0.56));
      const dom = getCoordDomain(2);
      drawPanelFrame(ctx, singleBox, 'Chuẩn hóa Z-score: Z = (X − μ_train) / σ_train', morph < 0.05 ? 'Bước 1: Trừ μ_train' : (morph < 0.98 ? 'Bước 2: Chia σ_train (đang bung trục...)' : 'Hoàn tất: Mọi cột cùng thang σ'), dom, 'Area sau Z-score (độ lệch chuẩn σ)', 'Hình dáng sau Z-score (độ lệch chuẩn σ)');
      drawBeansBatch(ctx, beans, data.totalCount, (b) => [
        lerp(b.rawCoord[0] * (1 - shiftStep * 0.2), b.zCoord[0], morph),
        lerp(b.rawCoord[1], b.zCoord[1], morph)
      ], (b) => b.varietyIndex, varietyPalette, singleBox, dom, 0);
      if (localU < 0.28) {
        drawCalloutPill(ctx, singleBox.x + 54, singleBox.y + 44, 'Bước 1: Trừ trung bình μ_train để dời tâm đàn hạt về gốc 0', '#D6ECFA', '#181A18');
      } else {
        drawCalloutPill(ctx, singleBox.x + 54, singleBox.y + 44, 'Bước 2: Chia σ_train → Giãn trục hình dáng lên bằng cỡ trục diện tích', '#D9F2C6', '#181A18');
      }
      telemetry.iterText = 'Z-score (16D)';
      telemetry.ariKm = 'Chuẩn bị';
      telemetry.silKmText = 'Cân bằng σ';
      telemetry.purityKm = 'Var = 1,0';
      telemetry.evalTone = 'safe';
      telemetry.evalVerdict = 'Chuẩn hóa Z-score thành công: Đưa cả 16 thông số về Var = 1 (không rò rỉ dữ liệu Test).';
      telemetry.ariBarPct = 55;
      telemetry.purityBarPct = 65;
      telemetry.robustBarPct = 50;
    } else if (act.id === 3) {
      const morph = easeInOutCubic(clamp01((localU - 0.22) / 0.56));
      const dom = getCoordDomain(3);
      drawPanelFrame(ctx, singleBox, 'Giảm chiều PCA (SVD): Cô đọng 16 chiều trùng lặp về mặt phẳng PC1–PC2', 'Giữ 81,90% tổng thông tin', dom, 'PC1 · Trục Kích thước (55,47%)', 'PC2 · Trục Độ thuôn dài vs Tròn (26,43%)');
      drawBeansBatch(ctx, beans, data.totalCount, (b) => [
        lerp(b.zCoord[0], b.pcClean[0], morph),
        lerp(b.zCoord[1], b.pcClean[1], morph)
      ], (b) => b.varietyIndex, varietyPalette, singleBox, dom, 0);
      drawPcaOverlayWidget(ctx, singleBox, clamp01((localU - 0.35) / 0.5));
      if (morph > 0.72) {
        const bombayPos = mapPoint(7.8, 5.5, singleBox, dom);
        const horozPos = mapPoint(-0.8, 3.3, singleBox, dom);
        const sekerPos = mapPoint(-1.8, -2.9, singleBox, dom);
        drawCalloutPill(ctx, bombayPos.x - 10, bombayPos.y + 18, 'Bombay (hạt to nhất · +PC1)', '#FDF3C7', '#181A18', 'center');
        drawCalloutPill(ctx, horozPos.x, horozPos.y - 28, 'Horoz (thuôn dài · +PC2)', '#FAD0C3', '#181A18', 'center');
        drawCalloutPill(ctx, sekerPos.x, sekerPos.y + 12, 'Seker (tròn đầy · -PC2)', '#D9F2C6', '#181A18', 'center');
      }
      telemetry.iterText = 'PCA (SVD)';
      telemetry.ariKm = '2D: 81,9%';
      telemetry.ariMed = '7D: 99,6%';
      telemetry.nmiKm = 'cond 2.230';
      telemetry.silKmText = '21 cặp >0.9';
      telemetry.evalTone = 'neutral';
      telemetry.evalVerdict = 'PCA khử 21 cặp đa cộng tuyến: 2D giữ 81,9%, 4D đạt 95,0%, 7D đạt 99,6% phương sai.';
      telemetry.ariBarPct = 82;
      telemetry.purityBarPct = 76;
      telemetry.robustBarPct = 55;
    } else if (act.id === 4) {
      const dom = getCoordDomain(4);
      const frames = data.kmClean;
      const iterProgress = clamp01((localU - 0.16) / 0.68);
      const kmState = interpolateCenters(frames, iterProgress * (frames.length - 1));
      drawPanelFrame(ctx, singleBox, 'K-Means++ chạy chậm từng vòng lặp (k = 7 · 16 chiều)', `Vòng ${kmState.iterDisplay} / ${kmState.totalIters} · ARI = ${kmState.ari.toFixed(3)}`, dom, 'PC1 · Trục Kích thước', 'PC2 · Trục Hình dáng');
      drawBeansBatch(ctx, beans, data.totalCount, (b) => b.pcClean, (_, idx) => kmState.assignments[idx], CLUSTER_COLORS, singleBox, dom, 0);
      drawKMeansCentroids(ctx, kmState, singleBox, dom, false, null);

      const kmNote = localU < 0.18
        ? 'Vòng 0: K-Means++ rải 7 hạt tâm xa nhau theo xác suất D²'
        : (localU < 0.84 ? 'Gán màu theo tâm gần nhất → Dời (+) về tọa độ trung bình cộng' : 'Hội tụ! Dấu (+) là trung bình toán học (không phải hạt thật)');
      drawCalloutPill(ctx, singleBox.x + 54, singleBox.y + 44, kmNote, '#D6ECFA', '#181A18');

      telemetry.iterText = `K-Means ${kmState.iterDisplay}/${kmState.totalIters}`;
      telemetry.ariKm = kmState.ari.toFixed(3);
      telemetry.nmiKm = kmState.nmi.toFixed(3);
      telemetry.silKmText = kmState.sil.toFixed(3);
      telemetry.silText = kmState.sil.toFixed(3);
      telemetry.purityKm = `${(kmState.purity * 100).toFixed(1)}%`;
      telemetry.sseText = `${Math.round(kmState.sse).toLocaleString('vi-VN')}`;
      telemetry.l1Text = `${Math.round(kmState.l1Cost).toLocaleString('vi-VN')}`;
      telemetry.evalTone = 'neutral';
      telemetry.evalVerdict = `Đánh giá K-Means (Vòng ${kmState.iterDisplay}): SSE giảm còn ${Math.round(kmState.sse).toLocaleString('vi-VN')}, ARI đạt ${kmState.ari.toFixed(3)}, Purity ${(kmState.purity * 100).toFixed(1)}%.`;
      telemetry.ariBarPct = Math.round(kmState.ari * 100);
      telemetry.purityBarPct = Math.round(kmState.purity * 100);
      telemetry.robustBarPct = 45;
    } else if (act.id === 5) {
      const dom = getCoordDomain(5);
      const kmFinal = interpolateCenters(data.kmClean, data.kmClean.length - 1);
      const iterProgress = clamp01((localU - 0.10) / 0.64);
      const pamState = interpolateCenters(data.pamClean, iterProgress * (data.pamClean.length - 1));
      const featuredIdx = pamState.points.length - 1;
      const featBean = beans[pamState.points[featuredIdx].beanIdx];

      drawPanelFrame(ctx, leftBox, 'K-Means (Tâm trung bình cộng ảo +)', `ARI = ${kmFinal.ari.toFixed(3)}`, dom, 'PC1 (Kích thước)', 'PC2 (Hình dáng)');
      drawBeansBatch(ctx, beans, data.totalCount, (b) => b.pcClean, (_, idx) => kmFinal.assignments[idx], CLUSTER_COLORS, leftBox, dom, 0);
      drawKMeansCentroids(ctx, kmFinal, leftBox, dom, false, null);
      drawCalloutPill(ctx, leftBox.x + 48, leftBox.y + 42, 'Dấu (+): Không trùng hạt đậu thật nào', '#D6ECFA', '#181A18');

      const pamStepLabel = pamState.iterDisplay === 0 ? 'Khởi tạo thô' : (pamState.iterDisplay === 1 ? 'Pha BUILD' : 'Pha SWAP');
      drawPanelFrame(ctx, rightBox, 'K-Medoids PAM (Hạt đậu đại diện thật ◉)', `${pamStepLabel} · ARI = ${pamState.ari.toFixed(3)}`, dom, 'PC1 (Kích thước)', 'PC2 (Hình dáng)');
      drawBeansBatch(ctx, beans, data.totalCount, (b) => b.pcClean, (_, idx) => pamState.assignments[idx], CLUSTER_COLORS, rightBox, dom, 0);
      drawMedoidBeans(ctx, pamState, rightBox, dom, featuredIdx);

      const pamNote = pamState.iterDisplay === 0
        ? 'Khởi tạo ban đầu trước khi tìm trung tâm'
        : (pamState.iterDisplay === 1 ? 'BUILD: Chọn hạt thật ở giữa cụm → ARI vọt 0,697' : 'SWAP: Đổi hạt cân hơn → ARI = 0,711 & soi 16 số đo M7');
      drawCalloutPill(ctx, rightBox.x + 48, rightBox.y + 42, pamNote, '#D9F2C6', '#181A18');

      if (localU > 0.65 && pamState.points[featuredIdx]) {
        const mPos = mapPoint(pamState.points[featuredIdx].x, pamState.points[featuredIdx].y, rightBox, dom);
        drawCalloutPill(ctx, Math.min(rightBox.x + rightBox.w - 20, mPos.x), Math.max(rightBox.y + 72, mPos.y + 20), `Hạt mẫu M7 (#Bean_${String(featBean.id).padStart(5, '0')})`, '#FDF3C7', '#181A18', 'right');
      }

      telemetry.iterText = `${pamStepLabel} (${pamState.iterDisplay}/${pamState.totalIters})`;
      telemetry.ariKm = kmFinal.ari.toFixed(3);
      telemetry.ariMed = pamState.ari.toFixed(3);
      telemetry.nmiKm = kmFinal.nmi.toFixed(3);
      telemetry.nmiMed = pamState.nmi.toFixed(3);
      telemetry.silKmText = kmFinal.sil.toFixed(3);
      telemetry.silText = pamState.sil.toFixed(3);
      telemetry.purityKm = `${(kmFinal.purity * 100).toFixed(1)}%`;
      telemetry.purityMed = `${(pamState.purity * 100).toFixed(1)}%`;
      telemetry.sseText = `${Math.round(kmFinal.sse).toLocaleString('vi-VN')}`;
      telemetry.l1Text = `${Math.round(pamState.l1Cost).toLocaleString('vi-VN')}`;
      telemetry.safeMed = pamState.ari >= kmFinal.ari;
      telemetry.evalTone = 'safe';
      telemetry.evalVerdict = `Đối chiếu Sạch (16D): PAM đạt ARI = ${pamState.ari.toFixed(3)} · Purity ${(pamState.purity * 100).toFixed(1)}% (K-Means: ${kmFinal.ari.toFixed(3)} · ${(kmFinal.purity * 100).toFixed(1)}%).`;
      telemetry.ariBarPct = Math.round(pamState.ari * 100);
      telemetry.purityBarPct = Math.round(pamState.purity * 100);
      telemetry.robustBarPct = 92;
      telemetry.featuredMedoidBean = featBean;
      telemetry.featuredMedoidIdx = featuredIdx;
    } else {
      const dom = getCoordDomain(6);
      const shockTravel = act.id === 6 ? easeOutCubic(clamp01(localU / 0.28)) : 1.0;
      const iterPhase = act.id === 6 ? clamp01((localU - 0.24) / 0.56) : 1.0;

      const kmState = interpolateCenters(data.kmOutlier, iterPhase * (data.kmOutlier.length - 1));
      const pamState = interpolateCenters(data.pamOutlier, iterPhase * (data.pamOutlier.length - 1));
      const kmCleanRef = data.kmClean[data.kmClean.length - 1].centroids;
      const featuredIdx = pamState.points.length - 1;
      const featBean = beans[pamState.points[featuredIdx].beanIdx];

      const coordFn = (b) => b.isOutlierCandidate
        ? [lerp(b.pcClean[0], b.pcaOutlier[0], shockTravel), lerp(b.pcClean[1], b.pcaOutlier[1], shockTravel)]
        : b.pcClean;

      drawPanelFrame(ctx, leftBox, 'K-Means khi dính 1% ngoại lai (Tâm + bị giật lệch!)', `ARI = ${kmState.ari.toFixed(3)}`, dom, 'PC1 (Kích thước)', 'PC2 (Hình dáng)');
      drawBeansBatch(ctx, beans, data.totalCount, coordFn, (_, idx) => kmState.assignments[idx], CLUSTER_COLORS, leftBox, dom, shockTravel);
      drawKMeansCentroids(ctx, kmState, leftBox, dom, shockTravel > 0.08, kmCleanRef);
      if (iterPhase > 0.05) {
        drawCalloutPill(ctx, leftBox.x + 48, leftBox.y + 42, `L2 (d²): Lực kéo mạnh làm tâm lệch ${kmState.shift.toFixed(1)} σ!`, '#FAD0C3', '#7F1D1D');
      }

      drawPanelFrame(ctx, rightBox, 'K-Medoids PAM khi dính 1% ngoại lai (Hạt ◉ giữ vững)', `ARI = ${pamState.ari.toFixed(3)}`, dom, 'PC1 (Kích thước)', 'PC2 (Hình dáng)');
      drawBeansBatch(ctx, beans, data.totalCount, coordFn, (_, idx) => pamState.assignments[idx], CLUSTER_COLORS, rightBox, dom, shockTravel);
      drawMedoidBeans(ctx, pamState, rightBox, dom, featuredIdx);
      if (iterPhase > 0.05) {
        drawCalloutPill(ctx, rightBox.x + 48, rightBox.y + 42, 'L1 (d): Từ chối hoán đổi ngoại lai → Hạt ◉ bất động!', '#D9F2C6', '#065F46');
      }

      const dKm = kmState.ari - cleanKmRef.ari;
      const dMed = pamState.ari - cleanPamRef.ari;
      telemetry.outlierText = '136 hạt (1%)';
      telemetry.iterText = act.id === 7 ? 'Hoàn chỉnh 10-seed' : `Nhiễu · Vòng ${kmState.iterDisplay}`;
      telemetry.ariKm = kmState.ari.toFixed(3);
      telemetry.ariMed = pamState.ari.toFixed(3);
      telemetry.deltaKmText = `${dKm >= 0 ? '+' : ''}${dKm.toFixed(3)}`;
      telemetry.deltaMedText = `${dMed >= 0 ? '+' : ''}${dMed.toFixed(3)}`;
      telemetry.nmiKm = kmState.nmi.toFixed(3);
      telemetry.nmiMed = pamState.nmi.toFixed(3);
      telemetry.silKmText = kmState.sil.toFixed(3);
      telemetry.silText = pamState.sil.toFixed(3);
      telemetry.purityKm = `${(kmState.purity * 100).toFixed(1)}%`;
      telemetry.purityMed = `${(pamState.purity * 100).toFixed(1)}%`;
      telemetry.sseText = `${Math.round(kmState.sse).toLocaleString('vi-VN')}`;
      telemetry.l1Text = `${Math.round(pamState.l1Cost).toLocaleString('vi-VN')}`;
      telemetry.shiftText = `${kmState.shift.toFixed(2)} σ`;
      telemetry.dangerKm = true;
      telemetry.safeMed = true;
      telemetry.evalTone = act.id === 7 ? 'safe' : 'danger';
      telemetry.evalVerdict = act.id === 7
        ? 'Kết luận 10-seed: PAM thắng có ý nghĩa thống kê (Wilcoxon p = 0,00195) & kháng ngoại lai 1% vượt trội.'
        : `Sốc 1% nhiễu: K-Means rớt ΔARI = ${dKm.toFixed(3)} (tâm văng ${kmState.shift.toFixed(1)}σ), PAM vẫn vững ở ${pamState.ari.toFixed(3)} (Δ ${dMed >= 0 ? '+' : ''}${dMed.toFixed(3)})!`;
      telemetry.ariBarPct = Math.round(pamState.ari * 100);
      telemetry.purityBarPct = Math.round(pamState.purity * 100);
      telemetry.robustBarPct = 97;
      telemetry.featuredMedoidBean = featBean;
      telemetry.featuredMedoidIdx = featuredIdx;
    }

    ctx.restore();
    return telemetry;
  }

  return { renderFrame };
})();
