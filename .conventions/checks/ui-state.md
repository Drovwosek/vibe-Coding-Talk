# UI State Checks

- Any change to state.venues, state.audiences, or state.drafts must be followed by save(...) and the affected render functions.
- Keep destructive actions behind window.confirm(...).
- Use showToast(...) for completed background actions that do not otherwise change the active panel.
- Use classList.toggle("hidden", condition) for view visibility instead of inline style changes.
- Escape user-controlled values before inserting HTML with innerHTML.
- Keep venue/audience relationships synchronized in all views: editor selects, profiles list, venue detail, and drafts.
