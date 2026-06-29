import type { ECharts } from "echarts";

/**
 * Gắn auto-resize cho một instance ECharts.
 *
 * Ngoài việc nghe sự kiện window resize, hàm còn quan sát thay đổi kích thước
 * của chính container qua ResizeObserver: toggle sidebar, reflow grid responsive,
 * hoặc trường hợp chart được init khi panel còn ẩn (width 0). Nếu không xử lý
 * container resize, canvas giữ kích thước cũ và bị tràn khỏi khung trên các màn
 * hình độ phân giải thấp như TV hoặc máy chiếu.
 *
 * Trả về hàm cleanup (đã bao gồm dispose chart) để dùng trực tiếp trong useEffect.
 */
export function attachChartResize(el: HTMLElement, chart: ECharts): () => void {
  const onResize = () => chart.resize();
  window.addEventListener("resize", onResize);
  const ro = new ResizeObserver(onResize);
  ro.observe(el);
  return () => {
    window.removeEventListener("resize", onResize);
    ro.disconnect();
    chart.dispose();
  };
}
