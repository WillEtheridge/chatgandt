"use client";

import { useEffect, useState } from "react";

const VOCABULARY = "MIX.STIR.POUR.TASTE.REVISE.REPEAT.";
const LARGE_HEIGHT = 40;

function createMartini(width: number, height: number) {
  const center = Math.floor(width / 2);
  const bowlTop = 4;
  const bowlBottom = Math.floor(height * 0.44);
  const bowlWidth = Math.floor(width * 0.24);
  const stemBottom = height - 3;
  const baseWidth = Math.floor(width * 0.11);

  return Array.from({ length: height }, (_, y) => {
    if (y === 0) return `MIXING${" ".repeat(width - 6)}`;

    return Array.from({ length: width }, (_, x) => {
      if (y >= bowlTop && y <= bowlBottom) {
        const progress = (y - bowlTop) / (bowlBottom - bowlTop);
        const halfWidth = Math.max(1, Math.round(bowlWidth * (1 - progress)));
        if (Math.abs(x - center) <= halfWidth) return " ";
      }

      if (y > bowlBottom && y <= stemBottom && x === center) return " ";
      if (y === stemBottom + 1 && Math.abs(x - center) <= baseWidth) return " ";

      return VOCABULARY[(x + y * (width + 7)) % VOCABULARY.length];
    }).join("");
  });
}

const LARGE_MARTINI = createMartini(103, LARGE_HEIGHT);
const SMALL_MARTINI = createMartini(43, 28);

function MartiniRows({ rows, visibleLineCount }: Readonly<{ rows: string[]; visibleLineCount: number }>) {
  const visibleRows = Math.ceil((visibleLineCount / LARGE_HEIGHT) * rows.length);
  const firstVisibleRow = rows.length - visibleRows;

  return (
    <pre aria-hidden="true" className="text-xs leading-none text-signal">
      {rows.map((row, index) => (
        <span className={`block ${index < firstVisibleRow ? "invisible" : ""}`} key={`${index}-${row}`}>
          {row}
        </span>
      ))}
    </pre>
  );
}

export function MartiniLoader() {
  const [visibleLineCount, setVisibleLineCount] = useState(0);

  useEffect(() => {
    let direction = 1;
    const revealLine = window.setInterval(() => {
      setVisibleLineCount((currentCount) => {
        if (currentCount >= LARGE_HEIGHT) {
          direction = -1;
        } else if (currentCount <= 0) {
          direction = 1;
        }

        return currentCount + direction;
      });
    }, 40);

    return () => window.clearInterval(revealLine);
  }, []);

  return (
    <div aria-label="Mixing a cocktail recipe" className="overflow-hidden" role="img">
      <div className="lg:hidden">
        <MartiniRows rows={SMALL_MARTINI} visibleLineCount={visibleLineCount} />
      </div>
      <div className="hidden lg:block">
        <MartiniRows rows={LARGE_MARTINI} visibleLineCount={visibleLineCount} />
      </div>
    </div>
  );
}
