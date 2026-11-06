import { useId } from "react";

/** A growth illustration, separate from purchased/placed inventory objects. */
export function PersonalPlant({ level }: { level: number }) {
  const id = useId().replaceAll(":", "");
  const leaves = Math.min(8, Math.max(2, Math.floor(level) + 1));
  const stemTop = 345 - (leaves - 2) * 25;
  return (
    <svg viewBox={`70 ${stemTop - 55} 360 ${620 - stemTop}`} role="img" aria-label={`Your growing plant, garden level ${level}`}>
      <defs>
        <radialGradient id={`${id}-light`}>
          <stop stopColor="#f2e7b8" stopOpacity=".8" />
          <stop offset="1" stopColor="#e7ebd4" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}-pot`} x2="1" y2="1">
          <stop stopColor="#c59876" /><stop offset="1" stopColor="#a67759" />
        </linearGradient>
      </defs>
      <circle cx="250" cy="255" r="215" fill={`url(#${id}-light)`} />
      <ellipse cx="250" cy="548" rx="120" ry="16" fill="#526b3c" opacity=".12" />
      <path d={`M250 447 Q240 395 250 ${stemTop}`} fill="none" stroke="#557643" strokeWidth="9" strokeLinecap="round" />
      {Array.from({ length: leaves }, (_, index) => {
        const right = index % 2 === 1;
        const y = 375 - Math.floor(index / 2) * 53;
        return (
          <g key={index} transform={`translate(250 ${y}) scale(${right ? 1 : -1} 1)`}>
            <path d="M0 5C4-42 51-73 91-67C95-23 52 15 0 5Z" fill={index % 3 ? "#65884e" : "#8ba76d"} />
            <path d="M1 4Q36-27 76-54" fill="none" stroke="#c0cf9f" strokeWidth="2" opacity=".6" />
          </g>
        );
      })}
      <path d={`M250 ${stemTop + 18}Q220 ${stemTop - 19}250 ${stemTop - 42}Q282 ${stemTop - 13}250 ${stemTop + 18}`} fill="#91ac70" />
      <path d="M166 440H334L314 529Q310 546 292 546H208Q190 546 186 529Z" fill={`url(#${id}-pot)`} />
      <rect x="157" y="425" width="186" height="29" rx="10" fill="#cba385" />
      <ellipse cx="250" cy="428" rx="79" ry="10" fill="#765941" />
      <path d="M207 467L214 523" stroke="#e4bea1" strokeWidth="5" strokeLinecap="round" opacity=".5" />
    </svg>
  );
}
