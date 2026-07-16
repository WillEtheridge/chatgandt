export type ChatGntRecipe = {
  title: string;
  ingredients: Array<{
    amount: number;
    unit: string;
    name: string;
  }>;
  method: string[];
  garnish: string;
};

export function Recipe({ recipe }: Readonly<{ recipe: ChatGntRecipe }>) {
  return (
    <article aria-labelledby="recipe-title" className="border border-outline">
      <header className="border-b border-outline p-4 sm:p-6">
        <h2 className="max-w-4xl text-3xl leading-none tracking-tighter sm:text-4xl" id="recipe-title">
          {recipe.title}
        </h2>
      </header>

      <div className="grid lg:grid-cols-3">
        <section className="border-b border-outline p-4 sm:p-6 lg:border-b-0 lg:border-r">
          <h3 className="text-xs uppercase">Ingredients / {String(recipe.ingredients.length).padStart(2, "0")}</h3>
          <table className="mt-6 w-full border-collapse text-left text-sm leading-relaxed">
            <caption className="sr-only">Recipe ingredients</caption>
            <tbody className="divide-y divide-outline">
              {recipe.ingredients.map((ingredient) => (
                <tr key={`${ingredient.amount}-${ingredient.unit}-${ingredient.name}`}>
                  <td className="w-24 py-3 pr-4 align-top tabular-nums">
                    {ingredient.amount} {ingredient.unit}
                  </td>
                  <td className="py-3 align-top">{ingredient.name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="p-4 sm:p-6 lg:col-span-2">
          <h3 className="text-xs uppercase">Method / {String(recipe.method.length).padStart(2, "0")}</h3>
          <ol className="mt-6 divide-y divide-outline">
            {recipe.method.map((step, index) => (
              <li className="flex gap-6 py-4 first:pt-0" key={step}>
                <span className="w-8 shrink-0 text-xs tabular-nums">{String(index + 1).padStart(2, "0")}</span>
                <p className="max-w-3xl text-sm leading-relaxed">{step}</p>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section className="bg-signal p-4 text-concrete sm:p-6">
        <h3 className="text-xs uppercase">Garnish</h3>
        <p className="mt-4 max-w-4xl text-sm leading-relaxed">{recipe.garnish}</p>
      </section>
    </article>
  );
}
