/**
 * =========================================================================
 * main.js — KHỞI CHẠY ỨNG DỤNG & ĐĂNG KÝ SỰ KIỆN TƯƠNG TÁC
 * =========================================================================
 */
function bindAllUiListeners() {
  document.getElementById('btnMobileSidebar').onclick = () => {
    document.getElementById('leftSidebar').classList.toggle('mobile-open');
  };

  document.getElementById('sliderK').addEventListener('input', (e) => {
    state.k = Number(e.target.value);
    recomputeAll(true);
  });

  document.getElementById('sliderPCA').addEventListener('input', (e) => {
    state.pcaDims = Number(e.target.value);
    recomputeAll(true);
  });

  const toggleOutlierAction = () => {
    state.outliersInjected = !state.outliersInjected;
    recomputeAll(true);
  };
  document.getElementById('btnQuickOutlier').onclick = toggleOutlierAction;
  document.getElementById('btnSidebarOutlier').onclick = toggleOutlierAction;

  document.getElementById('toggleStandardizeBox').onclick = () => {
    state.standardized = !state.standardized;
    recomputeAll(true);
  };

  document.getElementById('btnQuickReset').onclick = () => {
    state.viewport.scale = 1.0;
    state.viewport.offsetX = 0;
    state.viewport.offsetY = 0;
    document.getElementById('zoomBadge').textContent = '1.0×';
    activateGuidedStep(1);
  };

  document.getElementById('btnPrevStep').onclick = () => {
    const prev = state.guidedStep > 1 ? state.guidedStep - 1 : 6;
    activateGuidedStep(prev);
  };

  document.getElementById('btnNextStep').onclick = () => {
    const next = state.guidedStep < 6 ? state.guidedStep + 1 : 1;
    activateGuidedStep(next);
  };

  // Modal Data Adapter
  const modal = document.getElementById('adapterModal');
  document.getElementById('btnOpenAdapter').onclick = () => modal.classList.add('open');
  document.getElementById('btnCloseAdapter').onclick = () => modal.classList.remove('open');
  modal.onclick = (e) => { if (e.target === modal) modal.classList.remove('open'); };

  document.getElementById('jsonFileInput').onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target.result);
        window.DA14_DATA_ADAPTER.loadFromResults(parsed);
        document.getElementById('adapterLoadStatus').textContent = `✓ Đã nạp thành công từ ${file.name}!`;
      } catch (err) {
        document.getElementById('adapterLoadStatus').textContent = '✗ Tệp JSON không đúng định dạng.';
      }
    };
    reader.readAsText(file);
  };

  window.addEventListener('resize', () => {
    if (state.activeScreen === 6) {
      renderBothScatterCanvases();
      drawMetricsCurveChart();
    } else if (state.activeScreen === 2) drawEdaBoxplot();
    else if (state.activeScreen === 3) drawPcaScreeChart();
    else if (state.activeScreen === 4) drawMechanismDemoCanvas();
  });
}

window.addEventListener('DOMContentLoaded', () => {
  generateDryBeanDataset();
  initScreen1Content();
  initScreen2Content();
  initScreen4Mechanism();
  renderBenchmarkTable();
  buildTimelineSteps();
  bindAllUiListeners();
  bindSynchronizedCanvasControls(canvasKMeans, false);
  bindSynchronizedCanvasControls(canvasKMedoids, true);
  bindCurveChartEvents();

  recomputeAll(false);
  switchScreen(6);

  fetch('./web_data_buoc1_2.json')
    .then(res => res.ok ? res.json() : null)
    .then(data => {
      if (data) window.DA14_DATA_ADAPTER.loadFromResults(data);
    })
    .catch(() => {});
    
});
