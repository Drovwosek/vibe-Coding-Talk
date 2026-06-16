# Browser Module

Pattern: shared browser code uses one global namespace, small functions, and explicit exports at the bottom of each module.

~~~javascript
(function (app) {
  const STORAGE = {
    venues: "postovaya.venues",
    audiences: "postovaya.audiences",
    drafts: "postovaya.drafts",
    sidebarCollapsed: "postovaya.sidebarCollapsed",
  };

  function load(key, fallback) {
    try {
      return JSON.parse(localStorage.getItem(key)) || fallback;
    } catch {
      return fallback;
    }
  }

  function save(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function audiencesForVenue(venueId) {
    return state.audiences.filter(item => item.venueId === venueId);
  }

  app.store = { STORAGE, state, save, audiencesForVenue };
})(window.Postovaya = window.Postovaya || {});
~~~

For new frontend modules, prefer this IIFE namespace style over ES modules or extra build tooling.
