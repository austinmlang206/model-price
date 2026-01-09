import { useState, useRef, useEffect } from 'react';
import { ALL_CAPABILITIES, getCapabilityConfig } from '../config';

interface CapabilityBadgeProps {
  capability: string;
}

export function CapabilityBadge({ capability }: CapabilityBadgeProps) {
  const config = getCapabilityConfig(capability);

  return (
    <span className={`capability-badge ${config.className}`} title={config.label}>
      {config.label}
    </span>
  );
}

interface CapabilityListProps {
  capabilities: string[];
  compact?: boolean;
}

export function CapabilityList({ capabilities, compact = false }: CapabilityListProps) {
  if (capabilities.length === 0) {
    return <span className="capability-none">-</span>;
  }

  return (
    <div className={`capability-list ${compact ? 'compact' : ''}`}>
      {capabilities.map((cap) => (
        <CapabilityBadge key={cap} capability={cap} />
      ))}
    </div>
  );
}

interface EditableCapabilityListProps {
  capabilities: string[];
  onUpdate: (newCapabilities: string[]) => Promise<void>;
  editable?: boolean;
  updating?: boolean;
}

export function EditableCapabilityList({ 
  capabilities, 
  onUpdate, 
  editable = true,
  updating = false 
}: EditableCapabilityListProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedCaps, setSelectedCaps] = useState<string[]>(capabilities);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update selected caps when capabilities prop changes
  useEffect(() => {
    setSelectedCaps(capabilities);
  }, [capabilities]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        handleClose();
      }
    };

    if (isEditing) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isEditing, selectedCaps, capabilities]);

  const handleClose = async () => {
    // Check if there are actual changes
    const hasChanges = 
      selectedCaps.length !== capabilities.length ||
      !selectedCaps.every(cap => capabilities.includes(cap));
    
    if (hasChanges) {
      await onUpdate(selectedCaps);
    }
    setIsEditing(false);
  };

  const toggleCapability = (cap: string) => {
    setSelectedCaps(prev => 
      prev.includes(cap) 
        ? prev.filter(c => c !== cap)
        : [...prev, cap]
    );
  };

  const handleBadgeClick = (e: React.MouseEvent) => {
    if (!editable) return;
    e.stopPropagation();
    setIsEditing(true);
  };

  if (!editable) {
    return <CapabilityList capabilities={capabilities} />;
  }

  return (
    <div className="editable-capability-container" ref={dropdownRef}>
      <div 
        className={`capability-list-wrapper ${editable ? 'editable' : ''} ${updating ? 'updating' : ''}`}
        onClick={handleBadgeClick}
        title="点击编辑能力标签"
      >
        {capabilities.length === 0 ? (
          <span className="capability-none clickable">点击添加</span>
        ) : (
          <div className="capability-list">
            {capabilities.map((cap) => (
              <CapabilityBadge key={cap} capability={cap} />
            ))}
          </div>
        )}
        {editable && <span className="edit-icon">✎</span>}
      </div>
      
      {isEditing && (
        <div className="capability-dropdown">
          <div className="capability-dropdown-header">
            <span>选择能力</span>
            <button
              className="capability-dropdown-close"
              onClick={() => handleClose()}
            >
              完成
            </button>
          </div>
          <div className="capability-options">
            {ALL_CAPABILITIES.map(cap => {
              const config = getCapabilityConfig(cap);
              const isSelected = selectedCaps.includes(cap);
              return (
                <button
                  key={cap}
                  type="button"
                  className={`capability-option-btn ${config.className} ${isSelected ? 'selected' : ''}`}
                  onClick={() => toggleCapability(cap)}
                >
                  {isSelected && <span className="check-mark">✓</span>}
                  {config.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
