import type { LucideProps } from 'lucide-react';
import {
  Type,
  Image,
  Volume2,
  Video,
  FileText,
  Code,
  Boxes,
  Box,
} from 'lucide-react';

type LucideIcon = React.ComponentType<LucideProps>;

export type Modality =
  | 'text'
  | 'image'
  | 'audio'
  | 'video'
  | 'file'
  | 'code'
  | 'embedding'
  | '3d';

interface ModalityConfig {
  icon: LucideIcon;
  label: string;
  color: string;
}

const modalityConfig: Record<Modality, ModalityConfig> = {
  text: {
    icon: Type,
    label: '文本',
    color: '#6366f1', // indigo
  },
  image: {
    icon: Image,
    label: '图片',
    color: '#10b981', // emerald
  },
  audio: {
    icon: Volume2,
    label: '音频',
    color: '#f59e0b', // amber
  },
  video: {
    icon: Video,
    label: '视频',
    color: '#ef4444', // red
  },
  file: {
    icon: FileText,
    label: '文件',
    color: '#8b5cf6', // violet
  },
  code: {
    icon: Code,
    label: '代码',
    color: '#06b6d4', // cyan
  },
  embedding: {
    icon: Boxes,
    label: '嵌入向量',
    color: '#ec4899', // pink
  },
  '3d': {
    icon: Box,
    label: '3D模型',
    color: '#14b8a6', // teal
  },
};

interface ModalityIconProps {
  modality: string;
  size?: number;
}

export function ModalityIcon({ modality, size = 16 }: ModalityIconProps) {
  const config = modalityConfig[modality as Modality];

  if (!config) {
    return null;
  }

  const IconComponent = config.icon;

  return (
    <span
      className="modality-icon"
      title={config.label}
      style={{ color: config.color }}
    >
      <IconComponent size={size} strokeWidth={2} />
    </span>
  );
}

interface ModalityListProps {
  modalities: string[];
  size?: number;
}

export function ModalityList({ modalities, size = 20 }: ModalityListProps) {
  if (!modalities || modalities.length === 0) {
    return <span className="modality-none">-</span>;
  }

  return (
    <div className="modality-list">
      {modalities.map((mod) => (
        <ModalityIcon key={mod} modality={mod} size={size} />
      ))}
    </div>
  );
}

// Export all available modalities for reference
export const ALL_MODALITIES: Modality[] = [
  'text',
  'image',
  'audio',
  'video',
  'file',
  'code',
  'embedding',
  '3d',
];

export { modalityConfig };
