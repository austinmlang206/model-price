import type { Filters, ProviderInfo } from '../types/pricing';

interface FilterBarProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  providers: ProviderInfo[];
}

const CAPABILITIES = [
  { value: 'text', label: '文本' },
  { value: 'vision', label: '视觉' },
  { value: 'audio', label: '音频' },
  { value: 'embedding', label: '嵌入' },
];

export function FilterBar({ filters, onFiltersChange, providers }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label className="filter-label">提供商</label>
        <select
          className="filter-select"
          value={filters.provider || ''}
          onChange={(e) =>
            onFiltersChange({ ...filters, provider: e.target.value || null })
          }
        >
          <option value="">全部</option>
          {providers.map((p) => (
            <option key={p.name} value={p.name}>
              {p.display_name} ({p.model_count})
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label className="filter-label">能力</label>
        <select
          className="filter-select"
          value={filters.capability || ''}
          onChange={(e) =>
            onFiltersChange({ ...filters, capability: e.target.value || null })
          }
        >
          <option value="">全部</option>
          {CAPABILITIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group search-group">
        <label className="filter-label">搜索</label>
        <input
          type="text"
          className="filter-input"
          placeholder="模型名称..."
          value={filters.search}
          onChange={(e) =>
            onFiltersChange({ ...filters, search: e.target.value })
          }
        />
      </div>
    </div>
  );
}
