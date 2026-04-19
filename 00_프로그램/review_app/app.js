const state = {
  library: null,
  staticMode: false,
  current: {
    unit: null,
    category: null,
    sourceStem: null,
    page: null,
  },
  currentPagePayload: null,
};

const PREFERRED_UNITS = ["\ubc30", "\uac00\uc2b4", "\ub4f1"];
const PREFERRED_CATEGORIES = ["\ud604\uc7ac\ud1b5\ud569", "\ud1b5\ud569", "\ud544\uae30\ubcf8", "\uac15\uc758\uc6d0\ubcf8"];

const unitSelect = document.getElementById("unitSelect");
const categorySelect = document.getElementById("categorySelect");
const sourceSelect = document.getElementById("sourceSelect");
const pageList = document.getElementById("pageList");
const pageStats = document.getElementById("pageStats");
const sourceSummary = document.getElementById("sourceSummary");
const reviewImage = document.getElementById("reviewImage");
const openImageLink = document.getElementById("openImageLink");
const analysisSummary = document.getElementById("analysisSummary");
const noteTextStatus = document.getElementById("noteTextStatus");
const noteCorrectedText = document.getElementById("noteCorrectedText");
const noteSupplementalText = document.getElementById("noteSupplementalText");
const lectureTextStatus = document.getElementById("lectureTextStatus");
const lectureCorrectedText = document.getElementById("lectureCorrectedText");
const propositionStatus = document.getElementById("propositionStatus");
const coursePropositions = document.getElementById("coursePropositions");
const noteInferencePropositions = document.getElementById("noteInferencePropositions");
const canonicalPropositions = document.getElementById("canonicalPropositions");
const supportivePropositions = document.getElementById("supportivePropositions");
const unresolvedNotes = document.getElementById("unresolvedNotes");
const questionCount = document.getElementById("questionCount");
const questionList = document.getElementById("questionList");
const prevPageButton = document.getElementById("prevPageButton");
const nextPageButtonTop = document.getElementById("nextPageButtonTop");
const nextPageButtonBottom = document.getElementById("nextPageButtonBottom");
const refreshButton = document.getElementById("refreshButton");
const questionCardTemplate = document.getElementById("questionCardTemplate");

async function fetchJson(url) {
  if (url.startsWith("/api/") && state.staticMode) {
    return fetchStaticJson(url);
  }

  try {
    return await fetchNetworkJson(url);
  } catch (error) {
    if (!url.startsWith("/api/")) {
      throw error;
    }
    state.staticMode = true;
    return fetchStaticJson(url);
  }
}

async function fetchNetworkJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function fetchStaticJson(apiUrl) {
  const parsed = new URL(apiUrl, window.location.origin);
  if (parsed.pathname === "/api/library") {
    return fetchNetworkJson("./data/library.json");
  }
  if (parsed.pathname === "/api/refresh") {
    return { status: "static_bundle", refreshed: false };
  }
  if (parsed.pathname === "/api/page") {
    const pageNumber = Number(parsed.searchParams.get("page"));
    const sourceEntry = getCurrentSourceEntry();
    const pageEntry = sourceEntry?.pages.find((page) => Number(page.page_number) === pageNumber);
    if (!pageEntry?.static_page_file) {
      throw new Error("Static page payload not found");
    }
    return fetchNetworkJson(`./data/${pageEntry.static_page_file}`);
  }
  throw new Error(`Unsupported static API route: ${parsed.pathname}`);
}

function getCurrentUnitEntry() {
  return state.library?.units.find((item) => item.unit === state.current.unit) || null;
}

function getCurrentCategoryEntry() {
  const unitEntry = getCurrentUnitEntry();
  return unitEntry?.categories.find((item) => item.category === state.current.category) || null;
}

function getCurrentSourceEntry() {
  const categoryEntry = getCurrentCategoryEntry();
  return categoryEntry?.sources.find((item) => item.source_stem === state.current.sourceStem) || null;
}

function fillSelect(select, entries, currentValue, valueKey, labelBuilder) {
  select.innerHTML = "";
  entries.forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry[valueKey];
    option.textContent = labelBuilder(entry);
    if (option.value === currentValue) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function pickPreferredUnit(units) {
  for (const preferred of PREFERRED_UNITS) {
    const match = units.find((item) => item.unit === preferred);
    if (match) {
      return match.unit;
    }
  }
  return units[0]?.unit ?? null;
}

function pickPreferredCategory(categories) {
  for (const preferred of PREFERRED_CATEGORIES) {
    const match = categories.find((item) => item.category === preferred);
    if (match) {
      return match.category;
    }
  }
  return categories[0]?.category ?? null;
}

function pickPreferredSource(sources) {
  if (!sources.length) {
    return null;
  }

  const dated = sources
    .filter((item) => /^\d{8}_/.test(item.source_stem))
    .sort((a, b) => a.source_stem.localeCompare(b.source_stem, "ko"));
  if (dated.length) {
    return dated[dated.length - 1].source_stem;
  }
  return sources[0].source_stem;
}

function syncSelectors() {
  if (!state.library || !state.library.units.length) {
    return;
  }

  if (!state.current.unit || !state.library.units.some((item) => item.unit === state.current.unit)) {
    state.current.unit = pickPreferredUnit(state.library.units);
  }
  fillSelect(unitSelect, state.library.units, state.current.unit, "unit", (item) => item.unit);

  const unitEntry = getCurrentUnitEntry();
  if (!state.current.category || !unitEntry.categories.some((item) => item.category === state.current.category)) {
    state.current.category = pickPreferredCategory(unitEntry.categories);
  }
  fillSelect(categorySelect, unitEntry.categories, state.current.category, "category", (item) => item.category);

  const categoryEntry = getCurrentCategoryEntry();
  if (!state.current.sourceStem || !categoryEntry.sources.some((item) => item.source_stem === state.current.sourceStem)) {
    state.current.sourceStem = pickPreferredSource(categoryEntry.sources);
  }
  fillSelect(
    sourceSelect,
    categoryEntry.sources,
    state.current.sourceStem,
    "source_stem",
    (item) => `${item.source_stem} (${item.page_count}p / ${item.question_total} questions)`
  );

  const sourceEntry = getCurrentSourceEntry();
  const sourcePages = sourceEntry.pages.map((item) => item.page_number);
  if (!state.current.page || !sourcePages.includes(state.current.page)) {
    state.current.page = sourcePages[0];
  }
}

function formatAnswerValue(answer) {
  if (!answer) {
    return "-";
  }
  if (Array.isArray(answer.value)) {
    return answer.value.map((item, index) => `${index + 1}. ${item}`).join("\n");
  }
  return String(answer.value);
}

function formatAcceptedAnswers(answer) {
  if (!answer || !Array.isArray(answer.accepted_answers)) {
    return "-";
  }
  if (!answer.accepted_answers.length) {
    return "-";
  }
  if (Array.isArray(answer.accepted_answers[0])) {
    return answer.accepted_answers
      .map((group, index) => `${index + 1}. ${group.join(" / ")}`)
      .join("\n");
  }
  return answer.accepted_answers.join(" / ");
}

function renderAnalysisItems(container, items, formatter = (item) => String(item)) {
  if (!container) {
    return;
  }
  container.innerHTML = "";
  if (!items || !items.length) {
    const empty = document.createElement("div");
    empty.className = "analysis-item empty";
    empty.textContent = "-";
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "analysis-item";
    div.textContent = formatter(item);
    container.appendChild(div);
  });
}

function renderPageList() {
  const sourceEntry = getCurrentSourceEntry();
  pageList.innerHTML = "";

  if (!sourceEntry) {
    pageStats.textContent = "";
    return;
  }

  pageStats.textContent = `${sourceEntry.page_count} pages / ${sourceEntry.question_total} questions`;

  sourceEntry.pages.forEach((page) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = page.page_number === state.current.page ? "active" : "";
    const sourcePageSuffix =
      page.source_page_number ? ` / src p${String(page.source_page_number).padStart(3, "0")}` : "";
    button.innerHTML = `p${String(page.page_number).padStart(3, "0")}${sourcePageSuffix}<small>${page.question_count} questions | ${page.page_read_status}</small>`;
    button.addEventListener("click", () => {
      state.current.page = page.page_number;
      loadCurrentPage();
    });
    pageList.appendChild(button);
  });
}

function renderPagePayload(payload) {
  state.currentPagePayload = payload;
  const sourcePageNumber = payload.page_ref.source_page_number || payload.page_ref.original_page_number;
  const noteSourceStem = payload.page_ref.note_source_stem || payload.page_ref.source_stem || "-";
  const lectureSourceStem = payload.page_ref.original_source_stem || payload.page_ref.source_stem || "-";
  const sourcePageLabel = sourcePageNumber ? `src p${String(sourcePageNumber).padStart(3, "0")}` : "src -";
  sourceSummary.textContent = `${payload.page_ref.unit} | ${payload.page_ref.category} | note p${String(payload.page_ref.page_number).padStart(3, "0")} | ${sourcePageLabel}`;
  openImageLink.title = `lecture ${lectureSourceStem} | note ${noteSourceStem}`;
  document.title = `${payload.page_ref.unit} ${sourcePageLabel} Question Review`;

  reviewImage.alt = `${payload.page_ref.unit} page ${payload.page_ref.page_number}`;
  if (payload.review_image_url) {
    reviewImage.hidden = false;
    reviewImage.src = payload.review_image_url;
    openImageLink.href = payload.review_image_url;
    openImageLink.removeAttribute("aria-disabled");
  } else {
    reviewImage.hidden = true;
    reviewImage.removeAttribute("src");
    openImageLink.removeAttribute("href");
    openImageLink.setAttribute("aria-disabled", "true");
  }

  const analysis = payload.analysis || {};
  if (analysisSummary) {
    const noteText = analysis.note_exhaustive_text || null;
    const lectureText = analysis.lecture_exhaustive_text || null;
    const propositions = analysis.propositions || null;
    const analysisRef = analysis.analysis_ref || null;
    analysisSummary.textContent = analysisRef
      ? `${analysisRef.category} | ${analysisRef.source_stem} | p${String(analysisRef.page_number).padStart(3, "0")}`
      : "No analysis payload";

    if (noteTextStatus) noteTextStatus.textContent = noteText?.extraction_status || "-";
    if (noteCorrectedText) noteCorrectedText.textContent = noteText?.corrected_page_text || "";
    renderAnalysisItems(noteSupplementalText, noteText?.supplemental_ocr_blocks || []);

    if (lectureTextStatus) lectureTextStatus.textContent = lectureText?.extraction_status || "-";
    if (lectureCorrectedText) lectureCorrectedText.textContent = lectureText?.corrected_page_text || "";

    if (propositionStatus) propositionStatus.textContent = propositions?.finalization_status || "-";
    renderAnalysisItems(coursePropositions, propositions?.course_propositions || []);
    renderAnalysisItems(noteInferencePropositions, propositions?.note_concept_inference_propositions || []);
    renderAnalysisItems(canonicalPropositions, propositions?.canonical_propositions || []);
    renderAnalysisItems(supportivePropositions, propositions?.supportive_synthesized_propositions || []);
    renderAnalysisItems(
      unresolvedNotes,
      propositions?.unresolved_notes || [],
      (item) => `block ${item.block_index ?? "-"} | ${item.reason ?? "-"} | ${item.text ?? "-"}`
    );
  }

  questionCount.textContent = `${payload.summary.question_count} questions`;
  questionList.innerHTML = "";

  payload.questions.forEach((question, index) => {
    const fragment = questionCardTemplate.content.cloneNode(true);
    fragment.querySelector(".question-index").textContent = `Question ${index + 1}`;
    fragment.querySelector(".question-badge").textContent = question.question_focus;
    fragment.querySelector(".question-prompt").textContent = question.prompt;
    fragment.querySelector(".answer-value").textContent = formatAnswerValue(question.answer);
    fragment.querySelector(".accepted-answer-value").textContent = formatAcceptedAnswers(question.answer);
    fragment.querySelector(".answer-explanation").textContent = question.explanation?.full || "-";

    const answerPanel = fragment.querySelector(".answer-panel");
    const revealButton = fragment.querySelector(".reveal-answer-button");
    revealButton.addEventListener("click", () => {
      const isHidden = answerPanel.classList.contains("hidden");
      answerPanel.classList.toggle("hidden", !isHidden);
      revealButton.textContent = isHidden ? "\uc815\ub2f5 \uc228\uae30\uae30" : "\uc815\ub2f5 \ubcf4\uae30";
    });

    questionList.appendChild(fragment);
  });

  const previousPage = payload.navigation.previous_page;
  const nextPage = payload.navigation.next_page;
  prevPageButton.disabled = previousPage == null;
  nextPageButtonTop.disabled = nextPage == null;
  nextPageButtonBottom.disabled = nextPage == null;

  prevPageButton.onclick = () => {
    if (previousPage != null) {
      state.current.page = previousPage;
      loadCurrentPage();
    }
  };

  const goNext = () => {
    if (nextPage != null) {
      state.current.page = nextPage;
      loadCurrentPage();
    }
  };
  nextPageButtonTop.onclick = goNext;
  nextPageButtonBottom.onclick = goNext;

  renderPageList();
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
}

async function loadCurrentPage() {
  renderPageList();
  const query = new URLSearchParams({
    unit: state.current.unit,
    category: state.current.category,
    source_stem: state.current.sourceStem,
    page: String(state.current.page),
  });
  const payload = await fetchJson(`/api/page?${query.toString()}`);
  renderPagePayload(payload);
}

async function refreshLibrary() {
  state.library = await fetchJson("/api/library");
  syncSelectors();
  await loadCurrentPage();
}

unitSelect.addEventListener("change", async () => {
  state.current.unit = unitSelect.value;
  state.current.category = null;
  state.current.sourceStem = null;
  state.current.page = null;
  syncSelectors();
  await loadCurrentPage();
});

categorySelect.addEventListener("change", async () => {
  state.current.category = categorySelect.value;
  state.current.sourceStem = null;
  state.current.page = null;
  syncSelectors();
  await loadCurrentPage();
});

sourceSelect.addEventListener("change", async () => {
  state.current.sourceStem = sourceSelect.value;
  state.current.page = null;
  syncSelectors();
  await loadCurrentPage();
});

refreshButton.addEventListener("click", async () => {
  await fetchJson("/api/refresh");
  await refreshLibrary();
});

refreshLibrary().catch((error) => {
  sourceSummary.textContent = `Failed to load question library: ${String(error)}`;
});
