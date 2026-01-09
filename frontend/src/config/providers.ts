/**
 * Provider configuration - centralized names and colors.
 */

export interface ProviderConfig {
  displayName: string;
  color: string;
}

export const PROVIDER_CONFIG: Record<string, ProviderConfig> = {
  aws_bedrock: {
    displayName: 'AWS Bedrock',
    color: 'var(--aws-color)',
  },
  openai: {
    displayName: 'OpenAI',
    color: 'var(--openai-color)',
  },
  anthropic: {
    displayName: 'Anthropic',
    color: 'var(--anthropic-color)',
  },
  google_vertex_ai: {
    displayName: 'Google Vertex AI',
    color: 'var(--google-color)',
  },
  google_gemini: {
    displayName: 'Google Gemini',
    color: 'var(--google-color)',
  },
  azure_openai: {
    displayName: 'Azure OpenAI',
    color: 'var(--azure-color)',
  },
  openrouter: {
    displayName: 'OpenRouter',
    color: 'var(--openrouter-color)',
  },
  xai: {
    displayName: 'xAI',
    color: 'var(--xai-color)',
  },
};

/**
 * Get provider display name.
 */
export function getProviderDisplayName(provider: string): string {
  return PROVIDER_CONFIG[provider]?.displayName || provider;
}

/**
 * Get provider color CSS variable.
 */
export function getProviderColor(provider: string): string {
  return PROVIDER_CONFIG[provider]?.color || 'var(--accent-cyan)';
}
