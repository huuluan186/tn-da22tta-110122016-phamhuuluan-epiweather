export default function PulseDot() {
  return (
    <span className="relative inline-block w-2 h-2 rounded-full bg-[var(--color-risk-low)]">
      <span className="absolute inset-0 rounded-full bg-[var(--color-risk-low)] animate-[pulse-ring_2s_ease-out_infinite]" />
    </span>
  );
}
