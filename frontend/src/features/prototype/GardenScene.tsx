import { useId } from "react";

export type SceneItem = {
  id: string;
  asset: string;
  name: string;
  x: number;
  y: number;
};

/** Decorative landscape stays separate from actual, server-owned garden items. */
export function GardenScene({
  items = [],
  label = "An illustrated garden landscape",
}: {
  items?: SceneItem[];
  label?: string;
}) {
  const key = useId().replaceAll(":", "");
  return (
    <div className="j-landscape">
      <svg
        viewBox="0 0 900 460"
        preserveAspectRatio="xMidYMid slice"
        role="img"
        aria-label={label}
      >
        <defs>
          <linearGradient id={`${key}-sky`} x2="0" y2="1">
            <stop stopColor="#f4f0dc" />
            <stop offset="1" stopColor="#e4ebcf" />
          </linearGradient>
          <linearGradient id={`${key}-hill`} x2="0" y2="1">
            <stop stopColor="#93aa7c" />
            <stop offset="1" stopColor="#6c895b" />
          </linearGradient>
          <radialGradient id={`${key}-glow`}>
            <stop stopColor="#f5e6aa" stopOpacity=".7" />
            <stop offset="1" stopColor="#f5e6aa" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="900" height="460" fill={`url(#${key}-sky)`} />
        <circle cx="720" cy="104" r="100" fill={`url(#${key}-glow)`} />
        <circle cx="720" cy="104" r="35" fill="#f2e4b1" opacity=".8" />
        <path
          d="M0 285C155 223 235 263 375 251S610 280 900 232V460H0Z"
          fill="#b4c59e"
        />
        <path
          d="M0 342C180 296 271 342 440 321S670 339 900 310V460H0Z"
          fill={`url(#${key}-hill)`}
        />
        {[115, 245, 382, 514, 630].map((x, index) => (
          <g
            key={x}
            transform={`translate(${x} ${385 + (index % 2) * 13})`}
            opacity=".23"
            fill="#466a3b"
          >
            <path
              d="M0 14V-15"
              stroke="#466a3b"
              strokeWidth="4"
              strokeLinecap="round"
            />
            <path d="M0-9Q-21-10-18-29Q2-24 0-9M0-14Q-3-36 18-36Q21-17 0-14" />
          </g>
        ))}
        {items.map((item) => (
          <g
            key={item.id}
            transform={`translate(${item.x * 9} ${item.y * 4.6})`}
          >
            <title>{item.name}</title>
            {item.asset.includes("bonsai") ? (
              <>
                <path
                  d="M0 20V-80M0-26L-25-49M0-41L28-64"
                  stroke="#786747"
                  strokeWidth="10"
                  strokeLinecap="round"
                />
                <circle cx="0" cy="-103" r="42" fill="#5f7c4d" />
                <circle cx="-39" cy="-70" r="37" fill="#73905b" />
                <circle cx="38" cy="-72" r="40" fill="#64844f" />
                <circle cx="-14" cy="-121" r="34" fill="#89a16b" />
              </>
            ) : item.asset.includes("sunflower") ? (
              <>
                <path d="M0 14V-51" stroke="#557a42" strokeWidth="5" />
                <ellipse
                  cx="-12"
                  cy="-8"
                  rx="16"
                  ry="7"
                  fill="#6e914f"
                  transform="rotate(25)"
                />
                {[0, 60, 120].map((angle) => (
                  <ellipse
                    key={angle}
                    cx="0"
                    cy="-57"
                    rx="11"
                    ry="27"
                    fill="#e7bd57"
                    transform={`rotate(${angle} 0 -57)`}
                  />
                ))}
                <circle cy="-57" r="11" fill="#7b633f" />
              </>
            ) : item.asset.includes("bench") ? (
              <>
                <path
                  d="M-32 0H32M-30-15H30M-25 0V20M25 0V20"
                  stroke="#82795c"
                  strokeWidth="9"
                  strokeLinecap="round"
                />
              </>
            ) : item.asset.includes("cat") ? (
              <>
                <ellipse cy="5" rx="27" ry="16" fill="#b78960" />
                <circle cx="21" cy="-7" r="14" fill="#d7b18c" />
                <path d="M11-15L12-28L23-17M23-18L34-27L34-10" fill="#b78960" />
              </>
            ) : item.asset.includes("fountain") ? (
              <>
                <path d="M-35-12Q0 17 35-12Z" fill="#8c9a83" />
                <path d="M0 1V25M-18 28H18" stroke="#8c9a83" strokeWidth="10" />
                <ellipse cy="-12" rx="35" ry="8" fill="#bdcfbf" />
              </>
            ) : (
              <>
                <path d="M0 16V-18" stroke="#466b3e" strokeWidth="4" />
                <path
                  d="M0-10Q-23-16-20-36Q3-30 0-10M0-16Q0-40 23-39Q24-18 0-16"
                  fill="#62884f"
                />
              </>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
