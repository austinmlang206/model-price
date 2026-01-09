/**
 * Visualization constants for price bars and charts.
 */

/**
 * Maximum price values used for scaling price bars.
 * Input prices are typically lower than output prices.
 */
export const PRICE_BAR_SCALE = {
  /** Max input price for 100% bar width ($/M tokens) */
  inputMax: 20,
  /** Max output price for 100% bar width ($/M tokens) */
  outputMax: 80,
};

/**
 * Calculate price bar width percentage.
 */
export function calculatePriceBarWidth(
  price: number | null,
  type: 'input' | 'output'
): number {
  if (price === null || price <= 0) return 0;
  const max = type === 'input' ? PRICE_BAR_SCALE.inputMax : PRICE_BAR_SCALE.outputMax;
  return Math.min((price / max) * 100, 100);
}
