import { useState } from 'react';
import type { ModelPricing, ModelUpdate, SortConfig } from '../types/pricing';
import { CapabilityList, EditableCapabilityList } from './CapabilityBadge';
import { ModalityList } from './ModalityIcons';
import { getProviderDisplayName } from '../config';

interface ModelTableProps {
  models: ModelPricing[];
  sortConfig: SortConfig;
  onSort: (field: SortConfig['field']) => void;
  onUpdateModel?: (modelId: string, updates: ModelUpdate) => Promise<boolean>;
  updating?: string | null;
}

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

type EditableField = 'context_length' | 'max_output_tokens' | 'is_open_source' | 'pricing_input' | 'pricing_output' | 'pricing_cached_input';

interface EditingState {
  modelId: string;
  field: EditableField;
  value: string;
}

export function ModelTable({ models, sortConfig, onSort, onUpdateModel, updating }: ModelTableProps) {
  const [editing, setEditing] = useState<EditingState | null>(null);

  const renderSortIndicator = (field: SortConfig['field']) => {
    if (sortConfig.field !== field) return null;
    return <span className="sort-indicator">{sortConfig.order === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleDoubleClick = (
    modelId: string,
    field: EditableField,
    currentValue: number | null
  ) => {
    if (!onUpdateModel) return;
    setEditing({
      modelId,
      field,
      value: currentValue?.toString() || '',
    });
  };

  const handleEditSubmit = async () => {
    if (!editing || !onUpdateModel) return;

    const isPricingField = editing.field.startsWith('pricing_');
    const numValue = editing.value
      ? (isPricingField ? parseFloat(editing.value) : parseInt(editing.value, 10))
      : null;

    if (editing.value && (isNaN(numValue as number) || (numValue as number) < 0)) {
      setEditing(null);
      return;
    }

    let updates: ModelUpdate;
    if (isPricingField) {
      const pricingField = editing.field.replace('pricing_', '') as 'input' | 'output' | 'cached_input';
      updates = {
        pricing: {
          [pricingField]: numValue,
        },
      };
    } else {
      updates = {
        [editing.field]: numValue,
      };
    }

    await onUpdateModel(editing.modelId, updates);
    setEditing(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleEditSubmit();
    } else if (e.key === 'Escape') {
      setEditing(null);
    }
  };

  const handleOpenSourceClick = async (model: ModelPricing) => {
    if (!onUpdateModel) return;
    const newValue = model.is_open_source === true ? false : model.is_open_source === false ? null : true;
    await onUpdateModel(model.id, { is_open_source: newValue });
  };

  const renderOpenSourceBadge = (value: boolean | null) => {
    if (value === true) return <span className="badge badge-open">开源</span>;
    if (value === false) return <span className="badge badge-closed">闭源</span>;
    return <span className="badge badge-unknown">未知</span>;
  };

  const renderEditableCell = (
    model: ModelPricing,
    field: 'context_length' | 'max_output_tokens',
    value: number | null
  ) => {
    const isEditing = editing?.modelId === model.id && editing?.field === field;
    const isUpdating = updating === model.id;

    if (isEditing) {
      return (
        <input
          type="number"
          className="edit-input"
          value={editing.value}
          onChange={(e) => setEditing({ ...editing, value: e.target.value })}
          onBlur={handleEditSubmit}
          onKeyDown={handleKeyDown}
          autoFocus
          disabled={isUpdating}
        />
      );
    }

    return (
      <span
        className={onUpdateModel ? 'editable' : ''}
        onDoubleClick={() => handleDoubleClick(model.id, field, value)}
        title={onUpdateModel ? '双击编辑' : ''}
      >
        {formatNumber(value)}
      </span>
    );
  };

  const renderEditablePriceCell = (
    model: ModelPricing,
    field: 'pricing_input' | 'pricing_output' | 'pricing_cached_input',
    value: number | null
  ) => {
    const isEditing = editing?.modelId === model.id && editing?.field === field;
    const isUpdating = updating === model.id;

    if (isEditing) {
      return (
        <input
          type="number"
          step="0.01"
          className="edit-input"
          value={editing.value}
          onChange={(e) => setEditing({ ...editing, value: e.target.value })}
          onBlur={handleEditSubmit}
          onKeyDown={handleKeyDown}
          autoFocus
          disabled={isUpdating}
        />
      );
    }

    return (
      <span
        className={onUpdateModel ? 'editable' : ''}
        onDoubleClick={() => handleDoubleClick(model.id, field, value)}
        title={onUpdateModel ? '双击编辑' : ''}
      >
        {formatPrice(value)}
      </span>
    );
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
              title="每百万 token 价格"
            >
              输入 <span className="unit-hint">$/M</span> {renderSortIndicator('input')}
            </th>
            <th
              className="sortable numeric"
              onClick={() => onSort('output')}
              title="每百万 token 价格"
            >
              输出 <span className="unit-hint">$/M</span> {renderSortIndicator('output')}
            </th>
            <th className="numeric" title="缓存输入每百万 token 价格">缓存 <span className="unit-hint">$/M</span></th>
            <th
              className="sortable numeric"
              onClick={() => onSort('context_length')}
            >
              上下文 {renderSortIndicator('context_length')}
            </th>
            <th className="numeric">输出限制</th>
            <th>输入</th>
            <th>输出</th>
            <th>开源</th>
            <th>能力</th>
          </tr>
        </thead>
        <tbody>
          {models.map((model) => (
            <tr key={model.id}>
              <td className="provider-cell">
                {getProviderDisplayName(model.provider)}
              </td>
              <td className="model-name-cell" title={model.model_name}>{model.model_name}</td>
              <td className="mono numeric">
                {renderEditablePriceCell(model, 'pricing_input', model.pricing.input)}
              </td>
              <td className="mono numeric">
                {renderEditablePriceCell(model, 'pricing_output', model.pricing.output)}
              </td>
              <td className="mono numeric secondary">
                {renderEditablePriceCell(model, 'pricing_cached_input', model.pricing.cached_input)}
              </td>
              <td className="mono numeric">
                {renderEditableCell(model, 'context_length', model.context_length)}
              </td>
              <td className="mono numeric">
                {renderEditableCell(model, 'max_output_tokens', model.max_output_tokens)}
              </td>
              <td className="modality-cell">
                <ModalityList modalities={model.input_modalities || []} />
              </td>
              <td className="modality-cell">
                <ModalityList modalities={model.output_modalities || []} />
              </td>
              <td
                className={onUpdateModel ? 'clickable' : ''}
                onClick={() => handleOpenSourceClick(model)}
                title={onUpdateModel ? '点击切换' : ''}
              >
                {renderOpenSourceBadge(model.is_open_source)}
              </td>
              <td className="capabilities-cell">
                {onUpdateModel ? (
                  <EditableCapabilityList
                    capabilities={model.capabilities}
                    onUpdate={async (newCaps) => {
                      await onUpdateModel(model.id, { capabilities: newCaps });
                    }}
                    editable={true}
                    updating={updating === model.id}
                  />
                ) : (
                  <CapabilityList capabilities={model.capabilities} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
