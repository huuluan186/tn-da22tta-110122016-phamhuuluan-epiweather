import type { FeatureMetadata } from "../../hooks/useAnalytics";

interface Props {
	metadata: FeatureMetadata;
	className?: string;
}

export default function FeatureTooltip({ metadata, className = "" }: Props) {
	const label = metadata.display_name_vi || metadata.feature;
	const description = metadata.description_vi || "Chưa có mô tả ý nghĩa cho biến này.";

	return (
		<span className={`group relative inline-flex min-w-0 ${className}`}>
			<button
				type="button"
				className="min-w-0 cursor-help border-b border-dotted border-[var(--color-text-3)] text-left text-[var(--color-text-1)]"
				aria-label={`${label}. Tên kỹ thuật: ${metadata.feature}. ${description}`}
			>
				{label}
			</button>
			<span className="pointer-events-none invisible absolute bottom-full left-0 z-40 mb-2 w-[300px] max-w-[80vw] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left opacity-0 shadow-xl transition-opacity group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100">
				<span className="block text-xs font-semibold text-[var(--color-text-1)]">{label}</span>
				<span className="mt-1 block text-[11px] leading-relaxed text-[var(--color-text-2)]">
					{description}
				</span>
				<span className="mt-2 block border-t border-[var(--color-border-soft)] pt-2 text-[10px] text-[var(--color-text-3)]">
					Tên kỹ thuật: <code className="text-[var(--color-text-2)]">{metadata.feature}</code>
				</span>
			</span>
		</span>
	);
}
