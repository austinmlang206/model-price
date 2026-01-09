import { useState, useEffect, useRef } from 'react';

interface RefreshButtonProps {
  refreshing: boolean;
  onRefresh: () => void;
}

export function RefreshButton({ refreshing, onRefresh }: RefreshButtonProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (refreshing) {
      startTimeRef.current = Date.now();
      setElapsedTime(0);

      const timer = setInterval(() => {
        if (startTimeRef.current) {
          setElapsedTime(Math.floor((Date.now() - startTimeRef.current) / 1000));
        }
      }, 1000);

      return () => clearInterval(timer);
    } else {
      startTimeRef.current = null;
      setElapsedTime(0);
    }
  }, [refreshing]);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <button
      className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
      onClick={() => onRefresh()}
      disabled={refreshing}
      title={refreshing ? '正在刷新数据...' : '刷新数据'}
    >
      <span className="refresh-icon">⟳</span>
      <span className="refresh-text">
        {refreshing ? '刷新中' : '刷新'}
      </span>
      {refreshing && elapsedTime > 0 && (
        <span className="refresh-timer">{formatTime(elapsedTime)}</span>
      )}
      {refreshing && (
        <span className="refresh-pulse" />
      )}
    </button>
  );
}
