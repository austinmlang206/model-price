/**
 * Capability configuration - centralized definitions for filtering and display.
 */

export interface CapabilityConfig {
  label: string;
  shortLabel: string;
  className: string;
}

/**
 * All capability configurations for badge display.
 */
export const CAPABILITY_CONFIG: Record<string, CapabilityConfig> = {
  text: {
    label: 'Text',
    shortLabel: 'Txt',
    className: 'cap-text',
  },
  vision: {
    label: 'Vision',
    shortLabel: 'Vis',
    className: 'cap-vision',
  },
  audio: {
    label: 'Audio',
    shortLabel: 'Aud',
    className: 'cap-audio',
  },
  embedding: {
    label: 'Embed',
    shortLabel: 'Emb',
    className: 'cap-embedding',
  },
  tool_call: {
    label: 'Tool Call',
    shortLabel: 'Tool',
    className: 'cap-tool',
  },
  tool_use: {
    label: 'Tool Use',
    shortLabel: 'Tool',
    className: 'cap-tool',
  },
  reasoning: {
    label: 'Reasoning',
    shortLabel: 'Think',
    className: 'cap-reasoning',
  },
  image_generation: {
    label: 'Image Gen',
    shortLabel: 'Img',
    className: 'cap-image-gen',
  },
  web_search: {
    label: 'Web Search',
    shortLabel: 'Web',
    className: 'cap-web-search',
  },
  computer_use: {
    label: 'Computer Use',
    shortLabel: 'CU',
    className: 'cap-computer-use',
  },
  moderation: {
    label: 'Moderation',
    shortLabel: 'Mod',
    className: 'cap-moderation',
  },
  video: {
    label: 'Video',
    shortLabel: 'Vid',
    className: 'cap-video',
  },
  file: {
    label: 'File',
    shortLabel: 'File',
    className: 'cap-file',
  },
};

/**
 * Capabilities for filter dropdown (subset with Chinese labels).
 */
export const FILTER_CAPABILITIES = [
  { value: 'text', label: '文本' },
  { value: 'vision', label: '视觉' },
  { value: 'audio', label: '音频' },
  { value: 'embedding', label: '嵌入' },
  { value: 'image_generation', label: '图像生成' },
  { value: 'tool_use', label: '工具调用' },
  { value: 'reasoning', label: '推理' },
];

/**
 * All available capabilities for editing.
 */
export const ALL_CAPABILITIES = Object.keys(CAPABILITY_CONFIG);

/**
 * Get capability config, returns default for unknown capabilities.
 */
export function getCapabilityConfig(capability: string): CapabilityConfig {
  return CAPABILITY_CONFIG[capability] || {
    label: capability,
    shortLabel: capability.slice(0, 4),
    className: 'cap-unknown',
  };
}
