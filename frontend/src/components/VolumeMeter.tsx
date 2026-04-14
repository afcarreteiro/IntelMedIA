interface VolumeMeterProps {
  level: number;
  active: boolean;
}

export function VolumeMeter({ level, active }: VolumeMeterProps) {
  const bars = Array.from({ length: 18 }, (_, index) => {
    const threshold = (index + 1) / 18;
    const raised = active && level >= threshold - 0.08;
    return (
      <span
        key={threshold}
        className={`meter-bar ${raised ? 'meter-bar--active' : ''}`}
        style={{ height: `${14 + index * 2}px` }}
      />
    );
  });

  return (
    <div className="meter">
      <div className="meter-labels">
        <span>Mic activity</span>
        <span>{active ? 'listening' : 'idle'}</span>
      </div>
      <div className="meter-bars">{bars}</div>
    </div>
  );
}
