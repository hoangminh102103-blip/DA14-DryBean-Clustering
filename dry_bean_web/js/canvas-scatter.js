/**
 * =========================================================================
 * canvas-scatter.js — VẼ HAI BẢN ĐỒ PHÂN TÁN K-MEANS & K-MEDOIDS + ZOOM/PAN
 * =========================================================================
 */
const canvasKMeans = document.getElementById('canvasKMeans');
const canvasKMedoids = document.getElementById('canvasKMedoids');
const ctxKMeans = canvasKMeans.getContext('2d', { alpha: false });
const ctxKMedoids = canvasKMedoids.getContext('2d', { alpha: false });

function dataToScreen(pc1, pc2, width, height) {
  const padL = 42, padR = 16, padT = 18, padB = 30;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const normX = (pc1 - (-5.5)) / 17.0;
  const normY = 1 - (pc2 - (-5.2)) / 10.4;

  const baseX = padL + normX * plotW;
  const baseY = padT + normY * plotH;

  const cx = width * 0.5;
  const cy = height * 0.5;
  return {
    x: cx + (baseX - cx) * state.viewport.scale + state.viewport.offsetX,
    y: cy + (baseY - cy) * state.viewport.scale + state.viewport.offsetY
  };
}

function drawDraftingGrid(ctx, w, h) {
  const padL = 42, padR = 16, padT = 18, padB = 30;

  ctx.fillStyle = '#F9F7F2';
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = '#E6E2D8';
  ctx.lineWidth = 1;

  const xTicks = [-4, -2, 0, 2, 4, 6, 8, 10, 15, 20, 25, 30];
  const yTicks = [-4, -2, 0, 2, 4];

  ctx.font = '10px "JetBrains Mono", monospace';
  ctx.fillStyle = '#888880';

  xTicks.forEach(tx => {
    const p = dataToScreen(tx, 0, w, h);
    if (p.x >= padL && p.x <= w - padR) {
      ctx.beginPath();
      ctx.moveTo(p.x, padT);
      ctx.lineTo(p.x, h - padB);
      ctx.stroke();

      ctx.textAlign = 'center';
      ctx.fillText(String(tx), p.x, h - padB + 13);
    }
  });

  yTicks.forEach(ty => {
    const p = dataToScreen(0, ty, w, h);
    if (p.y >= padT && p.y <= h - padB) {
      ctx.beginPath();
      ctx.moveTo(padL, p.y);
      ctx.lineTo(w - padR, p.y);
      ctx.stroke();

      ctx.textAlign = 'right';
      ctx.fillText(String(ty), padL - 6, p.y + 3);
    }
  });

  const origin = dataToScreen(0, 0, w, h);
  ctx.strokeStyle = '#CFCBC0';
  if (origin.x >= padL && origin.x <= w - padR) {
    ctx.beginPath();
    ctx.moveTo(origin.x, padT);
    ctx.lineTo(origin.x, h - padB);
    ctx.stroke();
  }
  if (origin.y >= padT && origin.y <= h - padB) {
    ctx.beginPath();
    ctx.moveTo(padL, origin.y);
    ctx.lineTo(w - padR, origin.y);
    ctx.stroke();
  }

  ctx.strokeStyle = '#1E201E';
  ctx.lineWidth = 1.2;
  ctx.strokeRect(padL, padT, w - padL - padR, h - padT - padB);

  ctx.fillStyle = '#575852';
  ctx.font = '600 10px "JetBrains Mono", monospace';
  ctx.textAlign = 'right';
  ctx.fillText(state.standardized ? 'PC1 (Kích thước →)' : 'Area thô (px² →)', w - padR, h - 5);

  ctx.save();
  ctx.translate(12, padT + 4);
  ctx.rotate(-Math.PI / 2);
  ctx.textAlign = 'right';
  ctx.fillText(state.standardized ? 'PC2 (Hình dáng ↑)' : 'Hình dáng (nén)', 0, 0);
  ctx.restore();
}

function drawScatterCanvas(canvas, ctx, mode) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  if (canvas.width !== Math.round(rect.width * dpr) || canvas.height !== Math.round(rect.height * dpr)) {
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
  }

  const w = rect.width, h = rect.height;
  ctx.save();
  ctx.scale(dpr, dpr);

  drawDraftingGrid(ctx, w, h);

  const assignments = mode === 'kmeans' ? state.kmeansAssignments : state.kmedoidsAssignments;
  const selectedVar = state.selectedVariety;
  const ptSize = state.viewport.scale > 2.2 ? 2.2 : 1.65;

  // Lớp 1: Các hạt bị làm mờ khi lọc giống đậu
  if (selectedVar) {
    ctx.fillStyle = 'rgba(136, 136, 128, 0.16)';
    ctx.beginPath();
    for (let i = 0; i < beansData.length; i++) {
      const b = beansData[i];
      if (b.variety === selectedVar) continue;
      const pos = dataToScreen(b.pcCurrent[0], b.pcCurrent[1], w, h);
      if (pos.x < -4 || pos.x > w + 4 || pos.y < -4 || pos.y > h + 4) continue;
      ctx.rect(pos.x - 1, pos.y - 1, 2, 2);
    }
    ctx.fill();
  }

  // Lớp 2: Vẽ 13.611 hạt đậu theo cụm màu
  for (let c = 0; c < state.k; c++) {
    ctx.fillStyle = CLUSTER_COLORS[c % CLUSTER_COLORS.length];
    ctx.globalAlpha = selectedVar ? 0.92 : 0.68;
    ctx.beginPath();
    for (let i = 0; i < beansData.length; i++) {
      if (assignments[i] !== c) continue;
      const b = beansData[i];
      if (selectedVar && b.variety !== selectedVar) continue;
      if (b.isOutlier) continue;

      const pos = dataToScreen(b.pcCurrent[0], b.pcCurrent[1], w, h);
      if (pos.x < -4 || pos.x > w + 4 || pos.y < -4 || pos.y > h + 4) continue;
      ctx.rect(pos.x - ptSize * 0.5, pos.y - ptSize * 0.5, ptSize, ptSize);
    }
    ctx.fill();
  }
  ctx.globalAlpha = 1.0;

  // Lớp 3: Các hạt ngoại lai (136 hạt) nếu đang bật tiêm ngoại lai
  if (state.outliersInjected) {
    let offscreen = 0;
    for (let i = 0; i < beansData.length; i++) {
      const b = beansData[i];
      if (!b.isOutlier) continue;
      const pos = dataToScreen(b.pcCurrent[0], b.pcCurrent[1], w, h);
      if (pos.x > w - 12) {
        offscreen++;
        continue;
      }
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 3.4, 0, Math.PI * 2);
      ctx.fillStyle = '#DC2626';
      ctx.fill();
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = '#1E201E';
      ctx.stroke();
    }

    if (offscreen > 0) {
      const bw = 156, bh = 24;
      const bx = w - bw - 10, by = 26;
      ctx.fillStyle = '#F8C8B8';
      ctx.strokeStyle = '#1E201E';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.roundRect(bx, by, bw, bh, 5);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#1E201E';
      ctx.font = '700 10px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`⚡ ${offscreen} ngoại lai → (PC1 +25)`, bx + bw / 2, by + 15);
    }
  }

  // Lớp 4: Vẽ đại diện cụm theo đúng đặc tả
  if (mode === 'kmeans') {
    drawKMeansCrossCentroids(ctx, w, h);
  } else {
    drawKMedoidsRealBeans(ctx, w, h);
  }

  ctx.restore();
}

function drawKMeansCrossCentroids(ctx, w, h) {
  const t = 1 - Math.pow(1 - state.kmeansAnimProgress, 3);

  state.kmeansCentroids2D.forEach((cent, cIdx) => {
    let drawX = cent.x, drawY = cent.y;
    if (state.kmeansCentroidsPrev2D[cIdx] && t < 1) {
      drawX = state.kmeansCentroidsPrev2D[cIdx].x + (cent.x - state.kmeansCentroidsPrev2D[cIdx].x) * t;
      drawY = state.kmeansCentroidsPrev2D[cIdx].y + (cent.y - state.kmeansCentroidsPrev2D[cIdx].y) * t;
    }

    const pos = dataToScreen(drawX, drawY, w, h);

    if (state.outliersInjected && state.kmeansCentroidsCleanRef2D[cIdx]) {
      const refPos = dataToScreen(state.kmeansCentroidsCleanRef2D[cIdx].x, state.kmeansCentroidsCleanRef2D[cIdx].y, w, h);
      if (Math.hypot(pos.x - refPos.x, pos.y - refPos.y) > 8) {
        ctx.save();
        ctx.strokeStyle = '#DC2626';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(refPos.x, refPos.y);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        ctx.restore();
      }
    }

    ctx.save();
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 12, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(250, 249, 245, 0.92)';
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.setLineDash([3, 2]);
    ctx.strokeStyle = '#1E201E';
    ctx.stroke();
    ctx.setLineDash([]);

    const arm = 8.5;
    ctx.lineCap = 'square';
    ctx.lineWidth = 4.4;
    ctx.strokeStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.moveTo(pos.x - arm, pos.y);
    ctx.lineTo(pos.x + arm, pos.y);
    ctx.moveTo(pos.x, pos.y - arm);
    ctx.lineTo(pos.x, pos.y + arm);
    ctx.stroke();

    ctx.lineWidth = 2.4;
    ctx.strokeStyle = state.outliersInjected ? '#DC2626' : '#1E201E';
    ctx.beginPath();
    ctx.moveTo(pos.x - arm, pos.y);
    ctx.lineTo(pos.x + arm, pos.y);
    ctx.moveTo(pos.x, pos.y - arm);
    ctx.lineTo(pos.x, pos.y + arm);
    ctx.stroke();

    const tag = `C${cIdx + 1}`;
    ctx.font = '700 10px "JetBrains Mono", monospace';
    const tw = ctx.measureText(tag).width + 8;
    ctx.fillStyle = '#1E201E';
    ctx.beginPath();
    ctx.roundRect(pos.x + 9, pos.y - 17, tw, 15, 4);
    ctx.fill();

    ctx.fillStyle = '#FAF9F5';
    ctx.textAlign = 'center';
    ctx.fillText(tag, pos.x + 9 + tw / 2, pos.y - 6);
    ctx.restore();
  });
}

function drawKMedoidsRealBeans(ctx, w, h) {
  state.kmedoidIndices.forEach((beanIdx, cIdx) => {
    const bean = beansData[beanIdx];
    if (!bean) return;
    const pos = dataToScreen(bean.pcCurrent[0], bean.pcCurrent[1], w, h);
    const color = CLUSTER_COLORS[cIdx % CLUSTER_COLORS.length];
    const isSelected = state.selectedMedoidCluster === cIdx;
    const isHovered = state.hoveredMedoidIdx === cIdx;

    ctx.save();

    const glowR = isSelected ? 17 : (isHovered ? 15 : 12.5);
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, glowR, 0, Math.PI * 2);
    ctx.fillStyle = isSelected ? 'rgba(217, 242, 198, 0.85)' : 'rgba(253, 243, 199, 0.72)';
    ctx.fill();
    ctx.lineWidth = isSelected ? 1.8 : 1.2;
    ctx.strokeStyle = '#1E201E';
    ctx.stroke();

    ctx.translate(pos.x, pos.y);
    ctx.rotate(-0.35);
    ctx.beginPath();
    ctx.ellipse(0, 0, 7.2, 4.9, 0, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = '#1E201E';
    ctx.stroke();
    ctx.restore();

    ctx.save();
    const tag = `M${cIdx + 1}`;
    ctx.font = '700 10px "JetBrains Mono", monospace';
    const tw = ctx.measureText(tag).width + 8;
    ctx.fillStyle = isSelected ? '#D9F2C6' : '#FAF9F5';
    ctx.strokeStyle = '#1E201E';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.roundRect(pos.x + 8, pos.y - 17, tw, 15, 4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#1E201E';
    ctx.textAlign = 'center';
    ctx.fillText(tag, pos.x + 8 + tw / 2, pos.y - 6);
    ctx.restore();
  });
}

let animId = null;
function startCentroidAnimation() {
  if (animId) cancelAnimationFrame(animId);
  function tick() {
    if (state.kmeansAnimProgress < 1) {
      state.kmeansAnimProgress = Math.min(1, state.kmeansAnimProgress + 0.085);
      renderBothScatterCanvases();
      animId = requestAnimationFrame(tick);
    } else {
      renderBothScatterCanvases();
    }
  }
  animId = requestAnimationFrame(tick);
}

function renderBothScatterCanvases() {
  drawScatterCanvas(canvasKMeans, ctxKMeans, 'kmeans');
  drawScatterCanvas(canvasKMedoids, ctxKMedoids, 'kmedoids');
}

function bindSynchronizedCanvasControls(canvas, isMedoidCanvas) {
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const factor = e.deltaY < 0 ? 1.16 : 1 / 1.16;
    const nextScale = Math.min(14, Math.max(0.45, state.viewport.scale * factor));
    const ratio = nextScale / state.viewport.scale;

    const cx = rect.width * 0.5;
    const cy = rect.height * 0.5;

    state.viewport.offsetX = mx - cx - (mx - cx - state.viewport.offsetX) * ratio;
    state.viewport.offsetY = my - cy - (my - cy - state.viewport.offsetY) * ratio;
    state.viewport.scale = nextScale;

    document.getElementById('zoomBadge').textContent = `${state.viewport.scale.toFixed(1)}×`;
    renderBothScatterCanvases();
  }, { passive: false });

  canvas.addEventListener('pointerdown', (e) => {
    state.viewport.isDragging = true;
    state.viewport.dragMoved = false;
    state.viewport.dragStartX = e.clientX - state.viewport.offsetX;
    state.viewport.dragStartY = e.clientY - state.viewport.offsetY;
    canvas.setPointerCapture(e.pointerId);
  });

  canvas.addEventListener('pointermove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (state.viewport.isDragging) {
      const dx = (e.clientX - state.viewport.dragStartX) - state.viewport.offsetX;
      const dy = (e.clientY - state.viewport.dragStartY) - state.viewport.offsetY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) state.viewport.dragMoved = true;

      state.viewport.offsetX = e.clientX - state.viewport.dragStartX;
      state.viewport.offsetY = e.clientY - state.viewport.dragStartY;
      renderBothScatterCanvases();
      return;
    }

    if (isMedoidCanvas) {
      const hit = hitTestMedoid(mx, my, rect.width, rect.height);
      if (hit !== state.hoveredMedoidIdx) {
        state.hoveredMedoidIdx = hit;
        canvas.style.cursor = hit !== -1 ? 'pointer' : 'grab';
        drawScatterCanvas(canvasKMedoids, ctxKMedoids, 'kmedoids');
      }
    }
  });

  canvas.addEventListener('pointerup', (e) => {
    if (state.viewport.isDragging) {
      state.viewport.isDragging = false;
      canvas.releasePointerCapture(e.pointerId);
    }

    if (isMedoidCanvas && !state.viewport.dragMoved) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTestMedoid(mx, my, rect.width, rect.height);
      if (hit !== -1) {
        state.selectedMedoidCluster = hit;
        updateKpiAndInspectorUI();
        drawScatterCanvas(canvasKMedoids, ctxKMedoids, 'kmedoids');
      }
    }
  });
}

function hitTestMedoid(mx, my, width, height) {
  let best = -1, minDist = 22;
  state.kmedoidIndices.forEach((beanIdx, cIdx) => {
    const b = beansData[beanIdx];
    if (!b) return;
    const pos = dataToScreen(b.pcCurrent[0], b.pcCurrent[1], width, height);
    const dist = Math.hypot(mx - pos.x, my - pos.y);
    if (dist < minDist) { minDist = dist; best = cIdx; }
  });
  return best;
}
