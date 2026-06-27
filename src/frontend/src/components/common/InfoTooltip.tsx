import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface InfoTooltipProps {
	text: string;
	align?: "start" | "end";
}

const TOOLTIP_WIDTH = 260;
const VIEWPORT_MARGIN = 16;
const GAP = 8;

export default function InfoTooltip({ text, align = "start" }: InfoTooltipProps) {
	const buttonRef = useRef<HTMLButtonElement | null>(null);
	const tooltipId = useId();
	const [isOpen, setIsOpen] = useState(false);
	const [position, setPosition] = useState({ left: 0, top: 0, width: TOOLTIP_WIDTH });

	const updatePosition = useCallback(() => {
		const button = buttonRef.current;
		if (!button) return;

		const rect = button.getBoundingClientRect();
		const width = Math.min(TOOLTIP_WIDTH, window.innerWidth - VIEWPORT_MARGIN * 2);
		const preferredLeft = align === "end" ? rect.right - width : rect.left;
		const left = Math.min(
			Math.max(preferredLeft, VIEWPORT_MARGIN),
			window.innerWidth - width - VIEWPORT_MARGIN,
		);
		const top = Math.min(rect.bottom + GAP, window.innerHeight - VIEWPORT_MARGIN);

		setPosition({ left, top, width });
	}, [align]);

	const openTooltip = () => {
		updatePosition();
		setIsOpen(true);
	};

	useEffect(() => {
		if (!isOpen) return;
		updatePosition();
		window.addEventListener("resize", updatePosition);
		window.addEventListener("scroll", updatePosition, true);
		return () => {
			window.removeEventListener("resize", updatePosition);
			window.removeEventListener("scroll", updatePosition, true);
		};
	}, [isOpen, updatePosition]);

	return (
		<span className="inline-flex">
			<button
				ref={buttonRef}
				type="button"
				className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-400/60 text-[10px] font-bold leading-none text-slate-100 transition-colors hover:border-white hover:text-white focus:outline-none focus:ring-2 focus:ring-white/40"
				aria-label={text}
				aria-describedby={isOpen ? tooltipId : undefined}
				onBlur={() => setIsOpen(false)}
				onFocus={openTooltip}
				onMouseEnter={openTooltip}
				onMouseLeave={() => setIsOpen(false)}
			>
				?
			</button>
			{isOpen &&
				createPortal(
					<span
						id={tooltipId}
						role="tooltip"
						className="pointer-events-none fixed z-[9999] rounded-md border border-[var(--color-panel-border)] bg-[var(--color-panel)] p-2.5 text-left text-[11px] font-normal normal-case leading-relaxed text-slate-100 opacity-100 shadow-xl"
						style={{ left: position.left, top: position.top, width: position.width }}
					>
						{text}
					</span>,
					document.body,
				)}
		</span>
	);
}
