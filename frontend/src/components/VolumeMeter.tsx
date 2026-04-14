interface VolumeMeterProps {
  level: number;
  active: boolean;
}

export function VolumeMeter({ level, active }: VolumeMeterProps) {
  const bars = Array.from({ length: 12 }, (_, index) => {
    const threshold = (index + 1) / 12;
    const raised = active && level >= threshold - 0.08;
    return (
      <span
        key={threshold}
        className={`meter-bar ${raised ? 'meter-bar--active' : ''}`}
        style={{ height: `${8 + index * 1.8}px` }}
      />
    );
  });

  return (
    <div className="meter meter--compact">
      <div className="meter-labels">
        <span>Microfone</span>
        <span>{active ? 'A ouvir' : 'Pronto'}</span>
      </div>
      <div className="meter-bars">{bars}</div>
    </div>
  );
}
