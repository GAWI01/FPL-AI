type RankPoint = {
  event: number;
  overall_rank?: number | null;
};

export function RankTrend({ history, currentRank }: { history: RankPoint[]; currentRank?: number | null }) {
  const points = history.filter((item) => Number.isFinite(item.overall_rank));
  if (!points.length && !currentRank) {
    return (
      <div className="rank-trend-empty">
        <span>Rank trend</span>
        <b>Waiting for FPL history</b>
      </div>
    );
  }

  const values = points.map((p) => Number(p.overall_rank)).filter((n) => n > 0);
  if (currentRank && currentRank > 0 && (values.length === 0 || values[values.length - 1] !== currentRank)) {
    values.push(currentRank);
  }
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(1, max - min);
  const width = 720;
  const height = 150;
  const pad = 12;
  const coords = values.map((value, index) => {
    const x = pad + (index / Math.max(1, values.length - 1)) * (width - pad * 2);
    const y = pad + ((value - min) / range) * (height - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const improved = values.length > 1 ? values[values.length - 1] < values[0] : null;

  return (
    <div className="rank-trend">
      <div className="rank-trend-head">
        <div>
          <span>OVERALL RANK TREND</span>
          <b>{currentRank ? currentRank.toLocaleString("en-US") : "—"}</b>
        </div>
        {improved !== null && (
          <em className={improved ? "positive" : "negative"}>
            {improved ? "Improving" : "Needs attention"}
          </em>
        )}
      </div>
      <svg className="rank-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Overall rank trend">
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} />
        <polyline points={coords.join(" ")} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        {coords.map((point, index) => {
          const [cx, cy] = point.split(",");
          return <circle key={index} cx={cx} cy={cy} r="3.5" fill="currentColor" />;
        })}
      </svg>
      <div className="rank-trend-foot">
        <span>GW{points[0]?.event ?? "—"}</span>
        <span>Lower rank number = better</span>
        <span>GW{points[points.length - 1]?.event ?? "—"}</span>
      </div>
    </div>
  );
}
