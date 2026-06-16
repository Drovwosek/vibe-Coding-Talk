(function (app) {
  async function requestJson(path, options = {}) {
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Ошибка запроса.");
    return data;
  }

  function postJson(path, payload) {
    return requestJson(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  app.api = {
    health: () => requestJson("/api/health"),
    generatePost: payload => postJson("/api/generate", payload),
    promptTemplates: () => requestJson("/api/prompts"),
    updatePromptTemplate: payload => postJson("/api/prompts", payload),
    researchVenue: payload => postJson("/api/research-venue", payload),
  };
})(window.Postovaya = window.Postovaya || {});
