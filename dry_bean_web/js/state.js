/**
 * =========================================================================
 * state.js — QUẢN LÝ TRẠNG THÁI ỨNG DỤNG TẬP TRUNG
 * =========================================================================
 */
let beansData = [];
let featureStats = {};

const state = {
  activeScreen: 6,
  guidedStep: 1,
  k: 7,
  pcaDims: 2,
  outliersInjected: false,
  standardized: true,
  selectedVariety: null,
  selectedMedoidCluster: 0,

  kmeansAssignments: new Int32Array(TOTAL_BEANS),
  kmedoidsAssignments: new Int32Array(TOTAL_BEANS),
  kmeansCentroids2D: [],
  kmeansCentroidsCleanRef2D: [],
  kmeansCentroidsPrev2D: [],
  kmeansAnimProgress: 1,
  kmedoidIndices: [],
  hoveredMedoidIdx: -1,

  metrics: {
    kmeansARI: 0.674,
    kmeansSil: 0.438,
    kmedoidsARI: 0.669,
    kmedoidsSil: 0.431,
    centroidShift: 0.0,
    baselineClean: {
      kmeansARI: 0.674,
      kmedoidsARI: 0.669
    }
  },

  curveByK: [],
  hoveredCurveK: null,

  viewport: {
    scale: 1.0,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    dragMoved: false
  },

  edaFeature: 'Area',
  edaZscore: false,
  expDim: 2,
  mechOutlier: true,
  mechIter: 2
};
