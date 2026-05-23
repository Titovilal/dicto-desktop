interface WaveformProps {
  level: number
  bars?: number
  color?: string
}

export default function Waveform({ level, bars = 12, color = 'currentColor' }: WaveformProps) {
  // Each bar gets a height multiplier based on distance from center.
  // Center bars are tallest. Animate height based on level.
  const getBarHeight = (index: number): number => {
    const center = (bars - 1) / 2
    const distFromCenter = Math.abs(index - center) / center // 0 at center, 1 at edges
    const baseMultiplier = 1 - distFromCenter * 0.6 // center=1.0, edges=0.4
    const minHeight = 4
    const maxHeight = 40
    const height = minHeight + (maxHeight - minHeight) * baseMultiplier * level
    return Math.max(minHeight, height)
  }

  return (
    <div
      className="flex items-center justify-center gap-0.5"
      style={{ color }}
      aria-label={`Audio level: ${Math.round(level * 100)}%`}
    >
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          style={{
            width: 3,
            height: getBarHeight(i),
            backgroundColor: 'currentColor',
            borderRadius: 2,
            transition: 'height 50ms ease-out',
          }}
        />
      ))}
    </div>
  )
}
