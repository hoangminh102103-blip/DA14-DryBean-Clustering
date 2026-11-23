/**
 * =========================================================================
 * data.js — SINH DỮ LIỆU 13.611 HẠT ĐẬU & BIẾN ĐỔI TỌA ĐỘ THEO CẤU HÌNH
 * =========================================================================
 */
function generateDryBeanDataset() {
  const rng = createRng(202614);
  const rawBeans = [];
  let idCounter = 0;

  VARIETIES.forEach((v, vIdx) => {
    for (let i = 0; i < v.count; i++) {
      const area = Math.max(18500, v.areaMean + gaussianRng(rng) * v.areaStd);
      const aspect = Math.max(1.05, v.aspectMean + gaussianRng(rng) * v.aspectStd);
      const equivDiameter = Math.sqrt((4 * area) / Math.PI);
      const minorAxis = equivDiameter / Math.sqrt(aspect);
      const majorAxis = minorAxis * aspect;

      const roundness = Math.min(0.99, Math.max(0.55, v.roundMean + gaussianRng(rng) * 0.026));
      const perimeter = Math.sqrt((4 * Math.PI * area) / roundness);
      const solidity = Math.min(0.998, Math.max(0.93, v.solidityMean + gaussianRng(rng) * 0.005));
      const convexArea = area / solidity;
      const eccentricity = Math.sqrt(Math.max(0.01, 1 - 1 / (aspect * aspect)));
      const compactness = equivDiameter / majorAxis;
      const extent = Math.min(0.86, Math.max(0.58, 0.75 + (roundness - 0.88) * 0.35 + gaussianRng(rng) * 0.035));

      const sf1 = majorAxis / area;
      const sf2 = minorAxis / area;
      const sf3 = area / (Math.pow(majorAxis / 2, 2) * Math.PI);
      const sf4 = area / ((majorAxis / 2) * (minorAxis / 2) * Math.PI * (0.996 + gaussianRng(rng) * 0.003));

      const features = {
        Area: area,
        Perimeter: perimeter,
        MajorAxisLength: majorAxis,
        MinorAxisLength: minorAxis,
        AspectRation: aspect,
        Eccentricity: eccentricity,
        ConvexArea: convexArea,
        EquivDiameter: equivDiameter,
        Extent: extent,
        Solidity: solidity,
        roundness: roundness,
        Compactness: compactness,
        ShapeFactor1: sf1,
        ShapeFactor2: sf2,
        ShapeFactor3: sf3,
        ShapeFactor4: sf4
      };

      rawBeans.push({
        id: idCounter++,
        variety: v.key,
        varietyLabel: v.label,
        varietyIndex: vIdx,
        isOutlier: false,
        isOutlierCandidate: false,
        features,
        stdFeatures: new Float64Array(16),
        rawFeaturesArr: new Float64Array(16),
        pcClean: new Float64Array(16),
        pcCurrent: new Float64Array(16)
      });
    }
  });

  // Xáo trộn xác định
  for (let i = rawBeans.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const tmp = rawBeans[i];
    rawBeans[i] = rawBeans[j];
    rawBeans[j] = tmp;
  }

  // Đánh dấu đúng 1% hạt (136 hạt) làm ứng viên tiêm ngoại lai
  const outlierCount = Math.round(rawBeans.length * 0.01);
  for (let i = 0; i < outlierCount; i++) {
    const idx = Math.floor((i + 0.5) * (rawBeans.length / outlierCount));
    rawBeans[idx].isOutlierCandidate = true;
  }

  // Tính mean & std chuẩn hóa
  FEATURE_META.forEach((f, fIdx) => {
    let sum = 0, minVal = Infinity, maxVal = -Infinity;
    for (let i = 0; i < rawBeans.length; i++) {
      const val = rawBeans[i].features[f.key];
      rawBeans[i].rawFeaturesArr[fIdx] = val;
      sum += val;
      if (val < minVal) minVal = val;
      if (val > maxVal) maxVal = val;
    }
    const mean = sum / rawBeans.length;
    let sqSum = 0;
    for (let i = 0; i < rawBeans.length; i++) {
      const d = rawBeans[i].rawFeaturesArr[fIdx] - mean;
      sqSum += d * d;
    }
    const std = Math.sqrt(sqSum / rawBeans.length) || 1;
    featureStats[f.key] = { mean, std, min: minVal, max: maxVal };

    for (let i = 0; i < rawBeans.length; i++) {
      rawBeans[i].stdFeatures[fIdx] = (rawBeans[i].rawFeaturesArr[fIdx] - mean) / std;
    }
  });

  // Chiếu PCA
  const wPC1 = [0.33, 0.33, 0.31, 0.30, 0.06, 0.05, 0.33, 0.33, -0.04, -0.06, -0.14, -0.07, -0.31, -0.32, -0.07, -0.04];
  const wPC2 = [-0.05, 0.12, 0.25, -0.22, 0.44, 0.42, -0.05, -0.06, -0.18, -0.15, -0.43, -0.44, 0.14, -0.25, -0.43, -0.14];
  const wPC3 = [0.04, -0.08, 0.02, 0.05, -0.03, -0.02, 0.01, 0.04, 0.58, 0.62, 0.22, 0.03, -0.02, 0.02, 0.03, 0.45];
  const wPC4 = [0.08, 0.14, -0.05, 0.15, -0.12, 0.18, 0.09, 0.08, -0.52, 0.48, -0.28, 0.15, 0.05, -0.11, 0.14, 0.49];

  for (let i = 0; i < rawBeans.length; i++) {
    const z = rawBeans[i].stdFeatures;
    let p1 = 0, p2 = 0, p3 = 0, p4 = 0;
    for (let j = 0; j < 16; j++) {
      p1 += z[j] * wPC1[j];
      p2 += z[j] * wPC2[j];
      p3 += z[j] * wPC3[j];
      p4 += z[j] * wPC4[j];
    }
    rawBeans[i].pcClean[0] = p1;
    rawBeans[i].pcClean[1] = p2;
    rawBeans[i].pcClean[2] = p3;
    rawBeans[i].pcClean[3] = p4;
    for (let d = 4; d < 16; d++) {
      rawBeans[i].pcClean[d] = z[d] * Math.sqrt(PCA_VARIANCE_RATIO[d]);
    }
  }

  beansData = rawBeans;
}

function updateActiveCoordinates() {
  const outlierMultiplier = 10.5;
  for (let i = 0; i < beansData.length; i++) {
    const b = beansData[i];
    const isOut = state.outliersInjected && b.isOutlierCandidate;
    b.isOutlier = isOut;

    if (state.standardized) {
      if (!isOut) {
        for (let d = 0; d < 16; d++) b.pcCurrent[d] = b.pcClean[d];
      } else if (window.REAL_PCA_MODEL) {
        // Nhân cột Area (index 0) rồi chuẩn hóa & chiếu lại qua PCA thật giống Python
        const { mean, std, components } = window.REAL_PCA_MODEL;
        const z = new Float64Array(16);
        for (let j = 0; j < 16; j++) {
          const rawVal = j === 0 ? b.rawFeaturesArr[0] * outlierMultiplier : b.rawFeaturesArr[j];
          z[j] = (rawVal - mean[j]) / std[j];
        }
        for (let d = 0; d < 16; d++) {
          let sum = 0;
          for (let j = 0; j < 16; j++) sum += z[j] * components[d][j];
          b.pcCurrent[d] = sum;
        }
      } else {
        // Dự phòng khi chưa nạp file JSON thật
        b.pcCurrent[0] = b.pcClean[0] + 25.0 + (i % 7) * 1.1;
        b.pcCurrent[1] = b.pcClean[1] + 2.6;
        for (let d = 2; d < 16; d++) b.pcCurrent[d] = b.pcClean[d] * 1.35;
      }
    } else {
      // Tắt chuẩn hóa -> Thang đo Area thống trị tuyệt đối, nén trục hình dáng
      const rawArea = isOut ? b.features.Area * outlierMultiplier : b.features.Area;
      b.pcCurrent[0] = (rawArea - 53000) / 14500;
      b.pcCurrent[1] = b.pcClean[1] * 0.04;
      for (let d = 2; d < 16; d++) b.pcCurrent[d] = b.pcClean[d] * 0.01;
    }
  }
}