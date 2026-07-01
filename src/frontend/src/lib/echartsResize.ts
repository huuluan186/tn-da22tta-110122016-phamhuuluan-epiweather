import type { ECharts } from "echarts";

/**
 * Gắn auto-resize cho một instance ECharts.
 *
 * Dùng ResizeObserver trên container thay vì window resize: bắt được cả
 * toggle sidebar, reflow grid responsive, và chart được init khi panel còn ẩn
 * (width 0) — những trường hợp window resize không phát hiện được.
 * ResizeObserver cũng fire khi window resize (container thay đổi theo),
 * nên không cần window listener riêng — giữ cả hai sẽ gọi chart.resize() 2 lần/event.
 *
 * Trả về hàm cleanup (đã bao gồm dispose chart) để dùng trực tiếp trong useEffect.
 */
export function attachChartResize(el: HTMLElement, chart: ECharts): () => void {
  // Guard chống callback ResizeObserver đã được queue trước khi disconnect() chạy
  // vẫn fire sau chart.dispose() — ECharts throw "Instance not created" trong trường hợp đó.
  const onResize = () => { if (!chart.isDisposed()) chart.resize(); };
  const ro = new ResizeObserver(onResize);
  ro.observe(el);
  return () => {
    ro.disconnect();
    chart.dispose();
  };
}
