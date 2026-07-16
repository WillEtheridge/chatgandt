# Frontend implementation rules

These rules apply to all work inside `frontend/`.

## Typography

- Use the licensed Neue Montreal Mono Book face everywhere.
- Do not add other font weights or weight utility classes.
- Establish hierarchy with Tailwind's built-in font-size utilities and responsive prefixes.
- Use only named Tailwind sizes such as `text-xs`, `text-base`, `text-4xl`, and `lg:text-8xl`.
- Do not use arbitrary typography utilities such as `text-[...]`, `leading-[...]`, or `tracking-[...]`.

## Colour

- Define project colours as named semantic tokens in Tailwind's `@theme` block.
- Use the `concrete`, `steel`, and `signal` utilities rather than hexadecimal values in components.
- Do not use arbitrary colour utilities such as `text-[#...]`, `bg-[#...]`, or `border-[#...]`.

## Tailwind usage

- Prefer Tailwind's built-in sizing, spacing, leading, tracking, width, and height scales.
- Do not use arbitrary-value utilities unless the project author explicitly approves the individual exception.
- If the built-in scale is insufficient, discuss the need before adding a named theme token.
- Keep `globals.css` limited to the Tailwind import and approved global theme tokens. Do not add component styling there.
- Do not introduce a component library, CSS module, CSS-in-JS layer, or external design system without explicit approval.
