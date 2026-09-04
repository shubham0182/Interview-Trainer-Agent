---
role: frontend_developer
type: technical
difficulty: medium
---

# Frontend Developer — Technical Interview Questions

## JavaScript / TypeScript

- Explain the event loop in JavaScript. What is the call stack vs the task queue?
- What is a closure? Give a practical example of when closures are useful.
- Explain the difference between `==` and `===` in JavaScript.
- What are Promises? How do `async/await` relate to Promises?
- What is TypeScript? What advantages does it provide over plain JavaScript?

## React

- Explain the virtual DOM. How does React's reconciliation algorithm work?
- What is the difference between `useState` and `useReducer`? When do you use each?
- Explain `useEffect`. What are its common pitfalls?
- What is prop drilling? How can you solve it without an external state library?
- What is memoization in React? When should you use `useMemo` and `useCallback`?

## CSS and Layout

- Explain the CSS box model.
- What is the difference between Flexbox and CSS Grid? When would you choose each?
- What is responsive design? Describe a mobile-first approach.
- Explain CSS specificity and how it determines which styles are applied.

## Performance

- What is code splitting? How does Next.js support it?
- Explain lazy loading for images and components. Why does it improve performance?
- What is the difference between Server-Side Rendering (SSR) and Client-Side Rendering (CSR)?
- What is the purpose of a CDN in serving frontend assets?

## Accessibility

- What is WCAG? Name 3 accessibility best practices for web development.
- Explain semantic HTML. Why does it matter?

## Model Answers

**Q: Explain the virtual DOM.**

The virtual DOM is a lightweight in-memory representation of the real DOM. When state changes, React re-renders the component tree to a new virtual DOM, then diffs it against the previous virtual DOM (reconciliation). Only the actual changes are applied to the real DOM in a batch, minimizing expensive DOM operations. This makes UI updates efficient without developers manually managing DOM mutations.

**Q: What is the difference between SSR and CSR?**

CSR (Client-Side Rendering): The server sends a bare HTML shell + JavaScript bundle; the browser runs the JS to fetch data and build the UI. First paint is fast but content takes time to appear. SSR (Server-Side Rendering): The server renders the full HTML for each request before sending it. The browser displays content immediately, improving First Contentful Paint and SEO. Next.js supports both: SSR via server components or `getServerSideProps`, CSR via `"use client"` components.
