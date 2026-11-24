/**
 * =========================================================================
 * dry_bean_animation/js/engine.js
 * Chạy K-Means++ & K-Medoids (PAM BUILD+SWAP) trên 16 chiều thật,
 * ghi từng vòng lặp kèm đầy đủ chỉ số đánh giá: ARI, NMI, Silhouette, Purity, SSE, L1 Cost
 * =========================================================================
 */
window.ANIM_ENGINE = (function () {
  const OUTLIER_MULTIPLIER = 10.5;
  const DIMS = 16;
  const K = 7;
  const SEED = 20262028;

  let beans = [];
  let realPcaModel = null;
  let benchmark16 = null;
  let histories = null;

  function buildSyntheticFallbackBeans() {
    const rng = createRng(202614);
    const list = [];
    let idCounter = 0;
    VARIETIES.forEach((v, vIdx) => {
      for (let i = 0; i < v.count; i++) {
        const area = Math.max(18500, v.areaMean + gaussianRng(rng) * v.areaStd);
        const aspect = Math.max(1.05, v.aspectMean + gaussianRng(rng) * v.aspectStd);
        const eqD = Math.sqrt((4 * area) / Math.PI);
        const minor = eqD / Math.sqrt(aspect);
        const major = minor * aspect;
        const roundness = Math.min(0.99, Math.max(0.55, v.roundMean + gaussianRng(rng) * 0.026));
        const perimeter = Math.sqrt((4 * Math.PI * area) / roundness);
        const pc = new Float64Array(16);
        pc[0] = (area - 53046) / 14500;
        pc[1] = (aspect - 1.58) * 3.1;
        list.push({
          id: idCounter++,
          variety: v.key,
          varietyLabel: v.label,
          varietyIndex: vIdx,
          features: {
            Area: area,
            Perimeter: perimeter,
            MajorAxisLength: major,
            MinorAxisLength: minor,
            AspectRation: aspect,
            roundness,
            Solidity: v.solidityMean
          },
          pcClean: pc
        });
      }
    });
    return list;
  }

  function loadBeans() {
    const pre = window.DA14_PRELOADED_DATA;
    if (pre && Array.isArray(pre.beans) && pre.beans.length > 0) {
      realPcaModel = pre.pcaModel || null;
      benchmark16 = (pre.benchmarkTable && pre.benchmarkTable['16']) || BENCHMARK_DATA[16];
      beans = pre.beans.map((item, idx) => ({
        id: item.id ?? idx,
        variety: item.variety,
        varietyLabel: item.varietyLabel || item.variety,
        varietyIndex: Math.max(0, VARIETIES.findIndex(v => v.key === item.variety)),
        isOutlierCandidate: false,
        features: item.features,
        rawArea: Number(item.features.Area),
        rawAspect: Number(item.features.AspectRation),
        pcClean: Float64Array.from(item.pc),
        pcOutlier: null,
        rawCoord: [0, 0],
        zCoord: [0, 0]
      }));
    } else {
      benchmark16 = BENCHMARK_DATA[16];
      beans = buildSyntheticFallbackBeans().map((item) => ({
        ...item,
        isOutlierCandidate: false,
        rawArea: item.features.Area,
        rawAspect: item.features.AspectRation,
        pcOutlier: null,
        rawCoord: [0, 0],
        zCoord: [0, 0]
      }));
    }

    let outCount = 0;
    const step = Math.floor(beans.length / 136);
    for (let i = 0; i < beans.length; i++) {
      const mark = (outCount < 136) && (i % step === 0);
      beans[i].isOutlierCandidate = mark;
      if (mark) outCount++;
    }

    let minArea = Infinity, maxArea = -Infinity;
    let sumArea = 0, sumAspect = 0;
    for (let i = 0; i < beans.length; i++) {
      const a = beans[i].rawArea;
      const asp = beans[i].rawAspect;
      if (a < minArea) minArea = a;
      if (a > maxArea) maxArea = a;
      sumArea += a;
      sumAspect += asp;
    }
    const meanArea = sumArea / beans.length;
    const meanAspect = sumAspect / beans.length;
    let varArea = 0, varAspect = 0;
    for (let i = 0; i < beans.length; i++) {
      varArea += (beans[i].rawArea - meanArea) ** 2;
      varAspect += (beans[i].rawAspect - meanAspect) ** 2;
    }
    const stdArea = Math.sqrt(varArea / beans.length) || 1;
    const stdAspect = Math.sqrt(varAspect / beans.length) || 1;
    const spanArea = (maxArea - minArea) || 1;

    for (let i = 0; i < beans.length; i++) {
      const b = beans[i];
      b.rawCoord = [
        -5.2 + ((b.rawArea - minArea) / spanArea) * 16.0,
        ((b.rawAspect - meanAspect) / stdAspect) * 0.22
      ];
      b.zCoord = [
        ((b.rawArea - meanArea) / stdArea) * 1.1,
        ((b.rawAspect - meanAspect) / stdAspect) * 1.35
      ];
      b.pcaOutlier = [b.pcClean[0], b.pcClean[1]];

      if (!b.isOutlierCandidate) {
        b.pcOutlier = b.pcClean;
      } else if (realPcaModel && Array.isArray(realPcaModel.mean) && realPcaModel.components) {
        const { mean, std, components } = realPcaModel;
        const z = new Float64Array(DIMS);
        for (let j = 0; j < DIMS; j++) {
          const key = FEATURE_META[j].key;
          const rawVal = j === 0 ? Number(b.features[key]) * OUTLIER_MULTIPLIER : Number(b.features[key]);
          z[j] = (rawVal - mean[j]) / std[j];
        }
        const out = new Float64Array(DIMS);
        for (let d = 0; d < DIMS; d++) {
          let s = 0;
          for (let j = 0; j < DIMS; j++) s += z[j] * components[d][j];
          out[d] = s;
        }
        b.pcOutlier = out;
        b.pcaOutlier = [out[0], out[1]];
      } else {
        const out = Float64Array.from(b.pcClean);
        out[0] += 24.0 + (i % 5);
        out[1] += 2.2;
        b.pcOutlier = out;
        b.pcaOutlier = [out[0], out[1]];
      }
    }
  }

  function computeClusterMetrics(assignments) {
    const n = beans.length;
    const table = Array.from({ length: K }, () => new Int32Array(7));
    const rowSums = new Int32Array(K);
    const colSums = new Int32Array(7);
    for (let i = 0; i < n; i++) {
      const c = assignments[i];
      const v = beans[i].varietyIndex;
      table[c][v]++;
      rowSums[c]++;
      colSums[v]++;
    }

    // 1. ARI
    const comb2 = (x) => (x * (x - 1)) / 2;
    let sumTable = 0, sumRows = 0, sumCols = 0;
    let purityHits = 0;
    for (let c = 0; c < K; c++) {
      sumRows += comb2(rowSums[c]);
      let maxInCluster = 0;
      for (let v = 0; v < 7; v++) {
        sumTable += comb2(table[c][v]);
        if (table[c][v] > maxInCluster) maxInCluster = table[c][v];
      }
      purityHits += maxInCluster;
    }
    for (let v = 0; v < 7; v++) sumCols += comb2(colSums[v]);
    const total = comb2(n);
    const expected = (sumRows * sumCols) / total;
    const denom = 0.5 * (sumRows + sumCols) - expected;
    const ari = denom === 0 ? 0 : Math.max(0, (sumTable - expected) / denom);

    // 2. NMI (Normalized Mutual Information - arithmetic average normalization)
    let hc = 0, hy = 0, mi = 0;
    for (let c = 0; c < K; c++) {
      if (rowSums[c] > 0) {
        const p = rowSums[c] / n;
        hc -= p * Math.log(p);
      }
    }
    for (let v = 0; v < 7; v++) {
      if (colSums[v] > 0) {
        const p = colSums[v] / n;
        hy -= p * Math.log(p);
      }
    }
    for (let c = 0; c < K; c++) {
      for (let v = 0; v < 7; v++) {
        const cnt = table[c][v];
        if (cnt > 0) {
          const pxy = cnt / n;
          const px = rowSums[c] / n;
          const py = colSums[v] / n;
          mi += pxy * Math.log(pxy / (px * py));
        }
      }
    }
    const nmi = (hc + hy) > 0 ? Math.max(0, (2 * mi) / (hc + hy)) : 0;

    // 3. Purity
    const purity = n > 0 ? purityHits / n : 0;

    return { ari, nmi, purity };
  }

  function computeSilhouetteSampled(assignments, useOutlier) {
    const n = beans.length;
    const step = Math.max(1, Math.floor(n / 220));
    const sample = [];
    for (let i = 0; i < n; i += step) sample.push(i);
    const m = sample.length;
    let totalSil = 0, valid = 0;
    for (let i = 0; i < m; i++) {
      const idxA = sample[i];
      const cA = assignments[idxA];
      const pA = useOutlier ? beans[idxA].pcOutlier : beans[idxA].pcClean;
      const distSum = new Float64Array(K);
      const cnt = new Int32Array(K);
      for (let j = 0; j < m; j++) {
        if (i === j) continue;
        const idxB = sample[j];
        const cB = assignments[idxB];
        const pB = useOutlier ? beans[idxB].pcOutlier : beans[idxB].pcClean;
        let d2 = 0;
        for (let d = 0; d < DIMS; d++) {
          const diff = pA[d] - pB[d];
          d2 += diff * diff;
        }
        distSum[cB] += Math.sqrt(d2);
        cnt[cB]++;
      }
      if (cnt[cA] === 0) continue;
      const a = distSum[cA] / cnt[cA];
      let b = Infinity;
      for (let c = 0; c < K; c++) {
        if (c === cA || cnt[c] === 0) continue;
        const avg = distSum[c] / cnt[c];
        if (avg < b) b = avg;
      }
      if (!isFinite(b)) continue;
      totalSil += (b - a) / Math.max(a, b);
      valid++;
    }
    return valid > 0 ? totalSil / valid : 0;
  }

  function assignAndCostND(centers, useOutlier) {
    const n = beans.length;
    const assign = new Int32Array(n);
    let sse = 0;
    let l1 = 0;
    for (let i = 0; i < n; i++) {
      const p = useOutlier ? beans[i].pcOutlier : beans[i].pcClean;
      let bestC = 0, bestDistSq = Infinity;
      for (let c = 0; c < K; c++) {
        const cent = centers[c];
        let dSq = 0;
        for (let d = 0; d < DIMS; d++) {
          const diff = p[d] - cent[d];
          dSq += diff * diff;
        }
        if (dSq < bestDistSq) { bestDistSq = dSq; bestC = c; }
      }
      assign[i] = bestC;
      sse += bestDistSq;
      l1 += Math.sqrt(bestDistSq);
    }
    return { assign, sse, l1 };
  }

  function maxShift16D(centers, cleanRef) {
    if (!cleanRef || cleanRef.length !== K) return 0;
    let maxS = 0;
    for (let i = 0; i < K; i++) {
      let bestD = Infinity;
      for (let j = 0; j < K; j++) {
        let s = 0;
        for (let d = 0; d < DIMS; d++) {
          const diff = centers[i][d] - cleanRef[j][d];
          s += diff * diff;
        }
        const dist = Math.sqrt(s);
        if (dist < bestD) bestD = dist;
      }
      if (bestD > maxS) maxS = bestD;
    }
    return maxS;
  }

  function runKMeansHistory(useOutlier, cleanRef = null) {
    const n = beans.length;
    const rng = createRng(SEED);
    const vec = (i) => (useOutlier ? beans[i].pcOutlier : beans[i].pcClean);

    let centroids = [Float64Array.from(vec(Math.floor(rng() * n)))];
    const minD = new Float64Array(n).fill(Infinity);
    for (let c = 1; c < K; c++) {
      let sumD = 0;
      const prev = centroids[c - 1];
      for (let i = 0; i < n; i++) {
        const p = vec(i);
        let dSq = 0;
        for (let d = 0; d < DIMS; d++) {
          const diff = p[d] - prev[d];
          dSq += diff * diff;
        }
        if (dSq < minD[i]) minD[i] = dSq;
        sumD += minD[i];
      }
      let target = rng() * sumD;
      let pick = 0;
      for (let i = 0; i < n; i++) {
        target -= minD[i];
        if (target <= 0) { pick = i; break; }
      }
      centroids.push(Float64Array.from(vec(pick)));
    }
    centroids.sort((a, b) => a[0] - b[0]);

    const to2D = (arr) => arr.map(c => ({ x: c[0], y: c[1] }));
    const frames = [];
    const counts = new Int32Array(K);
    const sums = Array.from({ length: K }, () => new Float64Array(DIMS));

    const ac0 = assignAndCostND(centroids, useOutlier);
    const met0 = computeClusterMetrics(ac0.assign);
    frames.push({
      iter: 0,
      centroidsND: centroids.map(c => Float64Array.from(c)),
      centroids: to2D(centroids),
      assignments: ac0.assign,
      ari: met0.ari,
      nmi: met0.nmi,
      purity: met0.purity,
      sse: ac0.sse,
      l1Cost: ac0.l1,
      sil: computeSilhouetteSampled(ac0.assign, useOutlier),
      shift: maxShift16D(centroids, cleanRef)
    });

    for (let iter = 1; iter <= 12; iter++) {
      counts.fill(0);
      for (let c = 0; c < K; c++) sums[c].fill(0);
      const prevAssign = frames[frames.length - 1].assignments;

      for (let i = 0; i < n; i++) {
        const c = prevAssign[i];
        const p = vec(i);
        counts[c]++;
        for (let d = 0; d < DIMS; d++) sums[c][d] += p[d];
      }

      let maxMove = 0;
      centroids = centroids.map((c, idx) => {
        if (counts[idx] === 0) return c;
        const nextC = new Float64Array(DIMS);
        let mvSq = 0;
        for (let d = 0; d < DIMS; d++) {
          nextC[d] = sums[idx][d] / counts[idx];
          const diff = nextC[d] - c[d];
          mvSq += diff * diff;
        }
        const mv = Math.sqrt(mvSq);
        if (mv > maxMove) maxMove = mv;
        return nextC;
      });

      const ac = assignAndCostND(centroids, useOutlier);
      const met = computeClusterMetrics(ac.assign);
      frames.push({
        iter,
        centroidsND: centroids.map(c => Float64Array.from(c)),
        centroids: to2D(centroids),
        assignments: ac.assign,
        ari: met.ari,
        nmi: met.nmi,
        purity: met.purity,
        sse: ac.sse,
        l1Cost: ac.l1,
        sil: computeSilhouetteSampled(ac.assign, useOutlier),
        shift: maxShift16D(centroids, cleanRef)
      });

      if (maxMove < 0.03 && iter >= 5) break;
    }

    return frames;
  }

  function runPamCleanHistory() {
    const n = beans.length;
    const vec = (i) => beans[i].pcClean;
    const step = Math.floor(n / 350);
    const sIdx = [];
    for (let i = 0; i < n; i += step) sIdx.push(i);
    const m = sIdx.length;

    const D = new Float64Array(m * m);
    for (let i = 0; i < m; i++) {
      const pi = vec(sIdx[i]);
      for (let j = i + 1; j < m; j++) {
        const pj = vec(sIdx[j]);
        let d2 = 0;
        for (let d = 0; d < DIMS; d++) {
          const diff = pi[d] - pj[d];
          d2 += diff * diff;
        }
        const dd = Math.sqrt(d2);
        D[i * m + j] = dd;
        D[j * m + i] = dd;
      }
    }

    const toCoords2D = (idxArr) => idxArr.map(idx => {
      const p = vec(idx);
      return { x: p[0], y: p[1], beanIdx: idx };
    });

    const recordFrame = (iter, medLoc) => {
      const ordered = [...medLoc].sort((a, b) => vec(sIdx[a])[0] - vec(sIdx[b])[0]);
      const medGlob = ordered.map(li => sIdx[li]);
      const ac = assignAndCostND(medGlob.map(g => vec(g)), false);
      const met = computeClusterMetrics(ac.assign);
      return {
        iter,
        medoids: medGlob,
        medoidCoords: toCoords2D(medGlob),
        assignments: ac.assign,
        ari: met.ari,
        nmi: met.nmi,
        purity: met.purity,
        sse: ac.sse,
        l1Cost: ac.l1,
        sil: computeSilhouetteSampled(ac.assign, false)
      };
    };

    const frames = [];
    const initStub = [0, 50, 100, 150, 200, 250, 300].map(v => v % m);
    frames.push(recordFrame(0, initStub));

    let best0 = 0, bestS0 = Infinity;
    for (let i = 0; i < m; i++) {
      let s = 0;
      for (let j = 0; j < m; j++) s += D[i * m + j];
      if (s < bestS0) { bestS0 = s; best0 = i; }
    }
    const medLocal = [best0];
    const minDist = new Float64Array(m);
    for (let j = 0; j < m; j++) minDist[j] = D[best0 * m + j];

    for (let c = 1; c < K; c++) {
      let ba = -1, bg = -1;
      for (let i = 0; i < m; i++) {
        if (medLocal.includes(i)) continue;
        let g = 0;
        for (let j = 0; j < m; j++) {
          const df = minDist[j] - D[i * m + j];
          if (df > 0) g += df;
        }
        if (g > bg) { bg = g; ba = i; }
      }
      medLocal.push(ba);
      for (let j = 0; j < m; j++) {
        const d = D[ba * m + j];
        if (d < minDist[j]) minDist[j] = d;
      }
    }
    frames.push(recordFrame(1, medLocal));

    for (let sw = 2; sw <= 6; sw++) {
      let bg = 0, sm = -1, so = -1;
      const d1 = new Float64Array(m), d2 = new Float64Array(m), c1 = new Int32Array(m);
      for (let j = 0; j < m; j++) {
        let v1 = Infinity, v2 = Infinity, i1 = 0;
        for (let c = 0; c < K; c++) {
          const dd = D[medLocal[c] * m + j];
          if (dd < v1) { v2 = v1; v1 = dd; i1 = c; }
          else if (dd < v2) v2 = dd;
        }
        d1[j] = v1; d2[j] = v2; c1[j] = i1;
      }
      for (let c = 0; c < K; c++) {
        for (let h = 0; h < m; h++) {
          if (medLocal.includes(h)) continue;
          let dl = 0;
          for (let j = 0; j < m; j++) {
            const dh = D[h * m + j];
            if (c1[j] === c) dl += Math.min(d2[j], dh) - d1[j];
            else if (dh < d1[j]) dl += dh - d1[j];
          }
          if (dl < bg) { bg = dl; sm = c; so = h; }
        }
      }
      if (sm !== -1 && bg < -1e-4) {
        medLocal[sm] = so;
        frames.push(recordFrame(sw, medLocal));
      } else break;
    }

    return frames;
  }

  function runPamOutlierHistory(cleanMedoids) {
    const n = beans.length;
    const vec = (i) => beans[i].pcOutlier;
    const sOut = [];
    for (let i = 0; i < n; i += 9) sOut.push(i);

    let outMed = [...cleanMedoids];
    const makeFrame = (iter, medArr) => {
      const ordered = [...medArr].sort((a, b) => vec(a)[0] - vec(b)[0]);
      const ac = assignAndCostND(ordered.map(g => vec(g)), true);
      const met = computeClusterMetrics(ac.assign);
      return {
        iter,
        medoids: ordered,
        medoidCoords: ordered.map(idx => {
          const p = vec(idx);
          return { x: p[0], y: p[1], beanIdx: idx };
        }),
        assignments: ac.assign,
        ari: met.ari,
        nmi: met.nmi,
        purity: met.purity,
        sse: ac.sse,
        l1Cost: ac.l1,
        sil: computeSilhouetteSampled(ac.assign, true)
      };
    };

    const frames = [makeFrame(0, outMed)];
    for (let it = 1; it <= 3; it++) {
      const members = Array.from({ length: K }, () => []);
      for (let si = 0; si < sOut.length; si++) {
        const idx = sOut[si];
        let bc = 0, bd = Infinity;
        const p = vec(idx);
        for (let c = 0; c < K; c++) {
          const mp = vec(outMed[c]);
          let d2 = 0;
          for (let d = 0; d < DIMS; d++) {
            const diff = p[d] - mp[d];
            d2 += diff * diff;
          }
          if (d2 < bd) { bd = d2; bc = c; }
        }
        members[bc].push(idx);
      }

      const nextMed = [...outMed];
      for (let c = 0; c < K; c++) {
        const grp = members[c];
        if (grp.length === 0) continue;
        let bestCand = outMed[c], bestCost = Infinity;
        for (let a = 0; a < grp.length; a++) {
          const ci = grp[a];
          const p1 = vec(ci);
          let cost = 0;
          for (let b = 0; b < grp.length; b++) {
            const p2 = vec(grp[b]);
            let d2 = 0;
            for (let d = 0; d < DIMS; d++) {
              const diff = p1[d] - p2[d];
              d2 += diff * diff;
            }
            cost += Math.sqrt(d2);
          }
          if (cost < bestCost) { bestCost = cost; bestCand = ci; }
        }
        nextMed[c] = bestCand;
      }
      outMed = nextMed;
      frames.push(makeFrame(it, outMed));
    }
    return frames;
  }

  function init() {
    if (histories) return histories;
    loadBeans();

    const kmClean = runKMeansHistory(false, null);
    const cleanFinal = kmClean[kmClean.length - 1];
    const kmOutlierRaw = runKMeansHistory(true, cleanFinal.centroidsND);

    const kmOutlier = [
      {
        ...cleanFinal,
        iter: 0,
        shift: 0
      },
      ...kmOutlierRaw.map((fr, idx) => ({ ...fr, iter: idx + 1 }))
    ];

    const pamClean = runPamCleanHistory();
    const cleanMedoids = pamClean[pamClean.length - 1].medoids;
    const pamOutlier = runPamOutlierHistory(cleanMedoids);

    histories = {
      beans,
      totalCount: beans.length,
      outlierCount: beans.reduce((acc, b) => acc + (b.isOutlierCandidate ? 1 : 0), 0),
      benchmark16,
      kmClean,
      kmOutlier,
      pamClean,
      pamOutlier
    };
    return histories;
  }

  return { init };
})();
