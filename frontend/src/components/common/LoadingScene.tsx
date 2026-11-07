type LoadingSceneProps = {
  title?: string;
  description?: string;
  section?: string;
  variant?: "page" | "welcome" | "inline";
};

export function LoadingScene({
  title = "Your space is taking root.", description = "Preparing your little space…",
  section = "JOMO", variant = "page",
}: LoadingSceneProps) {
  return (
    <div className={`j-loading-placeholder j-loading-scene j-loading-scene--${variant}`}>
      <div className="j-loading-composition" role="status" aria-live="polite" aria-atomic="true">
        <div className="j-loading-wordmark" aria-hidden="true">
          <svg viewBox="0 0 40 28" fill="none"><path d="M6 24C18 22 27 13 33 3M15 20C5 20 7 10 7 10C17 10 17 17 15 20ZM24 13C16 12 19 3 19 3C27 5 27 10 24 13ZM27 9C27 1 37 1 37 1C36 9 32 11 27 9Z" fill="currentColor" /></svg>
          <span>JOMO</span>
        </div>
        <svg className="j-loading-art" viewBox="0 0 280 230" fill="none" aria-hidden="true">
          <circle cx="140" cy="105" r="88" fill="#e9edd9" /><circle cx="140" cy="105" r="72" fill="#f0f2e3" />
          <circle className="j-loading-sun" cx="202" cy="56" r="14" fill="#efcf83" />
          <ellipse cx="140" cy="205" rx="81" ry="9" fill="#d8dbc3" opacity=".45" />
          <path d="M64 204C89 200 99 187 124 189C139 181 159 185 171 192C190 191 204 202 218 204H64Z" fill="#c9b292" />
          <path d="M95 203C112 195 125 196 136 190C147 186 164 194 176 197" stroke="#b49b7b" strokeWidth="3" strokeLinecap="round" />
          <g className="j-loading-sprout">
            <path d="M140 193C137 165 147 147 143 125" stroke="#6f8652" strokeWidth="6" strokeLinecap="round" />
            <path d="M142 143C113 148 89 124 79 99C114 94 142 105 142 143Z" fill="#9eaf77" />
            <path d="M143 135C146 99 175 83 207 88C202 117 180 143 143 135Z" fill="#7d995c" />
            <path d="M141 142C123 122 104 109 89 104M145 134C159 115 179 101 196 94" stroke="#cbd8aa" strokeWidth="2" strokeLinecap="round" />
          </g>
          <path d="M83 203L77 186L91 202M192 202L200 181L198 203" stroke="#a1b17d" strokeWidth="3" strokeLinecap="round" />
          <g className="j-loading-float"><path d="M47 87C60 80 69 87 76 94C61 96 52 94 47 87Z" fill="#b5c297" /><path d="M218 159C225 145 237 144 245 144C239 155 231 161 218 159Z" fill="#9faf7d" /></g>
          <circle cx="55" cy="150" r="3" fill="#d6bd7f" /><circle cx="223" cy="109" r="2.5" fill="#a6b583" />
        </svg>
        <p className="j-loading-section">{section}</p>
        <h2 className="j-loading-title">{title}</h2>
        <p className="j-loading-description">{description}</p>
        <div className="j-loading-dots" aria-hidden="true"><span /><span /><span /></div>
      </div>
      <p className="j-loading-patience">This is taking a little longer. Your space will appear when it’s ready.</p>
      {variant === "welcome" && <p className="j-loading-tagline">Less scrolling. More living.</p>}
    </div>
  );
}
