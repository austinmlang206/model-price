import type { ModelPricing, SortConfig } from '../types/pricing';

interface ModelTableProps {
  models: ModelPricing[];
  sortConfig: SortConfig;
  onSort: (field: SortConfig['field']) => void;
}

const providerDisplayNames: Record<string, string> = {
  aws_bedrock: 'AWS Bedrock',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  azure: 'Azure',
  openrouter: 'OpenRouter',
};

const capabilityIcons: Record<string, string> = {
  text: '📝',
  vision: '🖼️',
  audio: '🎧',
  embedding: '📊',
};

function formatPrice(price: number | null): string {
  if (price === null) return '-';
  if (price === 0) return 'Free';
  return '$' + price.toFixed(2);
}

function formatNumber(num: number | null): string {
  if (num === null) return '-';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
  return num.toString();
}

export function ModelTable({ models, sortConfig, onSort }: ModelTableProps) {
  const renderSortIndicator = (field: SortConfig['field']) => {
    if (sortConfig.field !== field) return null;
    return <span className="sort-indicator">{sortConfig.order === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="table-container">
      <table className="model-table">
        <thead>
          <tr>
            <th>提供商</th>
            <th
              className="sortable"
              onClick={() => onSort('model_name')}
            >
              模型 {renderSortIndicator('model_name')}
            </th>
            <th
              className="sortable numeric"
              onClick={() => onSort('input')}
            >
              输入 {renderSortIndicator('input')}
            </th>
            <th
              className="sortable numeric"
              onClick={() => onSort('output')}
            >
              输出 {renderSortIndicator('output')}
            </th>
            <th className="numeric">缓存</th>
            <th
              className="sortable numeric"
              onClick={() => onSort('context_length')}
            >
              上下文 {renderSortIndicator('context_length')}
            </th>
            <th>能力</th>
          </tr>
        </thead>
        <tbody>
          {models.map((model) => (
            <tr key={model.id}>
              <td className="provider-cell">
                {providerDisplayNames[model.provider] || model.provider}
              </td>
              <td className="model-name-cell">{model.model_name}</td>
              <td className="mono numeric">{formatPrice(model.pricing.input)}</td>
              <td className="mono numeric">{formatPrice(model.pricing.output)}</td>
              <td className="mono numeric secondary">
                {formatPrice(model.pricing.cached_input)}
              </td>
              <td className="mono numeric">{formatNumber(model.context_length)}</td>
              <td className="capabilities-cell">
                {model.capabilities.map((cap) => (
                  <span key={cap} title={cap}>
                    {capabilityIcons[cap] || ''}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
