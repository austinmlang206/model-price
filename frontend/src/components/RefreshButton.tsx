interface RefreshButtonProps {
  refreshing: boolean;
  onRefresh: () => void;
}

export function RefreshButton({ refreshing, onRefresh }: RefreshButtonProps) {
  return (
    <button
      className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
      onClick={onRefresh}
      disabled={refreshing}
      title="刷新数据"
    >
      <span className="refresh-icon">⟳</span>
      {refreshing ? '刷新中...' : '刷新'}
    </button>
  );
}
