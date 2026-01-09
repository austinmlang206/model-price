import type { Filters, ProviderInfo, ModelFamily } from '../types/pricing';
import { FILTER_CAPABILITIES } from '../config';

interface FilterBarProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  providers: ProviderInfo[];
  families: ModelFamily[];
}

export function FilterBar({ filters, onFiltersChange, providers, families }: FilterBarProps) {
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
        <label className="filter-label">模型家族</label>
        <select
          className="filter-select"
          value={filters.family || ''}
          onChange={(e) =>
            onFiltersChange({ ...filters, family: e.target.value || null })
          }
        >
          <option value="">全部</option>
          {families.map((f) => (
            <option key={f.name} value={f.name}>
              {f.name} ({f.count})
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
          {FILTER_CAPABILITIES.map((c) => (
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
