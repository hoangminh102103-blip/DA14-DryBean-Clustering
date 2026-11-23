/**
 * =========================================================================
 * algorithms.js — THUẬT TOÁN K-MEANS++, K-MEDOIDS (PAM), ARI & SILHOUETTE
 * =========================================================================
 */
function runKMeans(k, dims) {
  const n = beansData.length;
  const rng = createRng(100 + k * 17 + dims * 3);
  const centroids = Array.from({ length: k }, () => new Float64Array(dims));

  const firstIdx = Math.floor(rng() * n);
  for (let d = 0; d < dims; d++) centroids[0][d] = beansData[firstIdx].pcCurrent[d];

  const minDistSq = new Float64Array(n).fill(Infinity);
  for (let c = 1; c < k; c++) {
    let totalDist = 0;
    for (let i = 0; i < n; i++) {
      const p = beansData[i].pcCurrent;
      let dist = 0;
      for (let d = 0; d < dims; d++) {
        const diff = p[d] - centroids[c - 1][d];
        dist += diff * diff;
      }
      if (dist < minDistSq[i]) minDistSq[i] = dist;
      totalDist += minDistSq[i];
    }
    let target = rng() * totalDist;
    let chosen = 0;
    for (let i = 0; i < n; i++) {
      target -= minDistSq[i];
      if (target <= 0) { chosen = i; break; }
    }
    for (let d = 0; d < dims; d++) centroids[c][d] = beansData[chosen].pcCurrent[d];
  }

  const assignments = new Int32Array(n);
  const counts = new Int32Array(k);
  const sums = Array.from({ length: k }, () => new Float64Array(dims));

  for (let iter = 0; iter < 22; iter++) {
    let changed = 0;
    counts.fill(0);
    for (let c = 0; c < k; c++) sums[c].fill(0);

    for (let i = 0; i < n; i++) {
      const p = beansData[i].pcCurrent;
      let bestC = 0, bestDist = Infinity;
      for (let c = 0; c < k; c++) {
        const cent = centroids[c];
        let dist = 0;
        for (let d = 0; d < dims; d++) {
          const diff = p[d] - cent[d];
          dist += diff * diff;
        }
        if (dist < bestDist) { bestDist = dist; bestC = c; }
      }
      if (assignments[i] !== bestC) { assignments[i] = bestC; changed++; }
      counts[bestC]++;
      for (let d = 0; d < dims; d++) sums[bestC][d] += p[d];
    }

    for (let c = 0; c < k; c++) {
      if (counts[c] > 0) {
        for (let d = 0; d < dims; d++) centroids[c][d] = sums[c][d] / counts[c];
      }
    }
    if (changed === 0 && iter > 2) break;
  }

  const order = Array.from({ length: k }, (_, idx) => idx).sort((a, b) => centroids[a][0] - centroids[b][0]);
  const invOrder = new Int32Array(k);
  order.forEach((oldIdx, newIdx) => { invOrder[oldIdx] = newIdx; });

  const sortedCentroids2D = order.map(idx => ({ x: centroids[idx][0], y: centroids[idx][1] }));
  for (let i = 0; i < n; i++) assignments[i] = invOrder[assignments[i]];

  return { assignments, centroids2D: sortedCentroids2D };
}

function runKMedoids(k, dims) {
  const n = beansData.length;
  const rng = createRng(777 + k * 13 + dims * 5);

  const sampleStep = Math.floor(n / 640);
  const sampleIndices = [];
  for (let i = 0; i < n; i += sampleStep) sampleIndices.push(i);
  const m = sampleIndices.length;

  let medoids = [sampleIndices[Math.floor(rng() * m)]];
  const minD = new Float64Array(m).fill(Infinity);

  for (let c = 1; c < k; c++) {
    let sumD = 0;
    const lastP = beansData[medoids[c - 1]].pcCurrent;
    for (let si = 0; si < m; si++) {
      const p = beansData[sampleIndices[si]].pcCurrent;
      let dVal = 0;
      for (let d = 0; d < dims; d++) dVal += Math.abs(p[d] - lastP[d]);
      if (dVal < minD[si]) minD[si] = dVal;
      sumD += minD[si];
    }
    let target = rng() * sumD;
    let pick = sampleIndices[0];
    for (let si = 0; si < m; si++) {
      target -= minD[si];
      if (target <= 0) { pick = sampleIndices[si]; break; }
    }
    medoids.push(pick);
  }

  const sampleAssign = new Int32Array(m);
  for (let iter = 0; iter < 8; iter++) {
    let changed = false;
    for (let si = 0; si < m; si++) {
      const p = beansData[sampleIndices[si]].pcCurrent;
      let bestC = 0, bestDist = Infinity;
      for (let c = 0; c < k; c++) {
        const mp = beansData[medoids[c]].pcCurrent;
        let dist = 0;
        for (let d = 0; d < dims; d++) {
          const diff = p[d] - mp[d];
          dist += Math.sqrt(diff * diff + 1e-6);
        }
        if (dist < bestDist) { bestDist = dist; bestC = c; }
      }
      sampleAssign[si] = bestC;
    }

    for (let c = 0; c < k; c++) {
      const members = [];
      for (let si = 0; si < m; si++) if (sampleAssign[si] === c) members.push(sampleIndices[si]);
      if (members.length === 0) continue;

      let bestCandidate = medoids[c];
      let bestCost = Infinity;
      for (let a = 0; a < members.length; a++) {
        const candIdx = members[a];
        const cp = beansData[candIdx].pcCurrent;
        let cost = 0;
        for (let b = 0; b < members.length; b++) {
          const op = beansData[members[b]].pcCurrent;
          let dist = 0;
          for (let d = 0; d < dims; d++) {
            const diff = cp[d] - op[d];
            dist += diff * diff;
          }
          cost += Math.sqrt(dist);
        }
        if (cost < bestCost) { bestCost = cost; bestCandidate = candIdx; }
      }
      if (bestCandidate !== medoids[c]) { medoids[c] = bestCandidate; changed = true; }
    }
    if (!changed) break;
  }

  medoids.sort((a, b) => beansData[a].pcCurrent[0] - beansData[b].pcCurrent[0]);

  const assignments = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    const p = beansData[i].pcCurrent;
    let bestC = 0, bestDist = Infinity;
    for (let c = 0; c < k; c++) {
      const mp = beansData[medoids[c]].pcCurrent;
      let dist = 0;
      for (let d = 0; d < dims; d++) {
        const diff = p[d] - mp[d];
        dist += diff * diff;
      }
      if (dist < bestDist) { bestDist = dist; bestC = c; }
    }
    assignments[i] = bestC;
  }

  return { assignments, medoidIndices: medoids };
}

function computeARI(assignments, k) {
  const n = beansData.length;
  const table = Array.from({ length: k }, () => new Int32Array(7));
  const rowSums = new Int32Array(k);
  const colSums = new Int32Array(7);

  for (let i = 0; i < n; i++) {
    const c = assignments[i];
    const v = beansData[i].varietyIndex;
    table[c][v]++;
    rowSums[c]++;
    colSums[v]++;
  }

  const comb2 = (x) => (x * (x - 1)) / 2;
  let sumCombTable = 0;
  for (let c = 0; c < k; c++) {
    for (let v = 0; v < 7; v++) sumCombTable += comb2(table[c][v]);
  }

  let sumCombRows = 0;
  for (let c = 0; c < k; c++) sumCombRows += comb2(rowSums[c]);

  let sumCombCols = 0;
  for (let v = 0; v < 7; v++) sumCombCols += comb2(colSums[v]);

  const totalComb = comb2(n);
  const expectedIndex = (sumCombRows * sumCombCols) / totalComb;
  const maxIndex = 0.5 * (sumCombRows + sumCombCols);
  const denom = maxIndex - expectedIndex;
  return denom === 0 ? 0 : Math.max(0, (sumCombTable - expectedIndex) / denom);
}

function computeSilhouette(assignments, k, dims) {
  const n = beansData.length;
  const step = Math.floor(n / 520);
  const sample = [];
  for (let i = 0; i < n; i += step) sample.push(i);
  const m = sample.length;

  let totalSil = 0, validCount = 0;
  for (let i = 0; i < m; i++) {
    const idxA = sample[i];
    const cA = assignments[idxA];
    const pA = beansData[idxA].pcCurrent;

    const clusterDistSum = new Float64Array(k);
    const clusterCounts = new Int32Array(k);

    for (let j = 0; j < m; j++) {
      if (i === j) continue;
      const idxB = sample[j];
      const cB = assignments[idxB];
      const pB = beansData[idxB].pcCurrent;
      let dist = 0;
      for (let d = 0; d < dims; d++) {
        const diff = pA[d] - pB[d];
        dist += diff * diff;
      }
      clusterDistSum[cB] += Math.sqrt(dist);
      clusterCounts[cB]++;
    }

    if (clusterCounts[cA] === 0) continue;
    const a = clusterDistSum[cA] / clusterCounts[cA];
    let b = Infinity;
    for (let c = 0; c < k; c++) {
      if (c === cA || clusterCounts[c] === 0) continue;
      const meanDist = clusterDistSum[c] / clusterCounts[c];
      if (meanDist < b) b = meanDist;
    }
    if (!isFinite(b)) continue;
    totalSil += (b - a) / Math.max(a, b);
    validCount++;
  }
  return validCount > 0 ? totalSil / validCount : 0;
}

function recomputeAll(animateCentroids = true) {
  updateActiveCoordinates();

  if (animateCentroids && state.kmeansCentroids2D.length === state.k) {
    state.kmeansCentroidsPrev2D = state.kmeansCentroids2D.map(c => ({ ...c }));
    state.kmeansAnimProgress = 0;
  } else {
    state.kmeansCentroidsPrev2D = [];
    state.kmeansAnimProgress = 1;
  }

  const curves = [];
  for (let kVal = 2; kVal <= 10; kVal++) {
    const km = runKMeans(kVal, state.pcaDims);
    const kmed = runKMedoids(kVal, state.pcaDims);
    const ariKm = computeARI(km.assignments, kVal);
    const ariMed = computeARI(kmed.assignments, kVal);
    const silMed = computeSilhouette(kmed.assignments, kVal, state.pcaDims);

    curves.push({ k: kVal, ariMedoids: ariMed, ariKMeans: ariKm, silhouette: silMed });

    if (kVal === state.k) {
      state.kmeansAssignments = km.assignments;
      state.kmeansCentroids2D = km.centroids2D;
      state.kmedoidsAssignments = kmed.assignments;
      state.kmedoidIndices = kmed.medoidIndices;

      const silKm = computeSilhouette(km.assignments, kVal, state.pcaDims);
      state.metrics.kmeansARI = ariKm;
      state.metrics.kmeansSil = silKm;
      state.metrics.kmedoidsARI = ariMed;
      state.metrics.kmedoidsSil = silMed;

      if (!state.outliersInjected && state.standardized) {
        state.metrics.baselineClean = { kmeansARI: ariKm, kmedoidsARI: ariMed };
        state.kmeansCentroidsCleanRef2D = km.centroids2D.map(c => ({ ...c }));
        state.metrics.centroidShift = 0.0;
      } else if (state.kmeansCentroidsCleanRef2D.length === km.centroids2D.length) {
        let maxShift = 0;
        for (let c = 0; c < km.centroids2D.length; c++) {
          const dx = km.centroids2D[c].x - state.kmeansCentroidsCleanRef2D[c].x;
          const dy = km.centroids2D[c].y - state.kmeansCentroidsCleanRef2D[c].y;
          const dist = Math.hypot(dx, dy);
          if (dist > maxShift) maxShift = dist;
        }
        state.metrics.centroidShift = maxShift;
      }
    }
  }

  state.curveByK = curves;
  if (state.selectedMedoidCluster >= state.k) state.selectedMedoidCluster = 0;

  syncControlsFromState();
  updateKpiAndInspectorUI();
  startCentroidAnimation();
  drawMetricsCurveChart();
}
