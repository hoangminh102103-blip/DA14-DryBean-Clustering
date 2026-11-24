/**
 * =========================================================================
 * dry_bean_animation/js/player.js
 * Điều khiển dòng thời gian chậm, cập nhật 8 ô đánh giá liên hoàn, Lý thuyết & Code
 * =========================================================================
 */
(function () {
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let data = null;
  let canvas = null;
  let currentTime = 0;
  let playing = !prefersReduced;
  let speed = 1.0;
  let lastTs = null;
  let lastActId = -1;
  let autoPauseEachAct = false;

  const SVG_PLAY = '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>';
  const SVG_PAUSE = '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';

  function fmtSec(sec) {
    const s = Math.max(0, Math.floor(sec));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
  }

  function findActAt(t) {
    const acts = window.ANIM_STORY;
    for (let i = 0; i < acts.length; i++) {
      if (t <= acts[i].end || i === acts.length - 1) return acts[i];
    }
    return acts[0];
  }

  function buildChapters() {
    const strip = document.getElementById('chapterStrip');
    strip.innerHTML = window.ANIM_STORY.map(st => `
      <button type="button" class="chapter-pill" data-act="${st.id}">
        <span class="chapter-num">0${st.id}</span>${st.shortTitle}
      </button>
    `).join('');

    strip.querySelectorAll('.chapter-pill').forEach(btn => {
      btn.onclick = () => {
        const targetId = Number(btn.dataset.act);
        const found = window.ANIM_STORY.find(s => s.id === targetId);
        if (!found) return;
        currentTime = found.start + 0.05;
        lastActId = -1;
        syncFrame();
      };
    });
  }

  function updatePlayButton() {
    const btn = document.getElementById('btnPlayPause');
    if (playing) {
      btn.classList.add('is-playing');
      btn.innerHTML = `${SVG_PAUSE}<span>Tạm dừng</span>`;
    } else {
      btn.classList.remove('is-playing');
      const atEnd = currentTime >= window.ANIM_TOTAL_DURATION - 0.1;
      btn.innerHTML = `${SVG_PLAY}<span>${atEnd ? 'Phát lại' : 'Tiếp tục'}</span>`;
    }
  }

  function updateChapterHighlights(actId) {
    document.querySelectorAll('.chapter-pill').forEach(el => {
      const id = Number(el.dataset.act);
      el.classList.toggle('active', id === actId);
      el.classList.toggle('done', id < actId);
    });
  }

  function updateMedoidSpotlight(bean, medIdx) {
    const box = document.getElementById('medoidSpotlightCard');
    if (!bean || !bean.features) {
      box.innerHTML = '<div style="color:var(--ink-muted);">Hạt mẫu thật (Medoid) sẽ hiển thị chi tiết 16 số đo vật lý ở Chương 5, 6 &amp; 7.</div>';
      return;
    }
    const f = bean.features;
    const fmt = (x, d = 1) => Number(x).toFixed(d);
    box.innerHTML = `
      <div><strong>M${medIdx + 1} · #Bean_${String(bean.id).padStart(5, '0')}</strong> (Giống thật: <strong>${bean.varietyLabel}</strong>)</div>
      <div class="medoid-mini-grid">
        <div class="medoid-mini-stat"><span>Diện tích (Area)</span><strong>${Number(f.Area).toLocaleString('vi-VN', { maximumFractionDigits: 0 })} px²</strong></div>
        <div class="medoid-mini-stat"><span>Chu vi (Perimeter)</span><strong>${fmt(f.Perimeter, 1)} px</strong></div>
        <div class="medoid-mini-stat"><span>Tỉ lệ dài / rộng</span><strong>${fmt(f.AspectRation, 3)}</strong></div>
        <div class="medoid-mini-stat"><span>Độ tròn (roundness)</span><strong>${fmt(f.roundness, 4)}</strong></div>
      </div>
    `;
  }

  function renderTheoryAndCode(act) {
    const theoryCard = document.getElementById('theoryExplainCard');
    if (theoryCard && act.theory) {
      theoryCard.innerHTML = `
        <div class="explain-head">
          <span class="explain-tag" style="background: var(--blue-pastel);">CƠ CHẾ THEO LÝ THUYẾT</span>
          <span style="font-size:11.5px; color:var(--ink-muted); font-weight:600;">Toán học &amp; Nguyên lý</span>
        </div>
        <div class="explain-subtitle">${act.theory.heading}</div>
        <ol class="explain-points">
          ${act.theory.points.map(p => `<li>${p}</li>`).join('')}
        </ol>
        <div class="explain-math-note"><strong>Điểm mấu chốt:</strong> ${act.theory.mathNote}</div>
      `;
    }

    const codeCard = document.getElementById('codeExplainCard');
    if (codeCard && act.codeExplain) {
      codeCard.innerHTML = `
        <div class="explain-head">
          <span class="explain-tag" style="background: var(--mint);">CƠ CHẾ THEO CODE ĐỒ ÁN</span>
          <code style="font-weight:700;">${act.codeExplain.file}</code>
        </div>
        <div class="explain-subtitle">Hàm thực thi: <code>${act.codeExplain.func}</code></div>
        <pre class="code-snippet-box">${act.codeExplain.snippet.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
        <ul class="explain-points">
          ${act.codeExplain.steps.map(s => `<li>${s}</li>`).join('')}
        </ul>
      `;
    }
  }

  function syncFrame() {
    if (!data || !canvas) return;
    const tele = window.ANIM_RENDERER.renderFrame(canvas, data, currentTime);
    if (!tele) return;

    const { act, localU } = tele;
    if (act.id !== lastActId) {
      lastActId = act.id;
      const badge = document.getElementById('sceneBadge');
      badge.textContent = act.badge;
      badge.style.background = act.badgeBg;
      document.getElementById('sceneTitle').textContent = act.title;
      document.getElementById('formulaBadge').textContent = act.formula;

      const mechBox = document.getElementById('mechanismFlow');
      if (mechBox && act.mechanism) {
        mechBox.innerHTML = `
          <div class="mech-row"><strong>Đầu vào:</strong>${act.mechanism.input}</div>
          <div class="mech-row"><strong>Cơ chế:</strong>${act.mechanism.process}</div>
          <div class="mech-row is-out"><strong>Kết quả:</strong>${act.mechanism.output}</div>
        `;
      }

      document.getElementById('bulletList').innerHTML = act.bullets
        .map(txt => `<li class="step-bullet-item"><span class="bullet-dot"></span><span>${txt}</span></li>`)
        .join('');

      renderTheoryAndCode(act);
      updateChapterHighlights(act.id);

      const overlay = document.getElementById('finaleOverlay');
      overlay.classList.toggle('visible', act.id === 7);
    }

    const phase = act.getPhaseInfo ? act.getPhaseInfo(localU) : { tag: '', caption: '' };
    document.getElementById('narrationPhaseTag').textContent = phase.tag;
    document.getElementById('narrationText').textContent = phase.caption;

    // 8 ô đánh giá liên hoàn bên phải
    document.getElementById('liveBeans').textContent = tele.beanCount.toLocaleString('vi-VN');
    document.getElementById('liveOutlierSub').textContent = `Ngoại lai: ${tele.outlierText}`;
    document.getElementById('liveIter').textContent = tele.iterText;

    document.getElementById('liveAriKm').textContent = tele.ariKm;
    const dKmEl = document.getElementById('liveDeltaKm');
    if (tele.deltaKmText) {
      dKmEl.style.display = 'inline-block';
      dKmEl.style.background = '#FAD0C3';
      dKmEl.style.color = '#7F1D1D';
      dKmEl.textContent = tele.deltaKmText;
    } else {
      dKmEl.style.display = 'none';
    }

    document.getElementById('liveAriMed').textContent = tele.ariMed;
    const dMedEl = document.getElementById('liveDeltaMed');
    if (tele.deltaMedText) {
      dMedEl.style.display = 'inline-block';
      dMedEl.style.background = '#D9F2C6';
      dMedEl.style.color = '#065F46';
      dMedEl.textContent = tele.deltaMedText;
    } else {
      dMedEl.style.display = 'none';
    }

    document.getElementById('liveNmiPair').textContent = tele.nmiMed !== '—'
      ? `${tele.nmiKm} / ${tele.nmiMed}`
      : tele.nmiKm;
    document.getElementById('liveSilPair').textContent = tele.silText !== '—'
      ? `${tele.silKmText} / ${tele.silText}`
      : tele.silKmText;
    document.getElementById('livePurityPair').textContent = tele.purityMed !== '—'
      ? `${tele.purityKm} / ${tele.purityMed}`
      : tele.purityKm;
    document.getElementById('liveCostPair').textContent = tele.l1Text !== '—' && tele.sseText !== '—'
      ? `${tele.sseText} / ${tele.l1Text}`
      : (tele.sseText !== '—' ? `SSE ${tele.sseText}` : '—');
    document.getElementById('liveShift').textContent = tele.shiftText;

    document.getElementById('kpiBoxKm').classList.toggle('is-danger', tele.dangerKm);
    document.getElementById('kpiBoxShift').classList.toggle('is-danger', tele.dangerKm);
    document.getElementById('kpiBoxMed').classList.toggle('is-safe', tele.safeMed);

    // Thanh đánh giá liên tục dưới sân khấu
    const verdictEl = document.getElementById('evalVerdictPill');
    if (verdictEl) {
      verdictEl.textContent = tele.evalVerdict;
      verdictEl.className = 'eval-verdict-pill';
      if (tele.evalTone === 'safe') verdictEl.classList.add('is-safe');
      else if (tele.evalTone === 'warn') verdictEl.classList.add('is-warn');
      else if (tele.evalTone === 'danger') verdictEl.classList.add('is-danger');
    }
    document.getElementById('valBarAri').textContent = `${tele.ariBarPct}%`;
    document.getElementById('fillBarAri').style.width = `${tele.ariBarPct}%`;
    document.getElementById('valBarPurity').textContent = `${tele.purityBarPct}%`;
    document.getElementById('fillBarPurity').style.width = `${tele.purityBarPct}%`;
    document.getElementById('valBarRobust').textContent = `${tele.robustBarPct}%`;
    document.getElementById('fillBarRobust').style.width = `${tele.robustBarPct}%`;

    updateMedoidSpotlight(tele.featuredMedoidBean, tele.featuredMedoidIdx);

    const scrubber = document.getElementById('timelineRange');
    scrubber.value = ((currentTime / window.ANIM_TOTAL_DURATION) * 1000).toFixed(0);
    document.getElementById('timeReadout').textContent = `${fmtSec(currentTime)} / ${fmtSec(window.ANIM_TOTAL_DURATION)}`;
  }

  function stepAnimation(ts) {
    if (lastTs === null) lastTs = ts;
    const dt = Math.min(0.06, (ts - lastTs) / 1000);
    lastTs = ts;

    if (playing) {
      const prevAct = findActAt(currentTime);
      const nextTime = currentTime + dt * speed;

      if (autoPauseEachAct && prevAct && nextTime >= prevAct.end && prevAct.id < window.ANIM_STORY.length) {
        currentTime = prevAct.end - 0.02;
        playing = false;
        updatePlayButton();
        syncFrame();
      } else {
        currentTime = nextTime;
        if (currentTime >= window.ANIM_TOTAL_DURATION) {
          currentTime = window.ANIM_TOTAL_DURATION;
          playing = false;
          updatePlayButton();
        }
        syncFrame();
      }
    }
    requestAnimationFrame(stepAnimation);
  }

  function bindControls() {
    document.getElementById('btnPlayPause').onclick = () => {
      if (currentTime >= window.ANIM_TOTAL_DURATION - 0.05) {
        currentTime = 0;
        lastActId = -1;
      } else if (!playing && autoPauseEachAct) {
        const curAct = findActAt(currentTime);
        if (curAct && currentTime >= curAct.end - 0.05 && curAct.id < window.ANIM_STORY.length) {
          currentTime = curAct.end + 0.05;
        }
      }
      playing = !playing;
      updatePlayButton();
    };

    document.getElementById('btnRestart').onclick = () => {
      currentTime = 0;
      lastActId = -1;
      playing = true;
      updatePlayButton();
      syncFrame();
    };

    document.getElementById('btnPrevAct').onclick = () => {
      const idx = window.ANIM_STORY.findIndex(s => s.id === lastActId);
      const prevIdx = Math.max(0, idx - 1);
      currentTime = window.ANIM_STORY[prevIdx].start + 0.05;
      lastActId = -1;
      syncFrame();
    };

    document.getElementById('btnNextAct').onclick = () => {
      const idx = window.ANIM_STORY.findIndex(s => s.id === lastActId);
      const nextIdx = Math.min(window.ANIM_STORY.length - 1, idx + 1);
      currentTime = window.ANIM_STORY[nextIdx].start + 0.05;
      lastActId = -1;
      syncFrame();
    };

    document.getElementById('timelineRange').addEventListener('input', (e) => {
      const frac = Number(e.target.value) / 1000;
      currentTime = frac * window.ANIM_TOTAL_DURATION;
      lastActId = -1;
      syncFrame();
    });

    document.querySelectorAll('.speed-btn').forEach(btn => {
      btn.onclick = () => {
        speed = Number(btn.dataset.speed);
        document.querySelectorAll('.speed-btn').forEach(b => b.classList.toggle('active', b === btn));
      };
    });

    const chkAutoPause = document.getElementById('chkAutoPauseAct');
    if (chkAutoPause) {
      chkAutoPause.onchange = (e) => { autoPauseEachAct = Boolean(e.target.checked); };
    }

    document.addEventListener('keydown', (e) => {
      if (e.code === 'Space' && e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        document.getElementById('btnPlayPause').click();
      } else if (e.code === 'ArrowRight') {
        document.getElementById('btnNextAct').click();
      } else if (e.code === 'ArrowLeft') {
        document.getElementById('btnPrevAct').click();
      } else if (e.key === 'r' || e.key === 'R') {
        document.getElementById('btnRestart').click();
      }
    });

    window.addEventListener('resize', syncFrame);
  }

  window.addEventListener('DOMContentLoaded', () => {
    canvas = document.getElementById('storyCanvas');
    data = window.ANIM_ENGINE.init();
    buildChapters();
    bindControls();
    updatePlayButton();
    syncFrame();
    requestAnimationFrame(stepAnimation);
  });
})();
