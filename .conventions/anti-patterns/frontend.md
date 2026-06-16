# Frontend Anti-Patterns

## Bypassing the Postovaya namespace

BAD: create new globals like window.api, window.state, or standalone helper scripts with implicit globals.

GOOD: attach shared modules to window.Postovaya and destructure them in web/app.js.

## Rendering user content without escaping

BAD:

~~~javascript
els.context.innerHTML = "<span>" + venue.description + "</span>";
~~~

GOOD:

~~~javascript
els.context.innerHTML = "<span>" + escapeHtml(venue.description) + "</span>";
~~~

## Persisting inconsistent localStorage data

BAD: update state.venues or state.audiences without saving the matching STORAGE key.

GOOD: mutate state, call save(STORAGE.<key>, state.<key>), then re-render dependent views.

## Adding build tooling for small browser changes

BAD: introduce bundlers, JSX, TypeScript, or package dependencies for a local-first static UI tweak.

GOOD: keep plain browser JavaScript unless the product requirement clearly exceeds the current static setup.
